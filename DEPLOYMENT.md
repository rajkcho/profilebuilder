# Orbital v7.0 - Deployment Guide

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/rajkcho/profilebuilder.git
cd profilebuilder

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run main.py
```

The app will open at `http://localhost:8501`

---

## System Requirements

### Minimum Requirements:
- Python 3.10 or higher
- 4GB RAM
- Internet connection (for live market data)

### Recommended:
- Python 3.11+
- 8GB RAM
- SSD storage
- High-speed internet

---

## Dependencies

Core packages (see requirements.txt for versions):
- **streamlit** - Web framework
- **yfinance** - Market data
- **plotly** - Interactive charts
- **pandas / numpy** - Data processing
- **python-pptx** - PowerPoint generation
- **openpyxl** - Excel export

---

## Environment Variables

Optional configuration:

```bash
# API Keys (optional - for enhanced features)
export OPENAI_API_KEY="your-key-here"  # For AI insights
export ALPHA_VANTAGE_KEY="your-key-here"  # Alternative data source

# App Configuration
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=true
```

---

## Production Deployment

### Option 1: Streamlit Cloud (Easiest)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository: `rajkcho/profilebuilder`
4. Deploy!

**Advantages:**
- Free hosting
- Automatic HTTPS
- Easy updates via git push
- Built-in secrets management

### Option 2: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t orbital:v7 .
docker run -p 8501:8501 orbital:v7
```

### Option 3: Cloud Platforms

**AWS (EC2/Elastic Beanstalk):**
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt

# Run with nohup
nohup streamlit run main.py --server.port=8501 &
```

**Google Cloud Run:**
- Push Docker image to GCR
- Deploy to Cloud Run
- Auto-scaling included

**Azure Web Apps:**
- Use Python runtime
- Configure startup command: `streamlit run main.py`

---

## Configuration

### .streamlit/config.toml

```toml
[theme]
primaryColor = "#2563EB"      # Electric blue
backgroundColor = "#0C0F1A"    # Deep charcoal
secondaryBackgroundColor = "#1F2937"  # Lighter dark
textColor = "#E5E7EB"         # Cool white
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[runner]
magicEnabled = true
fastReruns = true
```

---

## Performance Optimization

### Caching

The app uses Streamlit's caching extensively:

```python
@st.cache_data(ttl=300)  # 5-minute cache
def fetch_company_data(ticker):
    # Expensive data fetch
    pass
```

**Cache Management:**
- Market data: 5 minutes
- Company profiles: 1 hour
- Historical data: 24 hours

Clear cache: Settings → Clear Cache (in-app)

### Data Loading

**Optimization tips:**
- Use `show_spinner=False` for better UX
- Implement progressive loading
- Cache expensive calculations
- Use pandas efficiently

---

## Security Best Practices

### 1. API Keys
Never commit API keys! Use:
- Environment variables
- Streamlit secrets (`.streamlit/secrets.toml`)
- Secret management services

### 2. Input Validation
All user inputs are validated:
- Ticker symbols: uppercase, 1-10 chars
- Numerical inputs: range-constrained
- File uploads: type-checked

### 3. HTTPS
Use HTTPS in production:
- Streamlit Cloud: automatic
- Custom domain: use nginx/Apache reverse proxy
- Cloud platforms: built-in SSL

---

## Monitoring & Logging

### Application Logs

```bash
# View Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log
```

### Error Tracking

Implement error tracking:

```python
try:
    # Risky operation
    pass
except Exception as e:
    st.error(f"Error: {e}")
    # Log to external service (Sentry, etc.)
```

### Performance Metrics

Track:
- Page load times
- Data fetch latency
- Cache hit rates
- User sessions

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
pip install -r requirements.txt --upgrade
```

**2. Data fetch failures**
- Check internet connection
- Verify yfinance is not rate-limited
- Try alternative ticker symbols

**3. Memory issues**
- Increase available RAM
- Reduce cache TTL
- Restart application

**4. PPTX generation fails**
- Ensure python-pptx is installed
- Check template.pptx exists in assets/
- Verify write permissions

### Debug Mode

Enable debug logging:

```bash
streamlit run main.py --logger.level=debug
```

---

## Updating the Application

### From v5.8 → v7.0

1. **Backup your data**
   ```bash
   git stash  # Save local changes
   ```

2. **Pull latest code**
   ```bash
   git pull origin main
   ```

3. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Test locally**
   ```bash
   streamlit run main.py
   ```

5. **Deploy**
   - Streamlit Cloud: automatic on git push
   - Other platforms: redeploy container/code

---

## Custom Branding

### Logo & Colors

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#YOUR_COLOR"
backgroundColor = "#YOUR_BG"
# ... other colors
```

### Company Name

Search and replace "Orbital" in:
- `main.py` (header/footer)
- `README.md`
- `pptx_generator.py` (slide footers)

---

## Data Sources

### Primary: yfinance
- Real-time market data
- Company fundamentals
- Historical prices
- Free, no API key required

### Optional: Alpha Vantage
- Alternative data source
- Requires free API key
- Used as fallback

### Data Limitations

- Market data: 15-20 min delay (free tier)
- Historical data: Up to 10 years
- Fundamentals: Quarterly updates
- Some small-cap stocks may have limited data

---

## Scaling Considerations

### Single Instance
- Handles ~10-50 concurrent users
- 4GB RAM minimum
- SSD recommended

### Multi-Instance
For >50 users:
- Use load balancer
- Session state in Redis/Memcached
- Shared cache layer
- Container orchestration (Kubernetes)

---

## Support & Maintenance

### Health Checks

Endpoint for monitoring:
```python
# health.py
from streamlit import status
print("healthy")
```

### Automatic Restarts

Use process managers:
- **systemd** (Linux)
- **PM2** (Node.js process manager)
- **supervisord**
- Docker auto-restart policy

### Backup Strategy

**What to backup:**
- Configuration files
- Custom modifications
- User-uploaded data (if any)
- API keys/secrets

**What NOT to backup:**
- Cache files
- Log files
- Python __pycache__

---

## License & Attribution

ProfileBuilder (Orbital) v7.0
- MIT License (or your chosen license)
- Include attribution for data sources
- Link to GitHub repository

---

## Getting Help

- **GitHub Issues**: [github.com/rajkcho/profilebuilder/issues](https://github.com/rajkcho/profilebuilder/issues)
- **Documentation**: See CHANGELOG_v7.0.md for features
- **Community**: Discussions tab on GitHub

---

## Next Steps After Deployment

1. ✅ Test all analysis modes
2. ✅ Verify data sources working
3. ✅ Check PPTX/Excel exports
4. ✅ Test on multiple browsers
5. ✅ Set up monitoring
6. ✅ Configure backups
7. ✅ Share with users!

---

**Deployment checklist completed?** You're ready to go! 🚀
