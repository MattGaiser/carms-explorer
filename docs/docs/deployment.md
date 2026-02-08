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

## AWS Deployment (EC2 + Docker Compose)

Single EC2 instance running all 7 services via docker-compose (~$15/mo for t3.small, or free tier with t3.micro).

### Prerequisites
- AWS CLI configured with appropriate credentials
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
| `EC2_SSH_PRIVATE_KEY` | SSH private key for EC2 access |
| `EC2_HOST` | Elastic IP from `terraform output public_ip` |
| `POSTGRES_PASSWORD` | Database password |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) |

**CI pipeline** (`.github/workflows/ci.yml`): Runs `ruff` linting and `pytest` with a pgvector service container on every push/PR.

**CD pipeline** (`.github/workflows/deploy.yml`): Builds 4 Docker images, pushes to GHCR, deploys to EC2 via SSH.

### Manual Deploy

```bash
# SSH into the instance
ssh ec2-user@<elastic-ip>

# On the instance
cd /home/ec2-user/carms
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Access Services

```bash
echo "App:       http://<elastic-ip>:8000"
echo "Dagster:   http://<elastic-ip>:3000"
echo "Dashboard: http://<elastic-ip>:8501"
echo "Docs:      http://<elastic-ip>:8080"
```

### Architecture

| Resource | Service | Spec |
|----------|---------|------|
| Compute | EC2 | t3.small (2 vCPU, 2GB RAM) |
| Database | PostgreSQL + pgvector | Docker container with volume |
| Storage | EBS gp3 | 20 GB root volume |
| IP | Elastic IP | Stable public address |
| Registry | GHCR | GitHub Container Registry |
| CI/CD | GitHub Actions | Lint, test, build, deploy |

### Cost

| Component | Monthly Cost |
|-----------|-------------|
| EC2 t3.small | ~$15 |
| Elastic IP (attached) | $0 |
| EBS 20GB gp3 | ~$2 |
| GHCR | Free (public repo) |
| GitHub Actions | Free (2,000 min/mo) |
| **Total** | **~$17/mo** |

Free tier: Use `t3.micro` ($0 for 12 months) — add 2GB swap for PyTorch.
