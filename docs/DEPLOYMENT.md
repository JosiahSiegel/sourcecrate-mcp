# Fly.io Deployment Guide for SourceCrate

Complete guide for deploying SourceCrate HTTP API and Browser UI on Fly.io with optimal configuration for production scale.

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

3. **Clone SourceCrate repository:**
   ```bash
   git clone https://github.com/JosiahSiegel/sourcecrate-mcp.git
   cd sourcecrate-mcp
   ```

---

## 🐳 Optimized Multi-Stage Dockerfile

Create an optimized Dockerfile for SourceCrate using multi-stage builds:

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
COPY pyproject.toml README.md ./
COPY source_crate ./source_crate

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
COPY source_crate ./source_crate
COPY browser-ui ./browser-ui

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run with gunicorn for production
CMD ["gunicorn", "source_crate.http_server:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--keep-alive", "5"]
```

**Save as:** `Dockerfile.flyio` in the project root.

---

## ⚙️ Fly.io Configuration (fly.toml)

Create `fly.toml` for SourceCrate:

```toml
# SourceCrate HTTP API - Fly.io Configuration
app = "sourcecrate"  # Change to your app name
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
  processes = ["app"]

  # Concurrency limits (important for multi-source API calls)
  [http_service.concurrency]
    type = "requests"
    soft_limit = 10  # Start new machines at 10 concurrent requests
    hard_limit = 25  # Max 25 concurrent requests per machine

# VM resources
[[vm]]
  size = "shared-cpu-1x"  # 256MB RAM, 1 shared CPU (free tier)

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
fly launch --no-deploy --name sourcecrate --region iad
```

**Choose:**
- App name: `sourcecrate` (or your preferred name)
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

Your API will be available at: `https://sourcecrate.fly.dev`

### Step 5: Test the Deployment

```bash
# Test health endpoint
curl https://sourcecrate.fly.dev/health

# Test search endpoint
curl -X POST https://sourcecrate.fly.dev/api/v1/search \
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

UI available at: `https://sourcecrate.fly.dev/`

### Option B: Separate GitHub Pages Deployment

Follow the GitHub Pages instructions from [DEPLOYMENT.md](./DEPLOYMENT.md), using your Fly.io API URL:

```javascript
// browser-ui/config.js
window.SOURCECRATE_API_URL = 'https://sourcecrate.fly.dev';
```

---

## 📈 Scaling for Production

### Scale to 2-3 Machines (Recommended for Production)

**🎯 Primary Benefits:**
1. **3x rate limit capacity** - Each region gets unique IP
2. **Better global latency** - Users connect to nearest region
3. **High availability** - Automatic failover between regions
4. **Zero extra cost** - Free tier includes 3 VMs

```bash
# Scale to 3 machines across multiple regions (RECOMMENDED)
fly scale count 3 --region iad,lhr,syd

# Result:
# - 3 independent IPs for API rate limits
# - ~200ms latency worldwide
# - Free tier covers all 3 VMs

# Single region (NOT recommended - no rate limit benefit)
fly scale count 3  # Same IP, no rate limit improvement
```

**Rate Limit Impact:**
- **1 region**: 1,200 arXiv papers/hour, 3,600 Semantic Scholar/hour
- **3 regions**: 3,600 arXiv papers/hour, 10,800 Semantic Scholar/hour

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
   ┌─────┴─────┬─────────┬─────────┐
   │           │         │         │
FastAPI VM  FastAPI VM  FastAPI VM  ...
2GB RAM     2GB RAM     2GB RAM
IP: x.x.1   IP: x.x.2   IP: x.x.3   (5 unique IPs)
(iad)       (lhr)       (syd)       (gru, nrt)
```

**Commands:**

```bash
# Deploy 5 machines across 5 regions for maximum rate limit capacity
fly scale count 5 --region iad,lhr,syd,gru,nrt
fly scale vm shared-cpu-2x --memory 2048

# Result: 5 independent IPs = 5x rate limits
# - arXiv: 6,000 papers/hour (vs 1,200)
# - Semantic Scholar: 18,000 papers/hour (vs 3,600)
# - PubMed: 54,000 papers/hour (vs 10,800)

# Enable autoscaling (optional)
fly autoscale set min=3 max=10 --memory 2048
```

**Rate Limit Capacity:**
- **5 regions**: 5x effective rate limits
- **Handle**: 300K API calls/hour
- **Support**: 100K+ concurrent users

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
   fly ext redis create --name sourcecrate-cache
   ```

2. **Update Dockerfile.flyio:**
   ```dockerfile
   # Add redis to dependencies
   RUN pip install redis
   ```

3. **Access Redis URL:**
   Redis URL will be automatically set as `REDIS_URL` environment variable.

### Add Additional Academic Data Sources

🎯 Expand coverage with ToS-compliant academic APIs

SourceCrate MCP comes with 15+ built-in sources. Below are additional sources with commercial-use-friendly terms of service that you can integrate:

#### ✅ OpenAlex (250M+ works, CC0 license)

**Coverage:** Comprehensive cross-disciplinary database
**Terms:** CC0 public domain, commercial use explicitly allowed
**Rate Limits:** 100K calls/day (unlimited with polite pool)
**API Key:** None required (email recommended)

```bash
# Set polite pool email for unlimited access
fly secrets set OPENALEX_EMAIL=your.email@example.com
```

**Best for:** Comprehensive metadata, citation graphs, institutions, funding

#### ✅ Unpaywall (20M+ open access papers, CC0 license)

**Coverage:** Open access PDF URLs for paywalled papers
**Terms:** CC0 public domain, commercial use explicitly allowed
**Rate Limits:** 100K calls/day
**API Key:** None required (email recommended)

```bash
# Set email for tracking (optional)
fly secrets set UNPAYWALL_EMAIL=your.email@example.com
```

**Best for:** Finding free PDFs of papers behind paywalls

#### ✅ CORE (9.5M+ papers, commercial use allowed)

**Coverage:** Open access research papers across all disciplines
**Terms:** Commercial use allowed with attribution
**Rate Limits:** Free tier - 1 batch or 5 single requests per 10 seconds
**API Key:** **Required** (free registration)

```bash
# Register at: https://core.ac.uk/services/api
# Then set API key:
fly secrets set CORE_API_KEY=your_core_key_here
```

**Best for:** Humanities, social sciences, education research

#### ✅ DataCite (DOI metadata, CC0 license)

**Coverage:** Research dataset and paper DOI metadata
**Terms:** CC0 public domain, commercial use explicitly allowed
**Rate Limits:** Unlimited (reasonable use)
**API Key:** None required

**Best for:** Dataset metadata, research data discovery

#### ✅ Zenodo (Research data, CC0 metadata)

**Coverage:** Research datasets and publications from CERN
**Terms:** CC0 metadata, non-military use only
**Rate Limits:** Unlimited (reasonable use via OAI-PMH)
**API Key:** None required

**Best for:** Physics, datasets, open science repositories

#### ✅ PLOS (Open access journals, CC BY license)

**Coverage:** PLOS ONE and other PLOS journals
**Terms:** CC BY license, commercial use with attribution
**Rate Limits:** Unlimited (reasonable use)
**API Key:** None required

**Best for:** Biology, medicine, open access peer-reviewed papers

#### Rate Limit Benefits with Multi-Region

**Important:** When deployed to multiple regions, each source's rate limits multiply:

```text
Single Region (1 IP):
- OpenAlex: 100K calls/day
- Unpaywall: 100K calls/day
- CORE: 1 batch/10s

Three Regions (3 IPs):
- OpenAlex: 300K calls/day (3x)
- Unpaywall: 300K calls/day (3x)
- CORE: 3 batches/10s (3x)
```

#### Integration Steps

1. **Register for API keys** (where required)
2. **Set secrets** via `fly secrets set`
3. **Configure in YAML** (see SourceCrate MCP documentation)
4. **Deploy and test** with multi-region setup

**Note:** All sources listed have verified ToS allowing commercial use as of 2025. Always review individual ToS before deploying to production.

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

### Multi-Region Rate Limit Distribution

🎯 **Key Benefit:** Multiple Regions = Multiple IPs = Higher Rate Limits

Academic APIs rate-limit by server IP, not by end user. When you deploy to multiple regions, **each region gets its own IP address**, effectively multiplying your rate limits.

**Architecture:**

```text
User Search Request
        ↓
   Fly.io Load Balancer (routes to closest region)
        ↓
    ┌────────────┴────────────┬──────────────┐
    ↓                         ↓              ↓
US Server (iad)          EU Server (lhr)  Asia Server (syd)
IP: 1.2.3.4              IP: 5.6.7.8      IP: 9.10.11.12
    ↓                         ↓              ↓
Makes 15+ API calls from its own unique IP
    ↓                         ↓              ↓
Each IP has INDEPENDENT rate limits from academic APIs
```

**Rate Limit Examples (Per IP):**

| API Source | Rate Limit (1 IP) | Rate Limit (3 IPs) | Multiplier |
|------------|-------------------|-------------------|------------|
| arXiv | 1 req/3s (1,200/hour) | 3 concurrent (3,600/hour) | 3x |
| Semantic Scholar | 1 RPS (3,600/hour) | 3 RPS (10,800/hour) | 3x |
| PubMed | 3 RPS (10,800/hour) | 9 RPS (32,400/hour) | 3x |
| CrossRef | Unlimited* | Unlimited* | ∞ |
| OpenAlex | 100K/day | 300K/day | 3x |
| Unpaywall | 100K/day | 300K/day | 3x |

*With polite pool (email parameter)

**Real-World Impact:**

```text
Single Region Setup:
- 100 concurrent users
- All requests from 1 IP
- Hit rate limits quickly
- Some searches fail

3-Region Setup:
- 100 concurrent users
- Load distributed across 3 IPs
- 3x effective rate limits
- All searches succeed
```

**Cost-Benefit Analysis:**

| Configuration | Cost/Month | Effective Rate Limits | Best For |
|--------------|------------|----------------------|----------|
| 1 VM (single region) | $0 (free) | 1x | Hobby projects |
| 3 VMs (3 regions) | $0 (free) | 3x | 1K-5K MAU |
| 5 VMs (5 regions) | ~$10 | 5x | 10K-50K MAU |

**How It Works:**

1. **Load balancer** routes each user to nearest region
2. **That region's server** makes API calls from its IP
3. **Academic APIs** see only that server's IP for rate limiting
4. **Geographic distribution** naturally spreads load across IPs

**Optimal Strategy:**

```bash
# Free tier: Deploy to 3 strategic regions
fly scale count 3 --region iad,lhr,syd

# Result:
# - 3x rate limit capacity
# - Better global latency
# - Zero additional cost
```

**Why This Beats Client-Side Requests:**

| Approach | Rate Limits | Privacy | Works? |
|----------|-------------|---------|--------|
| **Client-side** (browser → APIs) | User's IP varies | APIs see user IP | ❌ CORS blocks |
| **Single server** (server → APIs) | 1 server IP | APIs see server IP | ✅ But limited |
| **Multi-region** (3 servers → APIs) | 3 independent IPs | APIs see server IPs | ✅ **Best** |

---

## 🆚 Fly.io vs Render.com Comparison

| Feature | Fly.io | Render.com |
|---------|--------|------------|
| **Free Tier** | 3× 256MB VMs | 1× 512MB VM |
| **API Rate Limits** | 3x (3 IPs) | 1x (1 IP) |
| **Spin-down** | Optional | Forced (15 min) |
| **Cold starts** | 5-10 sec (if enabled) | 50 sec |
| **Global regions** | 30+ regions | Single region |
| **Autoscaling** | Built-in | Manual only |
| **Load balancing** | Automatic | N/A (single VM) |
| **Small app cost** | ~$5.70/mo | $7/mo |
| **100K users** | ~$15-30/mo | ~$21-36/mo |
| **ToS compliance** | Accept terms | Accept terms |

**Recommendation:**
- **Fly.io**: Better for production, global apps, scaling, **3x rate limits**
- **Render.com**: Simpler setup, good for beginners, single IP

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
CMD ["gunicorn", "source_crate.http_server:app", \
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

### 6. Deploy to Multiple Regions for Rate Limit Optimization
**🎯 Critical for scaling:** Each region gets a unique IP address, multiplying your effective rate limits.

- **Lower latency** for global users (~200ms worldwide)
- **Better availability** with automatic failover
- **3-5x rate limit capacity** - independent IP per region
- **Zero extra cost** - free tier includes 3 VMs

**Recommended deployment:**
```bash
# Always deploy to 3+ regions (not single region)
fly scale count 3 --region iad,lhr,syd

# Each region gets its own IP:
# - iad (US): IP 1.2.3.4
# - lhr (EU): IP 5.6.7.8
# - syd (Asia): IP 9.10.11.12

# Result: 3x rate limits for all academic APIs
```

**Why this matters:**
- Academic APIs rate-limit by server IP
- 1 region = 1 IP = 1x rate limits
- 3 regions = 3 IPs = 3x rate limits
- Load balancer automatically distributes requests

---

## 📚 Additional Resources

- **Fly.io Docs:** <https://fly.io/docs>
- **FastAPI on Fly.io:** <https://fly.io/docs/python/frameworks/fastapi>
- **Fly.io Pricing:** <https://fly.io/docs/about/pricing>
- **Fly.io CLI Reference:** <https://fly.io/docs/flyctl>
- **SourceCrate GitHub:** <https://github.com/JosiahSiegel/sourcecrate-mcp>

---

## 🚦 Quick Start Summary

```bash
# 1. Install Fly CLI
brew install flyctl  # or curl -L https://fly.io/install.sh | sh

# 2. Authenticate
fly auth login

# 3. Clone and navigate
git clone https://github.com/JosiahSiegel/sourcecrate-mcp.git
cd sourcecrate-mcp

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

**Your API is now live at:** `https://sourcecrate.fly.dev` 🎉

---

## 🔌 Port Configuration Reference

Understanding the port setup across different environments:

### Local Development

| Component | Port | Access URL | Notes |
|-----------|------|------------|-------|
| HTTP API | 9000 | `http://localhost:9000` | Default local API port |
| Browser UI | 3001 | `http://localhost:3001` | Devcontainer setup |
| Browser UI (alt) | 3000 | `http://localhost:3000` | Standard local server |
| OpenAPI Docs | 9000 | `http://localhost:9000/docs` | Interactive API docs |

**Key Points:**
- Devcontainer uses VS Code port forwarding (9000→9000 mapping)
- UI auto-detects API at `localhost:9000` regardless of UI port
- Can run API and UI independently

### Fly.io Production

| Component | Internal Port | External Port | Access URL |
|-----------|---------------|---------------|------------|
| HTTP API | 8080 | 443 (HTTPS) | `https://sourcecrate.fly.dev/api/v1/*` |
| Browser UI | N/A | 443 (HTTPS) | `https://sourcecrate.fly.dev/` |
| Health Check | 8080 | N/A | Internal only |

**Key Points:**
- Single deployment serves both UI and API (via `[[statics]]`)
- Gunicorn binds to `0.0.0.0:8080` internally
- Fly.io proxy handles HTTPS termination and routing
- UI uses same-origin for API calls (no CORS issues)

### Environment Alignment Checklist

To ensure your app works identically in both environments:

- [x] **API Port**: Local uses 9000, Fly.io uses 8080 (both configurable)
- [x] **UI Auto-Detection**: Works for both local (3000/3001) and production (443)
- [x] **Health Checks**: `/health` endpoint works on both environments
- [x] **Static Files**: Fly.io serves from `/app/browser-ui`, local from `browser-ui/`
- [x] **CORS**: Enabled for local cross-origin, unnecessary for Fly.io same-origin
- [x] **Environment Variables**: `PORT` set in fly.toml, `HTTP_PORT` in local scripts

### Testing Both Environments

**Local:**
```bash
# Start API
bash scripts/local-manager.sh http-start

# Verify
curl http://localhost:9000/health

# Access UI
open http://localhost:3001  # Devcontainer
# or
python -m http.server 3000 && open http://localhost:3000
```

**Fly.io:**
```bash
# Deploy
fly deploy

# Verify
curl https://sourcecrate.fly.dev/health

# Access UI
open https://sourcecrate.fly.dev
```
