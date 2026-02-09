# Deployment

## Local Development (Docker Compose)

```bash
# Setup
cp .env.example .env
# Optionally add: ANTHROPIC_API_KEY=sk-ant-...

# Start all services
docker compose -f docker/docker-compose.yml up -d

# Run ETL
# Open http://localhost:3000 → Assets → Materialize All

# Access services
open http://localhost:8000       # Chat UI + API
open http://localhost:8000/docs  # Swagger docs
open http://localhost:8501       # Streamlit dashboard
open http://localhost:8080       # Documentation
```

## GCP Deployment (GCE + Docker Compose)

Single GCE e2-micro instance running all 7 services via docker-compose (free tier eligible).

### Prerequisites
- GCP project with Compute Engine API enabled
- `gcloud` CLI authenticated
- Terraform >= 1.5
- An SSH key pair (`ssh-keygen -t ed25519`)

### Infrastructure Setup

```bash
cd terraform

# Initialize
terraform init

# Plan (pass your SSH public key)
terraform plan -var="ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)"

# Apply
terraform apply -var="ssh_public_key=$(cat ~/.ssh/id_ed25519.pub)"

# Outputs
terraform output  # shows public_ip, ssh_command, service URLs
```

### CI/CD (GitHub Actions)

Pushes to `main` trigger automated lint, test, build, and deploy.

**Required GitHub Secrets:**

| Secret | Description |
|--------|-------------|
| `EC2_SSH_PRIVATE_KEY` | SSH private key for server access |
| `EC2_HOST` | Static IP from `terraform output public_ip` |
| `POSTGRES_PASSWORD` | Database password |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) |

**CI pipeline** (`.github/workflows/ci.yml`): Runs `ruff` linting and `pytest` with a pgvector service container on every push/PR.

**CD pipeline** (`.github/workflows/deploy.yml`): Builds 4 Docker images, pushes to GHCR, deploys to GCE via SSH.

### Manual Deploy

```bash
# SSH into the instance
ssh carms-deploy@<static-ip>

# On the instance
cd /home/carms-deploy/carms
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Access Services

```bash
echo "App:       http://<static-ip>:8000"
echo "Dagster:   http://<static-ip>:3000"
echo "Dashboard: http://<static-ip>:8501"
echo "Docs:      http://<static-ip>:8080"
```

### Architecture

| Resource | Service | Spec |
|----------|---------|------|
| Compute | GCE | e2-micro (0.25 vCPU, 1GB RAM + 2GB swap) |
| Database | PostgreSQL + pgvector | Docker container with volume |
| Storage | pd-standard | 30 GB boot disk |
| IP | Static external IP | Stable public address |
| Registry | GHCR | GitHub Container Registry |
| CI/CD | GitHub Actions | Lint, test, build, deploy |

### Cost

| Component | Monthly Cost |
|-----------|-------------|
| GCE e2-micro | $0 (free tier) |
| Static IP (attached) | $0 |
| pd-standard 30GB | $0 (free tier) |
| GHCR | Free (public repo) |
| GitHub Actions | Free (2,000 min/mo) |
| **Total** | **$0/mo** |
