output "public_ip" {
  description = "Static IP address of the GCE instance"
  value       = google_compute_address.app.address
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh ${var.ssh_user}@${google_compute_address.app.address}"
}

output "app_url" {
  description = "FastAPI chat UI + API"
  value       = "http://${google_compute_address.app.address}:8000"
}

output "dagster_url" {
  description = "Dagster webserver"
  value       = "http://${google_compute_address.app.address}:3000"
}

output "dashboard_url" {
  description = "Streamlit dashboard"
  value       = "http://${google_compute_address.app.address}:8501"
}

output "docs_url" {
  description = "MkDocs documentation"
  value       = "http://${google_compute_address.app.address}:8080"
}
