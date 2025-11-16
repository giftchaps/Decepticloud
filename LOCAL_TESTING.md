# DeceptiCloud Local Testing Guide

Test DeceptiCloud honeypots locally with Docker before deploying to AWS. This is the recommended way to validate your setup and understand how the honeypots work.

## Why Test Locally?

✅ **No AWS costs** - Test for free on your machine
✅ **Fast iteration** - Instant container startup vs EC2 deployment
✅ **Easy debugging** - Direct access to logs and containers
✅ **Safe environment** - No internet exposure during development
✅ **Validate changes** - Test configuration before AWS deployment

## Quick Start (5 minutes)

```bash
# 1. Setup (creates directories and honeypot content)
bash scripts/setup_local_test.sh

# 2. Start honeypots
docker-compose -f docker-compose.local.yml up -d

# 3. Test (automated validation)
python scripts/test_local_honeypots.py

# 4. View logs
docker-compose -f docker-compose.local.yml logs -f
```

## Prerequisites

- **Docker** installed and running
- **Docker Compose** (usually included with Docker Desktop)
- **Python 3.8+** with pip
- **Required Python packages**: `pip install paramiko requests`

### Install Docker

**macOS:**
```bash
brew install --cask docker
# Then start Docker Desktop
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add yourself to docker group
newgrp docker  # Activate group membership
```

**Windows:**
Download Docker Desktop from https://www.docker.com/products/docker-desktop

## Step-by-Step Setup

### Step 1: Setup Environment

The setup script creates all necessary directories and realistic honeypot content:

```bash
bash scripts/setup_local_test.sh
```

This creates:
```
data/
├── cowrie/
│   ├── logs/          # SSH honeypot logs
│   ├── downloads/     # Files downloaded by attackers
│   └── etc/           # Cowrie configuration
└── nginx/
    ├── logs/          # Web server logs
    └── content/       # Honeypot web content
        ├── index.html
        ├── robots.txt
        ├── .env       # Honeytoken!
        └── api-status.json
```

### Step 2: Start Honeypots

Start both honeypots in the background:

```bash
docker-compose -f docker-compose.local.yml up -d
```

Verify containers are running:

```bash
docker-compose -f docker-compose.local.yml ps
```

Expected output:
```
NAME                      STATUS              PORTS
cowrie_honeypot_local     Up (healthy)        0.0.0.0:2222->2222/tcp
nginx_honeypot_local      Up (healthy)        0.0.0.0:8080->80/tcp
```

### Step 3: Test Honeypots

#### Automated Testing

Run comprehensive automated tests:

```bash
python scripts/test_local_honeypots.py
```

This validates:
- ✓ Docker containers are running and healthy
- ✓ SSH honeypot accepts connections on port 2222
- ✓ Web honeypot serves content on port 8080
- ✓ Honeytokens are accessible (fake credentials in .env)
- ✓ Logs are being generated
- ✓ Attack simulation generates realistic log data

#### Manual Testing

**SSH Honeypot (Cowrie):**

```bash
# Connect to SSH honeypot
ssh -p 2222 root@localhost

# Try these passwords:
# - password
# - 123456
# - admin

# Once connected, try commands:
whoami
ls -la /home
cat /etc/passwd
uname -a
pwd
exit
```

**Web Honeypot (nginx):**

```bash
# Test in browser or with curl

# Index page
curl http://localhost:8080/

# robots.txt
curl http://localhost:8080/robots.txt

# Honeytoken (.env file with fake credentials)
curl http://localhost:8080/.env

# API status
curl http://localhost:8080/api-status.json

# Common attack paths
curl http://localhost:8080/admin
curl http://localhost:8080/.git/config
curl http://localhost:8080/backup.sql
```

### Step 4: View Logs

**Real-time container logs:**

```bash
# Both containers
docker-compose -f docker-compose.local.yml logs -f

# SSH honeypot only
docker logs -f cowrie_honeypot_local

# Web honeypot only
docker logs -f nginx_honeypot_local
```

**Cowrie SSH logs (JSON format):**

```bash
# View raw JSON logs
cat data/cowrie/logs/cowrie.json

# Pretty print with jq
cat data/cowrie/logs/cowrie.json | jq

# Filter for login attempts
cat data/cowrie/logs/cowrie.json | jq 'select(.eventid=="cowrie.login.failed")'

# Count login attempts by username
cat data/cowrie/logs/cowrie.json | jq -r '.username' | sort | uniq -c
```

**nginx Web logs:**

```bash
# Access log (all requests)
cat data/nginx/logs/access.log

# Filter for specific paths
grep ".env" data/nginx/logs/access.log
grep "admin" data/nginx/logs/access.log

# Count requests by IP
awk '{print $1}' data/nginx/logs/access.log | sort | uniq -c
```

### Step 5: Test with RL Agent

Once honeypots are running, test the RL agent locally:

```bash
# Edit main.py and update:
EC2_HOST = "localhost"
EC2_USER = None  # Not needed for local
EC2_KEY_FILE = None  # Not needed for local

# Run training
python main.py --episodes 10
```

**Note:** The RL agent expects to deploy containers itself, so you may need to stop the docker-compose containers first:

```bash
docker-compose -f docker-compose.local.yml down
```

## Honeypot Content

### SSH Honeypot (Cowrie)

**Default credentials (configured in `data/cowrie/etc/userdb.txt`):**
- root:password
- root:123456
- root:admin
- ubuntu:ubuntu
- admin:admin

**Realistic features:**
- Ubuntu SSH banner (OpenSSH_8.9p1 Ubuntu-3ubuntu0.6)
- Fake filesystem with /etc/passwd, /home directories
- Command execution (ls, cat, whoami, etc.)
- Download tracking for malware samples

### Web Honeypot (nginx)

**Honeytokens in `/.env`:**
- AWS credentials (AKIA3OEXAMPLEKEY123)
- Database passwords
- Stripe API keys
- Redis passwords
- SMTP credentials

**Realistic content:**
- Production API Gateway landing page
- robots.txt with disallow rules
- API status endpoint (api-status.json)
- Common paths that attract scanners

## Attack Simulation

Generate realistic attack traffic for testing:

```bash
# Run automated attack simulation (included in test script)
python scripts/test_local_honeypots.py

# Or simulate manually:

# SSH brute force
for user in root admin ubuntu test; do
  for pass in password 123456 admin root; do
    sshpass -p $pass ssh -p 2222 $user@localhost exit 2>/dev/null
  done
done

# Web enumeration
for path in / /admin /login /wp-admin /.env /.git/config /backup.sql; do
  curl -s http://localhost:8080$path > /dev/null
done

# SQL injection attempts
curl "http://localhost:8080/api?id=1' OR '1'='1"
curl "http://localhost:8080/api?id=admin'--"
```

## Testing Advanced Features

### Test Dwell Time Tracking

```bash
# Start dwell time tracker
python -c "
from src.dwell_time_tracker import get_tracker
import time

tracker = get_tracker()

# Simulate attacker session
tracker.session_start('test-session-1', 'localhost', 'ssh')
time.sleep(2)
tracker.log_command('test-session-1', 'whoami')
tracker.log_command('test-session-1', 'cat /etc/passwd')
time.sleep(1)
tracker.log_command('test-session-1', 'cat /home/ubuntu/.aws/credentials')  # Honeytoken!
metrics = tracker.session_end('test-session-1')

print(f'Dwell time: {metrics[\"duration_seconds\"]}s')
print(f'Engagement score: {metrics[\"engagement_score\"]}/100')
print(f'Honeytoken accessed: {metrics[\"honeytoken_accessed\"]}')
"
```

### Test Traffic Normalizer

```bash
# Generate realistic background traffic
python src/traffic_normalizer.py localhost &

# This simulates:
# - Legitimate SSH sessions
# - Normal web browsing
# - Cron job activity
# - Makes honeypot harder to detect
```

### Test Attack Framework Integration

```bash
# Test with realistic attack scenarios
python scripts/run_realistic_experiment.py \
  --scenario ssh_focused \
  --target localhost \
  --duration 60
```

## Troubleshooting

### Containers won't start

```bash
# Check Docker is running
docker info

# Check for port conflicts
lsof -i :2222  # SSH honeypot
lsof -i :8080  # Web honeypot

# View container logs
docker-compose -f docker-compose.local.yml logs

# Restart containers
docker-compose -f docker-compose.local.yml restart
```

### SSH connection refused

```bash
# Check Cowrie is listening
docker exec cowrie_honeypot_local netstat -tlnp | grep 2222

# Check health status
docker inspect cowrie_honeypot_local --format='{{.State.Health.Status}}'

# View Cowrie logs
docker logs cowrie_honeypot_local
```

### Web honeypot not accessible

```bash
# Check nginx is running
docker exec nginx_honeypot_local nginx -t

# Check if content exists
docker exec nginx_honeypot_local ls -la /usr/share/nginx/html

# View nginx error log
docker exec nginx_honeypot_local cat /var/log/nginx/error.log
```

### Logs not being generated

```bash
# Check log directories exist and are writable
ls -la data/cowrie/logs
ls -la data/nginx/logs

# Check volume mounts
docker inspect cowrie_honeypot_local --format='{{.Mounts}}'
docker inspect nginx_honeypot_local --format='{{.Mounts}}'

# Ensure logs are being written
docker exec cowrie_honeypot_local ls -la /cowrie/cowrie-git/var/log/cowrie
docker exec nginx_honeypot_local ls -la /var/log/nginx
```

### Permission errors

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/

# Or run containers with your UID (edit docker-compose.local.yml)
# Add under each service:
#   user: "${UID}:${GID}"
```

## Cleanup

### Stop containers (keep data)

```bash
docker-compose -f docker-compose.local.yml stop
```

### Stop and remove containers (keep data)

```bash
docker-compose -f docker-compose.local.yml down
```

### Remove everything including data

```bash
# Stop and remove containers
docker-compose -f docker-compose.local.yml down -v

# Remove data directories
rm -rf data/

# Remove generated files
rm -f LOCAL_TEST_README.md
rm -f local_test_results_*.json
```

## Next Steps

After successful local testing:

1. **Analyze Results**: Review logs and metrics
   ```bash
   jupyter notebook notebooks/01_data_analysis.ipynb
   ```

2. **Train RL Agent**: Run local training experiments
   ```bash
   python main.py --episodes 50
   ```

3. **Deploy to AWS**: See production deployment guide
   ```bash
   # See PRODUCTION_QUICK_START.md
   cd infra && terraform apply
   ```

4. **Run Realistic Attacks**: Test with industry-standard frameworks
   ```bash
   # See docs/ATTACK_FRAMEWORKS.md
   python scripts/run_realistic_experiment.py --scenario mixed
   ```

## Architecture (Local)

```
┌─────────────────────────────────────────────┐
│            Local Machine                    │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │     Docker Network (honeynet)          │ │
│  │                                        │ │
│  │  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │   Cowrie     │  │    nginx     │   │ │
│  │  │ SSH :2222    │  │  Web :8080   │   │ │
│  │  └──────────────┘  └──────────────┘   │ │
│  │         ↓                  ↓           │ │
│  │  ┌──────────────────────────────────┐ │ │
│  │  │     Volume Mounts (./data/)      │ │ │
│  │  └──────────────────────────────────┘ │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │  Logs: ./data/cowrie/logs/             │ │
│  │        ./data/nginx/logs/              │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## Comparison: Local vs Production

| Feature | Local Testing | AWS Production |
|---------|--------------|----------------|
| **Cost** | Free | ~$40/month |
| **Setup Time** | 5 minutes | 20 minutes |
| **Internet Exposure** | No | Yes (public IP) |
| **Real Attacks** | Manual simulation | Actual attackers |
| **Monitoring** | Local logs | CloudWatch, CloudTrail |
| **Alerting** | None | SNS email alerts |
| **VPC Isolation** | Docker network | AWS VPC |
| **Honeytoken Monitoring** | Manual | CloudTrail automated |
| **Use Case** | Development, testing | Research, production |

## Best Practices

1. **Test locally first** - Always validate changes locally before AWS deployment
2. **Review logs regularly** - Check data/cowrie/logs and data/nginx/logs
3. **Simulate attacks** - Use test script to generate realistic traffic
4. **Monitor resources** - Keep an eye on Docker CPU/memory usage
5. **Clean up** - Remove old containers and logs periodically
6. **Version control** - Don't commit data/ directory (already in .gitignore)

## Security Notes

⚠️ **Local testing is isolated and safe, but remember:**

- Don't expose honeypots to the internet from your local machine
- Use ports 2222 and 8080 (not standard 22/80) to avoid conflicts
- Honeytokens are fake but look realistic - don't confuse them with real credentials
- Local Docker network is isolated from your host network
- Stop containers when not testing to save resources

## Support

- **Local Testing Issues**: Check this guide's troubleshooting section
- **General DeceptiCloud Questions**: See README.md and GUIDE.md
- **Production Deployment**: See PRODUCTION_QUICK_START.md
- **Bug Reports**: GitHub Issues

---

**Ready to start? Run:** `bash scripts/setup_local_test.sh` 🚀
