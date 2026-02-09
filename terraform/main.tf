# --- Static IP ---

resource "google_compute_address" "app" {
  name   = "${var.project_name}-ip"
  region = var.gcp_region
}

# --- Firewall ---

resource "google_compute_firewall" "app" {
  name    = "${var.project_name}-allow-app"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "8000", "3000", "8501", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = [var.project_name]
}

# --- Compute Instance ---

resource "google_compute_instance" "app" {
  name         = "${var.project_name}-server"
  machine_type = var.machine_type
  zone         = var.gcp_zone

  tags = [var.project_name]

  boot_disk {
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2404-lts-amd64"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.app.address
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e

    # Install Docker
    apt-get update -y
    apt-get install -y docker.io docker-compose-v2
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ${var.ssh_user}

    # Create app directory
    mkdir -p /home/${var.ssh_user}/carms
    chown ${var.ssh_user}:${var.ssh_user} /home/${var.ssh_user}/carms

    # Create 2GB swap (helps PyTorch on 1GB RAM e2-micro)
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile swap swap defaults 0 0' >> /etc/fstab
  EOF
}
