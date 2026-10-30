terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "artifactregistry.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "private" {
  name                    = "${var.name}-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "serverless" {
  name          = "${var.name}-subnet"
  ip_cidr_range = "10.20.0.0/24"
  region        = var.region
  network       = google_compute_network.private.id
}

resource "google_vpc_access_connector" "connector" {
  name          = "${var.name}-connector"
  region        = var.region
  network       = google_compute_network.private.name
  ip_cidr_range = "10.8.0.0/28"
}

resource "google_compute_global_address" "private_services" {
  name          = "${var.name}-private-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.private.id
}

resource "google_service_networking_connection" "private_services" {
  network                 = google_compute_network.private.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services.name]
}

resource "google_sql_database_instance" "postgres" {
  name             = "${var.name}-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  depends_on       = [google_service_networking_connection.private_services]
  settings {
    tier              = var.sql_tier
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_size         = 20
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
    ip_configuration {
      ipv4_enabled    = false
      private_network  = google_compute_network.private.id
      allocated_ip_range = google_compute_global_address.private_services.name
    }
  }
  deletion_protection = true
}

resource "google_sql_database" "app" {
  name     = "hackeval"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

resource "google_redis_instance" "cache" {
  name           = "${var.name}-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
  redis_version  = "REDIS_7_2"
  authorized_network = google_compute_network.private.id
}

resource "google_storage_bucket" "uploads" {
  name                        = var.upload_bucket
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning { enabled = true }
  lifecycle_rule {
    condition { age = var.upload_retention_days }
    action { type = "Delete" }
  }
}

resource "google_service_account" "backend" {
  account_id   = "${var.name}-backend"
  display_name = "HackEval backend Cloud Run identity"
}

resource "google_service_account" "runner" {
  account_id   = "${var.name}-runner"
  display_name = "HackEval runner Cloud Run identity"
}

resource "google_storage_bucket_iam_member" "backend_uploads" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "runner_downloads" {
  bucket = google_storage_bucket.uploads.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_cloud_run_v2_service" "runner" {
  name     = "${var.name}-runner"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    service_account = google_service_account.runner.email
    vpc_access { connector = google_vpc_access_connector.connector.id; egress = "PRIVATE_RANGES_ONLY" }
    containers {
      image = var.runner_image
      env { name = "GCS_BUCKET"; value = google_storage_bucket.uploads.name }
      env { name = "SANDBOX_RUNNER_TOKEN"; value_source { secret_key_ref { secret = google_secret_manager_secret.runner_token.id; version = "latest" } } }
    }
  }
}

resource "google_cloud_run_v2_service" "backend" {
  name     = var.name
  location = var.region
  template {
    service_account = google_service_account.backend.email
    vpc_access { connector = google_vpc_access_connector.connector.id; egress = "PRIVATE_RANGES_ONLY" }
    scaling { max_instance_count = 10 }
    containers {
      image = var.backend_image
      env { name = "APP_ENV"; value = "production" }
      env { name = "GCS_BUCKET"; value = google_storage_bucket.uploads.name }
      env { name = "DATABASE_URL"; value = "postgresql+psycopg://${var.db_user}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/hackeval" }
      env { name = "SANDBOX_RUNNER_URL"; value = google_cloud_run_v2_service.runner.uri }
      env { name = "SANDBOX_RUNNER_TOKEN"; value_source { secret_key_ref { secret = google_secret_manager_secret.runner_token.id; version = "latest" } } }
      env { name = "REDIS_URL"; value = "redis://${google_redis_instance.cache.host}:6379/0" }
      env { name = "JWT_SECRET"; value_source { secret_key_ref { secret = google_secret_manager_secret.jwt.id; version = "latest" } } }
    }

    resource "google_cloud_run_v2_service" "frontend" {
      name     = "${var.name}-frontend"
      location = var.region
      template {
        containers {
          image = var.frontend_image
          ports { container_port = 8080 }
        }
      }
    }

    resource "google_cloud_run_v2_job" "migration" {
      name     = "${var.name}-migration"
      location = var.region
      template {
        template {
          service_account = google_service_account.backend.email
          vpc_access { connector = google_vpc_access_connector.connector.id; egress = "PRIVATE_RANGES_ONLY" }
          containers {
            image = var.backend_image
            command = ["alembic"]
            args = ["upgrade", "head"]
            env { name = "DATABASE_URL"; value = "postgresql+psycopg://${var.db_user}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/hackeval" }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  service  = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "backend_runner" {
  service  = google_cloud_run_v2_service.runner.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  service  = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_secret_manager_secret" "jwt" {
  secret_id = "${var.name}-jwt-secret"
  replication { auto {} }
}

resource "google_secret_manager_secret" "runner_token" {
  secret_id = "${var.name}-runner-token"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "jwt" {
  secret      = google_secret_manager_secret.jwt.id
  secret_data = var.jwt_secret
}

resource "google_secret_manager_secret_version" "runner_token" {
  secret      = google_secret_manager_secret.runner_token.id
  secret_data = var.runner_token
}
