variable "project_id" { type = string }
variable "region" { type = string default = "us-central1" }
variable "name" { type = string default = "hackeval" }
variable "backend_image" { type = string }
variable "runner_image" { type = string }
variable "frontend_image" { type = string }
variable "upload_bucket" { type = string }
variable "db_user" { type = string default = "hackeval" }
variable "db_password" { type = string sensitive = true }
variable "sql_tier" { type = string default = "db-custom-1-3840" }
variable "upload_retention_days" { type = number default = 30 }
variable "jwt_secret" { type = string sensitive = true }
variable "runner_token" { type = string sensitive = true }
variable "alert_email" { type = string }
