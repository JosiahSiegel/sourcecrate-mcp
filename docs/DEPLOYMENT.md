# Free Deployment Guide

Deploy Paperez Browser UI and HTTP API for **$0/month** using free hosting platforms.

## ⚠️ FREE TIER CAPACITY LIMITS

**IMPORTANT:** Free hosting is suitable for **personal projects and prototypes**, not production scale.

### Realistic Free Tier Capacity (Render.com):

```
✅ Concurrent searches: 5-10 maximum
✅ Searches per hour: 200-500
✅ Searches per day: 2,000-5,000
✅ Monthly active users: ~700-1,600 (assuming 3 searches each)

❌ NOT suitable for:
   - 10K+ daily users
   - 100K+ monthly users
   - High-traffic production apps
   - Commercial applications
```

**Why the limits?**
- **512MB RAM** (fills quickly with cached API responses)
- **0.1 CPU** (1/10th of a core, shared)
- **Each search is heavy:** Queries 15+ APIs, BM25 ranking, deduplication
- **Shared infrastructure:** Can restart anytime under load

**Need more capacity?** See [Scaling Beyond Free Tier](#scaling-beyond-free-tier) below.

---

## ⚖️ Terms of Service Compliance

**IMPORTANT:** This guide follows all platform Terms of Service. Please read carefully:

### Render.com Free Tier
✅ **Intended for:** Low-traffic hobby projects, prototypes, development/testing
✅ **Acceptable:** Allowing natural spin-down after 15 min of inactivity
❌ **Prohibited:** Using keep-alive services to circumvent spin-down behavior

**Cold starts are by design.** If you need 24/7 uptime without cold starts, upgrade to Starter plan ($7/month).

### GitHub Pages
✅ **Intended for:** Personal projects, open-source documentation, educational use
✅ **Acceptable:** Donation buttons, crowdfunding links
❌ **Prohibited:** Commercial SaaS products, e-commerce sites, business hosting

**For commercial use,** host your UI on paid platforms (Netlify, Vercel, Cloudflare Pages).

### Free Tier Philosophy
Free tiers are for **genuine small-scale use**, not production applications. When you outgrow free limits:
- ✅ Upgrade to paid plans
- ✅ Optimize to reduce resource usage
- ❌ Don't circumvent limitations with workarounds

---

## 🎯 Recommended: GitHub Pages + Render.com

```
GitHub Pages (Static UI)  +  Render.com (API Server)
     FREE                       FREE (750 hrs/mo)
```

**Total Cost:** $0/month
**Setup Time:** 15 minutes
**Cold Starts:** ~50 seconds after 15 min inactivity (by design)
**Capacity:** ~1,000 MAU (personal/hobby use)
**Uptime:** Suitable for hobby projects, not production

---

## Part 1: Deploy HTTP API to Render.com

### Step 1: Sign Up
1. Visit [render.com](https://render.com)
2. Sign up with GitHub account (free)

### Step 2: Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository:
   - If using fork: Connect your fork
   - If using original: `JosiahSiegel/paperez-mcp`
3. Configure service:
   ```
   Name: paperez-api
   Environment: Python 3
   Build Command: pip install -e ".[http]"
   Start Command: paperez-http --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

4. (Optional) Add environment variables for enhanced performance:
   ```
   SEMANTIC_SCHOLAR_API_KEY=your_key_here
   CROSSREF_EMAIL=your_email@example.com
   NCBI_API_KEY=your_ncbi_key
   ```

5. Click **"Create Web Service"**

### Step 3: Get Your API URL
After deployment completes, Render provides a URL like:
```
https://paperez-api.onrender.com
```

**Save this URL** - you'll need it for the browser UI.

### Step 4: Understanding Cold Starts

**Render's free tier spins down after 15 minutes of inactivity** (by design). When a new request arrives:
- Spin-up takes ~50 seconds
- Subsequent requests are fast until next 15-min idle period

**This is normal and expected behavior for the free tier.**

**Options:**

1. **Accept cold starts** (recommended for hobby projects)
   - First request after idle: 50 seconds
   - Perfect for personal research, demos, learning

2. **Upgrade to eliminate cold starts** (production use)
   - Render Starter: $7/month (no spin-down, guaranteed uptime)
   - See [Scaling Beyond Free Tier](#scaling-beyond-free-tier) below

**⚠️ Do NOT use keep-alive services** (UptimeRobot, cron jobs, etc.) to circumvent spin-down. This violates Render's Terms of Service.

---

## Part 2: Deploy Browser UI to GitHub Pages

### Step 1: Fork Repository (if you haven't)
1. Visit [github.com/JosiahSiegel/paperez-mcp](https://github.com/JosiahSiegel/paperez-mcp)
2. Click **"Fork"** in top-right

### Step 2: Configure API URL

**Option A: Using config.js (Recommended)**
1. Copy the example config:
   ```bash
   cd browser-ui
   cp config.js.example config.js
   ```

2. Edit `browser-ui/config.js`:
   ```javascript
   // Replace with your Render.com API URL
   window.PAPEREZ_API_URL = 'https://paperez-api.onrender.com';
   ```

3. Update `browser-ui/index.html` to load config.js:
   ```html
   <!-- Add this line BEFORE <script src="app.js"></script> -->
   <script src="config.js"></script>
   <script src="app.js"></script>
   ```

4. Commit and push:
   ```bash
   git add browser-ui/config.js browser-ui/index.html
   git commit -m "Configure production API URL"
   git push
   ```

**Option B: Direct Inline Configuration**
1. Edit `browser-ui/index.html`
2. Add before `<script src="app.js"></script>`:
   ```html
   <script>
     window.PAPEREZ_API_URL = 'https://paperez-api.onrender.com';
   </script>
   <script src="app.js"></script>
   ```

### Step 3: Enable GitHub Pages
1. Go to your fork's **Settings** → **Pages**
2. Configure:
   ```
   Source: Deploy from a branch
   Branch: main
   Folder: /browser-ui
   ```
3. Click **"Save"**

### Step 4: Access Your Deployed UI
After 1-2 minutes, your site will be live at:
```
https://YOUR_USERNAME.github.io/paperez-mcp/
```

**Done! 🎉** You now have a free, globally-distributed academic paper search engine!

---

## Alternative Deployment Options

### Option B: All-in-One on Render.com

Deploy both UI and API on the same Render service (simpler, same domain, no CORS issues).

**Pros:**
- Single deployment
- No CORS configuration needed
- Easier to manage

**Cons:**
- Slower static file serving (no CDN)
- Still has 15-min sleep/cold starts (free tier limitation)

**Setup:**
1. Follow Part 1 above
2. Configure Render to serve static files:
   ```
   Start Command: paperez-http --host 0.0.0.0 --port $PORT --static-dir browser-ui
   ```
3. Access UI at: `https://paperez-api.onrender.com/`

### Option C: Fly.io (Alternative to Render)

**Pros:**
- 3 free shared VMs (256MB RAM each)
- Better performance than Render
- No forced spin-down

**Cons:**
- Requires Dockerfile (already provided)
- More complex setup
- Free tier limits may change

**Setup:**
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up: `fly auth signup`
3. Launch app:
   ```bash
   cd /path/to/paperez-mcp
   fly launch
   # Name: paperez-api
   # Region: Choose closest to you
   # Plan: Free
   ```
4. Deploy: `fly deploy`
5. Get URL: `fly status`

---

## Production Checklist

Before going public:

- [ ] API deployed and accessible (test: `curl https://your-api.com/health`)
- [ ] Browser UI deployed to GitHub Pages
- [ ] API URL configured in browser UI
- [ ] Test search functionality (expect 50-sec cold start on first request)
- [ ] Understand cold start behavior (normal for free tier)
- [ ] (Optional) Add custom domain
- [ ] (Optional) Set up environment variables for API keys
- [ ] (Optional) Upgrade to paid plan if cold starts are unacceptable

---

## Monitoring & Maintenance

### Free Monitoring Tools
- **Render Dashboard**: View logs, metrics, and deployment status
- **GitHub Actions**: Monitor deployment status for UI updates
- **Browser DevTools**: Check API responses and network performance

**Note:** Uptime monitoring services (UptimeRobot, etc.) should NOT be used to circumvent free tier spin-down. This violates ToS.

### Updating Your Deployment

**Update API Server:**
```bash
git push  # Render auto-deploys on push
```

**Update Browser UI:**
```bash
git push  # GitHub Pages auto-deploys on push
```

---

## Troubleshooting

### Issue: API Returns 404
**Fix:** Check Render logs for errors. Ensure build command installed dependencies.

### Issue: Browser UI Shows "Failed to fetch"
**Fix:** Verify `window.PAPEREZ_API_URL` is set correctly. Check browser console for CORS errors.

### Issue: Slow First Request (50+ seconds)
**This is normal behavior for Render's free tier.** The service spins down after 15 minutes of inactivity.

**Options:**
1. Accept cold starts (recommended for hobby projects)
2. Upgrade to Render Starter ($7/month) for instant responses

**Do NOT use keep-alive services** - this violates Render's ToS.

### Issue: GitHub Pages Shows 404
**Fix:** Ensure Pages is configured to serve from `/browser-ui` folder, not root.

---

## Cost Breakdown

| Service | Free Tier | Actual Cost |
|---------|-----------|-------------|
| Render.com | 750 hrs/mo | $0 |
| GitHub Pages | Unlimited | $0 |
| **Total** | - | **$0/month** |

**Trade-offs with free tier:**
- ✅ Completely free
- ✅ Perfect for hobby projects, demos, learning
- ⚠️ Cold starts (~50 seconds after 15 min idle)
- ⚠️ Not suitable for production use

**For production:** Upgrade to paid plans ($7-36/month) for guaranteed uptime.

---

## Scaling Beyond Free Tier

### When to Upgrade

**Upgrade if you experience:**
- ❌ Frequent 503 errors (server overloaded)
- ❌ Searches taking > 10 seconds
- ❌ Memory errors in logs
- ❌ > 5,000 searches/day consistently

### Scaling Path by User Count

#### Stage 1: Hobby (FREE)
```
Users: < 1,000 MAU
Searches: < 5,000/day
Platform: Render Free + GitHub Pages
Cost: $0/month
```

#### Stage 2: Small Scale ($7/month)
```
Users: 1,000 - 10,000 MAU
Searches: 5,000 - 50,000/day
Platform: Render Starter (512MB RAM, no spin-down)
Cost: $7/month
Benefits:
  - No cold starts (instant responses)
  - 512MB RAM (same as free, but dedicated)
  - Guaranteed uptime
```

#### Stage 3: Medium Scale ($21-36/month)
```
Users: 10,000 - 100,000 MAU
Searches: 50,000 - 500,000/day
Platform: 3-5 servers behind load balancer
Cost: $21-36/month

Recommended Architecture:
┌─────────────────────────────────────────┐
│  Cloudflare CDN (Static UI - FREE)      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Load Balancer (AWS ALB / Cloudflare)   │
└─────────────────────────────────────────┘
                  ↓
      ┌───────────────────────┐
      │                       │
┌─────▼─────┐         ┌───────▼──────┐
│ FastAPI   │         │   FastAPI    │
│ Server 1  │   ...   │   Server N   │
│ 2GB RAM   │         │   2GB RAM    │
│ 1-2 vCPU  │         │   1-2 vCPU   │
└───────────┘         └──────────────┘
      │                       │
      └───────────┬───────────┘
                  ↓
    ┌─────────────────────────┐
    │  Redis Cache (Optional)  │
    │  - Cache search results  │
    │  - 50% faster responses  │
    └─────────────────────────┘

Provider Options:
  - AWS Lightsail: 3× $10/mo = $30/month
  - DigitalOcean: 3× $12/mo = $36/month
  - Render Starter: 3× $7/mo = $21/month
  - Fly.io: 3× 2GB RAM = ~$15-20/month
```

#### Stage 4: Large Scale ($100-500/month)
```
Users: 100,000 - 1,000,000 MAU
Searches: 500,000 - 5,000,000/day
Platform: Auto-scaling cluster, CDN, Redis, monitoring
Cost: $100-500/month

Requirements:
  - 10-20 API servers (auto-scaling)
  - Load balancer with health checks
  - Redis cluster for caching
  - CDN for static assets
  - Monitoring (Datadog, New Relic)
  - Database for user analytics (optional)
```

### Quick Upgrade Paths

**For 10K Users (Simplest):**
1. Upgrade Render to Starter plan: $7/month
2. Done! No architecture changes needed.

**For 100K Users (Recommended):**
1. Use Fly.io or DigitalOcean
2. Deploy 3 instances (2GB RAM, 2 vCPU each)
3. Add Cloudflare load balancer (free)
4. Optional: Add Redis for caching
5. Total: $21-36/month

**For 1M Users (Enterprise):**
1. AWS/GCP/Azure with auto-scaling
2. Kubernetes cluster (5-20 pods)
3. Managed Redis/Memcached
4. CDN (Cloudflare, AWS CloudFront)
5. Monitoring and alerting
6. Total: $500-2,000/month

### Provider Comparison

| Provider | Free Tier | Paid Start | Best For |
|----------|-----------|------------|----------|
| **Render** | 512MB, 0.1 CPU | $7/mo | Simplest upgr ade |
| **Fly.io** | 3× 256MB VMs | ~$2/mo | Cost-effective |
| **DigitalOcean** | None | $6/mo | Full control |
| **AWS Lightsail** | None | $5/mo | AWS ecosystem |
| **Railway** | $5 credit/mo | $5/mo | Dev-friendly |

### Performance Optimization Tips

**Before scaling up:**
1. **Enable caching:** Redis for search results (50% faster)
2. **Optimize queries:** Use `limit` parameter wisely
3. **Monitor performance:** Check Render logs for bottlenecks
4. **Rate limiting:** Prevent abuse with API rate limits

**Cheap wins:**
- Add Redis: DigitalOcean Managed Redis ($15/mo)
- Use CDN: Cloudflare (free tier is excellent)
- Compress responses: Enable gzip in FastAPI
- Optimize Docker image: Multi-stage build

---

## Need Help?

- **Issues:** [GitHub Issues](https://github.com/JosiahSiegel/paperez-mcp/issues)
- **Render Docs:** [render.com/docs](https://render.com/docs)
- **GitHub Pages Docs:** [docs.github.com/pages](https://docs.github.com/pages)
