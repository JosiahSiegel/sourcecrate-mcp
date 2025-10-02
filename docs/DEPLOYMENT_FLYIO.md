# Fly.io Deployment Guide for Paperez

Complete guide for deploying Paperez HTTP API and Browser UI on Fly.io with optimal configuration for production scale.

---

## 🎯 Why Fly.io?

```text
✅ Better free tier than Render (3 VMs vs 1)
✅ No forced spin-down (runs 24/7)
✅ Global edge network (30+ regions)
✅ Scale to zero support (optional)
✅ Built-in load balancing
✅ Pay-as-you-go pricing
```

**Cost Comparison:**
- Free tier: 3× 256MB VMs (enough for ~2,000 MAU)
- Small scale: $5.70/month for 1GB RAM
- 100K users: $15-30/month (vs $21-36 on alternatives)

---

## ⚖️ Terms of Service Compliance

**Fly.io ToS states:**
> "You may not access the Services in a manner intended to avoid incurring fees or exceeding usage limits or quotas"

**Compliant usage:**
- ✅ Using free tier for genuine small-scale projects
- ✅ Paying for what you use when you exceed limits
- ✅ Scaling up to paid plans when needed

**Non-compliant:**
- ❌ Splitting workloads across multiple accounts to avoid payment
- ❌ Gaming the system to stay just under free limits
- ❌ Running production services on free tier indefinitely

**Recommendation:** Use free tier for hobby projects (<2K MAU), upgrade to paid for production.

---

## 📋 Prerequisites

1. **Install Fly CLI:**
   ```bash
   # macOS
   brew install flyctl

   # Linux
   curl -L https://fly.io/install.sh | sh

   # Windows
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Sign up and authenticate:**
   ```bash
   fly auth signup
   # or if you have an account
   fly auth login
   ```

3. **Clone Paperez repository:**
   ```bash
   git clone https://github.com/JosiahSiegel/paperez-mcp.git
   cd paperez-mcp
   ```

---

## 🐳 Optimized Multi-Stage Dockerfile

Create an optimized Dockerfile for Paperez using multi-stage builds:

```dockerfile
# =============================================================================
# Stage 1: Builder - Install dependencies with full Python image
# =============================================================================
FROM python:3.11-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY pyproject.toml setup.py setup.cfg README.md ./
COPY paperez_mcp ./paperez_mcp

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[http]"

# =============================================================================
# Stage 2: Runtime - Slim image with only necessary files
# =============================================================================
FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:$PATH"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY paperez_mcp ./paperez_mcp
COPY browser-ui ./browser-ui

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run with gunicorn for production
CMD ["gunicorn", "paperez_mcp.http_server:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--keep-alive", "5"]
```

**Save as:** `Dockerfile.flyio` in the project root.

---

## ⚙️ Fly.io Configuration (fly.toml)

Create `fly.toml` for Paperez:

```toml
# Paperez HTTP API - Fly.io Configuration
app = "paperez-api"  # Change to your app name
primary_region = "iad"  # Change to closest region

# Build configuration
[build]
  dockerfile = "Dockerfile.flyio"

# Deploy configuration
[deploy]
  strategy = "rolling"
  wait_timeout = "10m"

# Environment variables
[env]
  PORT = "8080"
  PYTHONUNBUFFERED = "1"

# HTTP service configuration
[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false  # Keep running 24/7
  auto_start_machines = true
  min_machines_running = 1

  # Concurrency limits (important for multi-source API calls)
  [http_service.concurrency]
    type = "requests"
    soft_limit = 10  # Start new machines at 10 concurrent requests
    hard_limit = 25  # Max 25 concurrent requests per machine

# VM resources
[[vm]]
  size = "shared-cpu-1x"  # 256MB RAM, 1 shared CPU (free tier)
  memory = "256mb"
  cpu_kind = "shared"
  cpus = 1

# Health checks
[[checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"
  protocol = "http"

  [checks.headers]
    User-Agent = "Fly Health Check"
```

**Save as:** `fly.toml` in the project root.

---

## 🚀 Deployment Steps

### Step 1: Initialize Fly App

```bash
# Generate fly.toml (or use the one above)
fly launch --no-deploy --name paperez-api --region iad
```

**Choose:**
- App name: `paperez-api` (or your preferred name)
- Region: Choose closest to you (see `fly regions list`)
- Postgres: No (we don't need a database)
- Redis: No (optional, for caching later)

### Step 2: Set Environment Variables (Optional)

Add API keys for better performance:

```bash
fly secrets set \
  SEMANTIC_SCHOLAR_API_KEY=your_key_here \
  CROSSREF_EMAIL=your_email@example.com \
  NCBI_API_KEY=your_ncbi_key
```

### Step 3: Deploy to Fly.io

```bash
# Deploy the application
fly deploy

# Monitor deployment
fly logs
```

### Step 4: Get Your API URL

```bash
fly status
```

Your API will be available at: `https://paperez-api.fly.dev`

### Step 5: Test the Deployment

```bash
# Test health endpoint
curl https://paperez-api.fly.dev/health

# Test search endpoint
curl -X POST https://paperez-api.fly.dev/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"machine learning","limit":5}'
```

---

## 🌐 Deploy Browser UI

### Option A: Serve from Same Fly App

**Update Dockerfile.flyio** to serve static files:

```dockerfile
# Add this after COPY commands
COPY browser-ui ./browser-ui
```

**Update fly.toml:**

```toml
# Add static file serving
[[statics]]
  guest_path = "/app/browser-ui"
  url_prefix = "/"
```

Then redeploy:

```bash
fly deploy
```

UI available at: `https://paperez-api.fly.dev/`

### Option B: Separate GitHub Pages Deployment

Follow the GitHub Pages instructions from [DEPLOYMENT.md](./DEPLOYMENT.md), using your Fly.io API URL:

```javascript
// browser-ui/config.js
window.PAPEREZ_API_URL = 'https://paperez-api.fly.dev';
```

---

## 📈 Scaling for Production

### Scale to 2-3 Machines (Recommended for Production)

```bash
# Scale to 3 machines across multiple regions
fly scale count 3 --region iad,lhr,syd

# Or scale in single region
fly scale count 3
```

### Upgrade VM Size

```bash
# Upgrade to 1GB RAM (recommended for 10K-50K MAU)
fly scale vm shared-cpu-2x --memory 1024

# Or use dedicated CPU for better performance
fly scale vm performance-1x --memory 2048
```

### Scale to 100K Users

**Architecture:**

```text
Cloudflare CDN (Browser UI)
         ↓
    Fly.io Load Balancer
         ↓
   ┌─────┴─────┬─────────┐
   │           │         │
FastAPI VM  FastAPI VM  FastAPI VM
2GB RAM     2GB RAM     2GB RAM
(region 1)  (region 2)  (region 3)
```

**Commands:**

```bash
# Deploy 3-5 machines with 2GB RAM each
fly scale count 5 --region iad,lhr,syd,gru,nrt
fly scale vm shared-cpu-2x --memory 2048

# Enable autoscaling (optional)
fly autoscale set min=3 max=10 --memory 2048
```

**Cost:** ~$15-30/month for 100K MAU

---

## 💰 Cost Breakdown

### Free Tier (Hobby Projects)

```text
Resources: 3× 256MB VMs
Cost: $0/month
Capacity: ~2,000 MAU
Monthly searches: ~6,000
Suitable for: Personal projects, demos, learning
```

### Small Scale ($5-10/month)

```text
Resources: 1× 1GB VM
Cost: ~$5.70/month
Capacity: 5,000-10,000 MAU
Monthly searches: 15,000-30,000
Suitable for: Small production apps
```

### Medium Scale ($15-30/month)

```text
Resources: 3-5× 2GB VMs
Cost: ~$15-30/month
Capacity: 50,000-100,000 MAU
Monthly searches: 150,000-300,000
Suitable for: Production apps with global users
```

### Large Scale ($100-200/month)

```text
Resources: 10× 4GB VMs + Redis
Cost: ~$100-200/month
Capacity: 500,000-1,000,000 MAU
Monthly searches: 1,500,000-3,000,000
Suitable for: Enterprise applications
```

**Pricing details:**
- Shared CPU VMs: $0.0000008/sec (~$2.07/month per 256MB)
- Performance VMs: $0.000002/sec (~$5.18/month per 1GB)
- Network: First 100GB free, then $0.02/GB
- Storage: $0.15/GB/month

---

## 🔍 Monitoring & Management

### View Logs

```bash
# Stream live logs
fly logs

# View specific machine logs
fly logs -i <machine-id>
```

### SSH into Machine

```bash
fly ssh console
```

### Check Machine Status

```bash
# List all machines
fly machines list

# Show app status
fly status

# Show metrics
fly dashboard metrics
```

### Restart Machines

```bash
# Restart all machines
fly apps restart

# Restart specific machine
fly machine restart <machine-id>
```

---

## 🎛️ Advanced Configuration

### Add Redis Caching (Recommended for 10K+ MAU)

1. **Create Upstash Redis:**
   ```bash
   fly ext redis create --name paperez-cache
   ```

2. **Update Dockerfile.flyio:**
   ```dockerfile
   # Add redis to dependencies
   RUN pip install redis
   ```

3. **Access Redis URL:**
   Redis URL will be automatically set as `REDIS_URL` environment variable.

### Enable Scale-to-Zero (Cost Optimization)

**Update fly.toml:**

```toml
[http_service]
  auto_stop_machines = true   # Stop when idle
  auto_start_machines = true  # Start on request
  min_machines_running = 0    # Can scale to zero
```

**Trade-offs:**
- ✅ Lower cost (only pay when running)
- ⚠️ Cold starts (~5-10 seconds)
- ⚠️ Not suitable for production

### Multi-Region Deployment

```bash
# Deploy to multiple regions
fly scale count 3 --region iad,lhr,syd

# Add more regions later
fly scale count 5 --region iad,lhr,syd,gru,nrt

# View region list
fly regions list
```

**Recommended regions for global coverage:**
- `iad` - Ashburn, VA (US East)
- `lhr` - London (Europe)
- `syd` - Sydney (Asia-Pacific)
- `gru` - São Paulo (South America)
- `nrt` - Tokyo (Asia)

---

## 🆚 Fly.io vs Render.com Comparison

| Feature | Fly.io | Render.com |
|---------|--------|------------|
| **Free Tier** | 3× 256MB VMs | 1× 512MB VM |
| **Spin-down** | Optional | Forced (15 min) |
| **Cold starts** | 5-10 sec (if enabled) | 50 sec |
| **Global regions** | 30+ regions | Single region |
| **Autoscaling** | Built-in | Manual only |
| **Load balancing** | Automatic | N/A (single VM) |
| **Small app cost** | ~$5.70/mo | $7/mo |
| **100K users** | ~$15-30/mo | ~$21-36/mo |
| **ToS compliance** | Accept terms | Accept terms |

**Recommendation:**
- **Fly.io**: Better for production, global apps, scaling
- **Render.com**: Simpler setup, good for beginners

---

## 🐛 Troubleshooting

### Issue: Deployment Timeout

**Symptom:** `Error: timeout reached waiting for health checks to pass`

**Fix:**
```bash
# Increase wait timeout in fly.toml
[deploy]
  wait_timeout = "15m"
```

### Issue: Out of Memory

**Symptom:** Machine keeps restarting, logs show memory errors

**Fix:**
```bash
# Upgrade VM memory
fly scale vm shared-cpu-1x --memory 512

# Or upgrade to larger VM
fly scale vm shared-cpu-2x --memory 1024
```

### Issue: High Latency

**Symptom:** Searches taking > 5 seconds

**Fix:**
```bash
# Deploy closer to users
fly scale count 3 --region iad,lhr,syd

# Or upgrade CPU
fly scale vm performance-1x
```

### Issue: Connection Timeout

**Symptom:** `502 Bad Gateway` errors

**Fix:**
```bash
# Increase gunicorn timeout in Dockerfile.flyio
CMD ["gunicorn", "paperez_mcp.http_server:app", \
     "--timeout", "180", \  # Increase from 120
     ...]
```

---

## 🎓 Best Practices

### 1. Use Multi-Stage Docker Builds
- Reduces final image size by 50-70%
- Faster deployments
- Lower bandwidth costs

### 2. Set Appropriate Concurrency Limits
```toml
[http_service.concurrency]
  soft_limit = 10  # Start new VM
  hard_limit = 25  # Reject requests
```

### 3. Enable Health Checks
- Automatic restart on failure
- Better uptime
- Faster problem detection

### 4. Use Secrets for API Keys
```bash
fly secrets set KEY=value
# Never commit secrets to git
```

### 5. Monitor Resource Usage
```bash
# Check metrics dashboard
fly dashboard metrics

# Set up alerts (in dashboard)
```

### 6. Deploy to Multiple Regions
- Lower latency for global users
- Better availability
- Automatic failover

---

## 📚 Additional Resources

- **Fly.io Docs:** <https://fly.io/docs>
- **FastAPI on Fly.io:** <https://fly.io/docs/python/frameworks/fastapi>
- **Fly.io Pricing:** <https://fly.io/docs/about/pricing>
- **Fly.io CLI Reference:** <https://fly.io/docs/flyctl>
- **Paperez GitHub:** <https://github.com/JosiahSiegel/paperez-mcp>

---

## 🚦 Quick Start Summary

```bash
# 1. Install Fly CLI
brew install flyctl  # or curl -L https://fly.io/install.sh | sh

# 2. Authenticate
fly auth login

# 3. Clone and navigate
git clone https://github.com/JosiahSiegel/paperez-mcp.git
cd paperez-mcp

# 4. Create Dockerfile.flyio and fly.toml (see above)

# 5. Launch app
fly launch --no-deploy

# 6. Set secrets (optional)
fly secrets set SEMANTIC_SCHOLAR_API_KEY=your_key

# 7. Deploy
fly deploy

# 8. Scale for production (if needed)
fly scale count 3 --region iad,lhr,syd
fly scale vm shared-cpu-2x --memory 2048

# 9. Monitor
fly logs
fly status
```

**Your API is now live at:** `https://paperez-api.fly.dev` 🎉
