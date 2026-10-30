resource "google_monitoring_notification_channel" "email" {
  display_name = "${var.name} operations email"
  type         = "email"
  labels       = { email_address = var.alert_email }
}

resource "google_monitoring_alert_policy" "backend_5xx" {
  display_name = "${var.name} backend 5xx errors"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run 5xx responses"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.name}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "300s"
      aggregations { alignment_period = "60s"; per_series_aligner = "ALIGN_RATE"; cross_series_reducer = "REDUCE_SUM" }
    }
  }
  notification_channels = [google_monitoring_notification_channel.email.name]
}

resource "google_monitoring_alert_policy" "sql_cpu" {
  display_name = "${var.name} Cloud SQL CPU"
  combiner     = "OR"
  conditions {
    display_name = "Cloud SQL CPU above 80%"
    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      duration        = "900s"
      aggregations { alignment_period = "60s"; per_series_aligner = "ALIGN_MEAN" }
    }
  }
  notification_channels = [google_monitoring_notification_channel.email.name]
}
