# Free Deployment Guide

Deploy Paperez Browser UI and HTTP API for **$0/month** using free hosting platforms.

## 🎯 Recommended: GitHub Pages + Render.com

```
GitHub Pages (Static UI)  +  Render.com (API Server)
     FREE                       FREE (750 hrs/mo)
```

**Total Cost:** $0/month
**Setup Time:** 15 minutes
**Uptime:** 24/7 with UptimeRobot

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

### Step 4: Keep API Awake (Prevent Cold Starts)

**Problem:** Render's free tier spins down after 15 minutes of inactivity (50-second cold start).

**Solution:** Use UptimeRobot to ping your API every 10 minutes.

1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
2. Click **"+ Add New Monitor"**
3. Configure:
   ```
   Monitor Type: HTTP(s)
   Friendly Name: Paperez API
   URL: https://your-paperez-api.onrender.com/health
   Monitoring Interval: 10 minutes
   ```
4. Click **"Create Monitor"**

**Result:** Your API stays warm 24/7, responses are instant! 🚀

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
- Still has 15-min sleep issue (use UptimeRobot)

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
- [ ] UptimeRobot configured (prevents cold starts)
- [ ] Browser UI deployed to GitHub Pages
- [ ] API URL configured in browser UI
- [ ] Test search functionality
- [ ] (Optional) Add custom domain
- [ ] (Optional) Set up environment variables for API keys

---

## Monitoring & Maintenance

### Free Monitoring Tools
- **UptimeRobot**: 24/7 uptime monitoring (50 monitors free)
- **Render Dashboard**: View logs and metrics
- **GitHub Actions**: Monitor deployment status

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
**Fix:** Set up UptimeRobot to keep API awake (see Part 1, Step 4).

### Issue: GitHub Pages Shows 404
**Fix:** Ensure Pages is configured to serve from `/browser-ui` folder, not root.

---

## Cost Breakdown

| Service | Free Tier | Actual Cost |
|---------|-----------|-------------|
| Render.com | 750 hrs/mo | $0 |
| GitHub Pages | Unlimited | $0 |
| UptimeRobot | 50 monitors | $0 |
| **Total** | - | **$0/month** |

---

## Scaling Beyond Free Tier

When you outgrow free hosting:

**Render.com Paid Plans:**
- Starter: $7/month (512MB RAM, no spin-down)
- Standard: $25/month (2GB RAM, autoscaling)

**Alternatives:**
- AWS Lightsail: $5/month (VPS)
- DigitalOcean: $6/month (Droplet)
- Fly.io Hobby: ~$2/month (pay for what you use)

---

## Need Help?

- **Issues:** [GitHub Issues](https://github.com/JosiahSiegel/paperez-mcp/issues)
- **Render Docs:** [render.com/docs](https://render.com/docs)
- **GitHub Pages Docs:** [docs.github.com/pages](https://docs.github.com/pages)
