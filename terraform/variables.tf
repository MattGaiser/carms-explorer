variable "gcp_project" {
  description = "GCP project ID"
  type        = string
  default     = "aiproductproject"
}

variable "gcp_region" {
  description = "GCP region (us-central1/us-west1/us-east1 for free tier)"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "carms-explorer"
}

variable "machine_type" {
  description = "GCE machine type (e2-micro = free tier)"
  type        = string
  default     = "e2-micro"
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "ssh_user" {
  description = "SSH username (derived from key comment)"
  type        = string
  default     = "carms-deploy"
}
