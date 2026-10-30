output "backend_url" { value = google_cloud_run_v2_service.backend.uri }
output "frontend_url" { value = google_cloud_run_v2_service.frontend.uri }
output "runner_url" { value = google_cloud_run_v2_service.runner.uri }
output "uploads_bucket" { value = google_storage_bucket.uploads.name }
output "redis_host" { value = google_redis_instance.cache.host }
output "sql_private_ip" { value = google_sql_database_instance.postgres.private_ip_address }
