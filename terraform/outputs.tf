output "public_ip" {
  description = "Elastic IP address of the EC2 instance"
  value       = aws_eip.app.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh ec2-user@${aws_eip.app.public_ip}"
}

output "app_url" {
  description = "FastAPI chat UI + API"
  value       = "http://${aws_eip.app.public_ip}:8000"
}

output "dagster_url" {
  description = "Dagster webserver"
  value       = "http://${aws_eip.app.public_ip}:3000"
}

output "dashboard_url" {
  description = "Streamlit dashboard"
  value       = "http://${aws_eip.app.public_ip}:8501"
}

output "docs_url" {
  description = "MkDocs documentation"
  value       = "http://${aws_eip.app.public_ip}:8080"
}
