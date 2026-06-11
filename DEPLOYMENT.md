# 🚀 Deployment Guide: NYC Taxi Analytics Pipeline

## Overview

This guide covers deploying the autonomous analytics pipeline to your Ubuntu server (192.168.6.51) using Docker and Jenkins (running on port 8090).

## Architecture

```
Your Windows Dev Machine
         ↓
    Push to GitHub
         ↓
Jenkins (192.168.6.51:8090) ← Webhook triggered
         ↓
    Build Docker Image
         ↓
Ubuntu Docker Host (192.168.6.51)
         ├→ API Container (8100)
         │  └→ FastAPI + orchestrator.py
         └→ Volumes
            ├→ schema/ (AVRO files)
            ├→ code_cache/ (cached code)
            ├→ execution_log.json
            └→ api_usage.json
```

## Prerequisites

✅ **Already configured on your Ubuntu server:**
- Docker installed and running
- Docker Compose installed
- Jenkins running on http://192.168.6.51:8090

✅ **Not needed:**
- Port 8000 (already in use)
- .env files (using Jenkins credentials instead)

## 1️⃣ Jenkins Configuration

### Step 1: Create API Key Credentials in Jenkins

1. **Open Jenkins Console:**
   - Navigate to http://192.168.6.51:8090
   - Click **Manage Jenkins** → **Manage Credentials**
   - Select **Global credentials**
   - Click **+ Add Credentials**

2. **Add Anthropic API Key:**
   - **Kind:** Secret text
   - **Secret:** `sk-ant-xxxxxxxxxxxxx` (your actual key)
   - **ID:** `anthropic-api-key`
   - **Description:** Anthropic Claude API Key
   - Click **Create**

3. **Add OpenAI API Key (Optional):**
   - **Kind:** Secret text
   - **Secret:** `sk-xxxxxxxxxxxxx` (your OpenAI key)
   - **ID:** `openai-api-key`
   - **Description:** OpenAI API Key (optional)
   - Click **Create**

### Step 2: Create SSH Key Credentials in Jenkins

1. Go back to **Manage Credentials** → **Global credentials**
2. Click **+ Add Credentials**
   - **Kind:** SSH Username with private key
   - **Username:** `ubuntu`
   - **Private Key:** Paste your SSH private key content (from `~/.ssh/id_rsa`)
   - **ID:** `ubuntu-ssh-key`
   - **Description:** Ubuntu Server SSH Key
   - Click **Create**

> **Don't have SSH key?** Generate one on your Windows machine:
> ```powershell
> ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
> # Add public key to Ubuntu: ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@192.168.6.51
> ```

### Step 3: Create New Pipeline Job in Jenkins

1. Click **+ New Item**
   - **Job name:** `taxi-analytics-pipeline`
   - **Type:** Pipeline
   - Click **OK**

2. **Configure:**
   - **Description:** Autonomous NYC taxi analytics with smart caching
   - **Pipeline** section:
     - **Definition:** Pipeline script from SCM
     - **SCM:** Git
     - **Repository URL:** `https://github.com/manyloun/self_healing_sandbox.git`
     - **Branch:** `*/main`
     - **Script Path:** `Jenkinsfile`
   - Click **Save**

3. **Test the Pipeline:**
   - Click **Build Now**
   - Monitor logs in real-time

## 2️⃣ Ubuntu Server Setup

### Initial Setup (One-time)

SSH to your Ubuntu server:

```bash
ssh ubuntu@192.168.6.51

# Create deployment directory
sudo mkdir -p /opt/taxi-analytics
cd /opt/taxi-analytics

# Initialize git repo (if not cloned)
git clone https://github.com/manyloun/self_healing_sandbox.git .

# Set proper permissions
sudo chown -R ubuntu:ubuntu /opt/taxi-analytics

# Create directories for persistent volumes
mkdir -p schema code_cache
touch execution_log.json api_usage.json
```

**Verify Docker is running:**
```bash
docker --version
docker-compose --version
docker ps
```

## 3️⃣ Port Configuration

### Port Usage

| Service | Port | Host | Status |
|---------|------|------|--------|
| Jenkins | 8090 | 192.168.6.51 | ✅ Existing |
| Taxi API | 8100 | 192.168.6.51 | 🆕 This deployment |
| Other services | 8101-8110 | Available | Reserved |

**Port 8000 range:** Already in use (not touched)

### Firewall Rules (if needed)

```bash
# Allow Jenkins to access port 8100 locally
sudo ufw allow 8100/tcp

# Or disable firewall for internal network
sudo ufw disable  # (if running on private network)
```

## 4️⃣ Manual Deployment (For Testing)

If you want to deploy without Jenkins:

```bash
ssh ubuntu@192.168.6.51

cd /opt/taxi-analytics

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxx"
export OPENAI_API_KEY="sk-xxxxxxxxxxxx"  # Optional

# Build and start containers
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs -f taxi-api

# Test API
curl http://localhost:8100/health
```

## 5️⃣ API Endpoints

Once deployed, access your API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/status` | GET | Service status |
| `/api/costs` | GET | Spending summary |
| `/api/analyze` | POST | Execute pipeline |
| `/api/history` | GET | Execution history |
| `/api/dashboard` | GET | Full metrics dashboard |

### Example: Trigger Analysis from Jenkins

Add this stage to any Jenkins job:

```groovy
stage('Run Analytics') {
    steps {
        script {
            sh '''
                curl -X POST http://192.168.6.51:8100/api/analyze \
                  -H "Content-Type: application/json" \
                  -d '{
                    "vehicle_type": "green",
                    "month": 3,
                    "task": "Calculate average trip distance and revenue",
                    "provider": "anthropic"
                  }'
            '''
        }
    }
}
```

### Example: Python Client

```python
import requests
import json

# Trigger analysis
response = requests.post(
    "http://192.168.6.51:8100/api/analyze",
    json={
        "vehicle_type": "green",
        "month": 3,
        "task": "Calculate trip count and average fare",
        "provider": "anthropic"
    }
)

result = response.json()
print(json.dumps(result, indent=2))

# Check spending
costs = requests.get("http://192.168.6.51:8100/api/costs").json()
print(f"Total spend: ${costs['spending_summary']['total_cost']}")
```

## 6️⃣ Monitoring & Debugging

### View Container Logs

```bash
ssh ubuntu@192.168.6.51

cd /opt/taxi-analytics

# Real-time logs
docker-compose logs -f taxi-api

# Last 50 lines
docker-compose logs --tail=50 taxi-api

# Without timestamps
docker-compose logs --no-log-prefix taxi-api
```

### Check Container Health

```bash
docker ps --filter "name=taxi-analytics-api" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected output:
# NAMES                  STATUS          PORTS
# taxi-analytics-api     Up 2 minutes     0.0.0.0:8100->8100/tcp
```

### Access Execution Logs

```bash
cd /opt/taxi-analytics

# View API usage summary
cat api_usage.json | python -m json.tool

# View detailed execution log
cat execution_log.json | python -m json.tool | head -50

# Monitor in real-time
watch -n 2 'cat execution_log.json | python -c "import json, sys; data=json.load(sys.stdin); print(f\"Total: {len(data)} | Cost: ${sum(e.get(\"total_cost\",0) for e in data):.4f}\")"'
```

### Run Monitor Dashboard

```bash
docker exec taxi-analytics-api python monitor.py
```

## 7️⃣ Maintenance

### Update Code

```bash
cd /opt/taxi-analytics

# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check health
curl http://localhost:8100/health
```

### Rotate Logs

Logs are automatically rotated (max 10MB, 3 files) in docker-compose.yml

### Backup Data

```bash
cd /opt/taxi-analytics

# Backup execution logs
tar czf backup_logs_$(date +%Y%m%d).tar.gz \
    execution_log.json \
    api_usage.json \
    schema/ \
    code_cache/

# Upload to cloud storage or external drive
```

## 8️⃣ Troubleshooting

### Container won't start

```bash
docker logs taxi-analytics-api

# Common issues:
# 1. API key not set: Check Jenkins credentials configured
# 2. Port in use: Change 8100 in docker-compose.yml
# 3. Permission denied: Check file ownership: chown ubuntu:ubuntu /opt/taxi-analytics
```

### Connection refused on :8100

```bash
# Verify container is running
docker ps | grep taxi-analytics

# Verify port is listening
netstat -tlnp | grep 8100

# Wait longer for startup (especially first run)
sleep 10 && curl http://localhost:8100/health
```

### Out of disk space

```bash
# Check Docker disk usage
docker system df

# Clean up old images
docker image prune -a --force

# Clean up dangling volumes
docker volume prune --force
```

### API key not working

1. **Verify credentials in Jenkins:**
   - Jenkins → Manage Credentials → Global → Check `anthropic-api-key`
   
2. **Verify it's being passed to container:**
   - `docker inspect taxi-analytics-api | grep ANTHROPIC_API_KEY`

3. **Test API key directly:**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-xxxxx"
   python -c "import orchestrator; orchestrator.run_multi_agent_pipeline(...)"
   ```

## 9️⃣ Cost Management

### Daily Spending Limit

Default: **$10.00/day**

Edit on Ubuntu server:

```bash
cd /opt/taxi-analytics

# Edit source code
nano usage_tracker.py

# Change line: DAILY_LIMIT = 10.00

# Restart container
docker-compose restart taxi-api
```

### Monitor Spending in Real-Time

```bash
# From Jenkins job:
curl http://192.168.6.51:8100/api/costs | python -m json.tool

# Expected output:
# {
#   "spending_summary": {
#     "total_cost": 0.0045,
#     "total_input_tokens": 1200,
#     "total_output_tokens": 800,
#     "total_sessions": 5
#   },
#   "budget_status": {
#     "within_limit": true,
#     "daily_limit": 10.0,
#     "hourly_limit": 1.0
#   }
# }
```

## 🔟 Production Checklist

- [ ] Jenkins configured with credentials
- [ ] SSH key added to Jenkins
- [ ] Ubuntu deployment directory created
- [ ] Docker running on Ubuntu server
- [ ] Jenkinsfile committed to main branch
- [ ] API responds to health check
- [ ] Spending limits configured
- [ ] Monitoring dashboard accessible
- [ ] Logs persisted to volumes
- [ ] Firewall allows port 8100

## Summary

| Component | Config | Status |
|-----------|--------|--------|
| Jenkins | Port 8090 ✅ | Webhook-triggered |
| API | Port 8100 🆕 | FastAPI on Ubuntu |
| Credentials | Jenkins store | No .env files |
| Data | Volumes | Persistent |
| Monitoring | /api/dashboard | Real-time |
| Costs | Kill switch + limits | $10/day default |

You're ready to deploy! 🚀

```bash
# Final verification
curl http://192.168.6.51:8100/health
# {"status":"healthy","version":"2.0.0","port":8100}
```
