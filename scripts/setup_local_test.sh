#!/bin/bash
# Setup script for local DeceptiCloud testing
# Creates necessary directories and realistic honeypot content

set -e

echo "=========================================="
echo "DeceptiCloud Local Testing Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directory structure
echo -e "\n${BLUE}[1/5] Creating directory structure...${NC}"
mkdir -p data/cowrie/{logs,downloads,etc}
mkdir -p data/nginx/{logs,content}
mkdir -p config

echo "✓ Directories created"

# Create nginx content
echo -e "\n${BLUE}[2/5] Creating realistic web content...${NC}"

# Index page
cat > data/nginx/content/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production API Gateway</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .status { color: #28a745; font-weight: bold; }
        .info { color: #666; margin: 10px 0; }
        .build { font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Production API Gateway</h1>
        <p class="status">✓ All Systems Operational</p>
        <p class="info">Environment: Production</p>
        <p class="info">Region: us-east-1</p>
        <p class="build">Build: v1.2.3-a4f8d9c (2024-01-15 14:32:10 UTC)</p>
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            Apache/2.4.52 (Ubuntu) Server
        </p>
    </div>
</body>
</html>
EOF

# robots.txt
cat > data/nginx/content/robots.txt << 'EOF'
User-agent: *
Disallow: /admin
Disallow: /api/internal
Disallow: /backup
Disallow: /.git
Allow: /api/v1
EOF

# .env file with honeytokens
cat > data/nginx/content/.env << 'EOF'
# Production Environment Configuration
# DO NOT COMMIT TO VERSION CONTROL

APP_ENV=production
APP_DEBUG=false
APP_URL=http://api.production.local

# Database
DB_CONNECTION=mysql
DB_HOST=10.0.1.42
DB_PORT=3306
DB_DATABASE=production_db
DB_USERNAME=app_user
DB_PASSWORD=HONEYTOKEN_DB_Pass_Prod_2024_FAKE

# AWS Credentials (HONEYTOKENS - FAKE)
AWS_ACCESS_KEY_ID=AKIA3OEXAMPLEKEY123
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=prod-data-backup

# API Keys (HONEYTOKENS - FAKE)
STRIPE_KEY=sk_live_EXAMPLE123456789_HONEYTOKEN_FAKE
STRIPE_SECRET=rk_live_EXAMPLE987654321_HONEYTOKEN_FAKE

# Redis
REDIS_HOST=10.0.1.43
REDIS_PASSWORD=HONEYTOKEN_Redis_Prod_FAKE_2024
REDIS_PORT=6379

# Session
SESSION_DRIVER=redis
SESSION_LIFETIME=120

# Mail
MAIL_MAILER=smtp
MAIL_HOST=smtp.mailtrap.io
MAIL_PORT=587
MAIL_USERNAME=HONEYTOKEN_MAIL_USER_FAKE
MAIL_PASSWORD=HONEYTOKEN_MAIL_PASS_FAKE
EOF

# Create API status endpoint
cat > data/nginx/content/api-status.json << 'EOF'
{
  "status": "operational",
  "version": "1.2.3",
  "build": "a4f8d9c",
  "timestamp": "2024-01-15T14:32:10Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "s3": "healthy"
  },
  "endpoints": [
    "/api/v1/users",
    "/api/v1/auth",
    "/api/v1/data"
  ]
}
EOF

echo "✓ Web content created with honeytokens"

# Create Cowrie configuration
echo -e "\n${BLUE}[3/5] Creating Cowrie configuration...${NC}"

cat > data/cowrie/etc/cowrie.cfg << 'EOF'
[honeypot]
hostname = production-server-42
log_path = /cowrie/cowrie-git/var/log/cowrie
download_path = /cowrie/cowrie-git/var/lib/cowrie/downloads
state_path = /cowrie/cowrie-git/var/lib/cowrie
etc_path = /cowrie/cowrie-git/etc
share_path = /cowrie/cowrie-git/share/cowrie
tty_log_path = /cowrie/cowrie-git/var/lib/cowrie/tty

# SSH version string (realistic Ubuntu server)
ssh_version_string = SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6

[ssh]
enabled = true
rsa_public_key = etc/ssh_host_rsa_key.pub
rsa_private_key = etc/ssh_host_rsa_key
dsa_public_key = etc/ssh_host_dsa_key.pub
dsa_private_key = etc/ssh_host_dsa_key
listen_endpoints = tcp:2222:interface=0.0.0.0

[output_jsonlog]
enabled = true
logfile = /cowrie/cowrie-git/var/log/cowrie/cowrie.json
EOF

echo "✓ Cowrie configuration created"

# Create simple test credentials file
echo -e "\n${BLUE}[4/5] Creating test userdb for Cowrie...${NC}"

cat > data/cowrie/etc/userdb.txt << 'EOF'
# Simple userdb for testing
# Format: username:uid:password
root:0:password
root:0:123456
root:0:admin
ubuntu:1000:ubuntu
admin:1001:admin
EOF

echo "✓ Cowrie userdb created"

# Create README
echo -e "\n${BLUE}[5/5] Creating local test README...${NC}"

cat > LOCAL_TEST_README.md << 'EOF'
# Local Testing Guide

This directory contains everything needed to test DeceptiCloud honeypots locally.

## Quick Start

```bash
# 1. Run setup (creates directories and content)
bash scripts/setup_local_test.sh

# 2. Start honeypots
docker-compose -f docker-compose.local.yml up -d

# 3. Test honeypots
python scripts/test_local_honeypots.py

# 4. View logs
docker-compose -f docker-compose.local.yml logs -f
```

## Access Honeypots

**SSH Honeypot (Cowrie):**
```bash
ssh -p 2222 root@localhost
# Try passwords: password, 123456, admin
```

**Web Honeypot:**
```bash
# In browser or curl
curl http://localhost:8080/
curl http://localhost:8080/.env
curl http://localhost:8080/robots.txt
```

## View Logs

**Cowrie logs (SSH attacks):**
```bash
docker logs cowrie_honeypot_local
cat data/cowrie/logs/cowrie.json
```

**nginx logs (web attacks):**
```bash
docker logs nginx_honeypot_local
cat data/nginx/logs/access.log
```

## Stop Honeypots

```bash
docker-compose -f docker-compose.local.yml down
```

## Clean Up

```bash
# Remove containers and volumes
docker-compose -f docker-compose.local.yml down -v

# Remove data directories
rm -rf data/
```
EOF

echo "✓ README created"

echo -e "\n${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start honeypots:    docker-compose -f docker-compose.local.yml up -d"
echo "  2. Test deployment:    python scripts/test_local_honeypots.py"
echo "  3. View logs:          docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo "Access points:"
echo "  SSH Honeypot:  ssh -p 2222 root@localhost (password: password)"
echo "  Web Honeypot:  http://localhost:8080"
echo ""
