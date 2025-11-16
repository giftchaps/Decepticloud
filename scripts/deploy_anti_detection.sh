#!/bin/bash
# Deploy Anti-Detection Measures for DeceptiCloud Honeypots
# This script configures honeypots to be realistic and avoid detection

set -e

echo "=================================="
echo "DeceptiCloud Anti-Detection Setup"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
COWRIE_DIR="/opt/cowrie"
WEB_ROOT="/var/www/html"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Step 1: Creating realistic Cowrie filesystem${NC}"
# Create realistic filesystem
python3 << 'EOF'
import pickle
import os
from datetime import datetime, timedelta
import random

print("Creating realistic Ubuntu 22.04 AWS filesystem...")

# Generate realistic filesystem
fs = {}

# Root directory
fs['/'] = {'type': 'directory', 'mtime': (datetime.now() - timedelta(days=180)).timestamp()}

# Home directory
fs['/home/ubuntu'] = {'type': 'directory', 'mtime': (datetime.now() - timedelta(days=30)).timestamp()}

# Realistic .bash_history
bash_history = '''cd /opt/app
git pull origin master
sudo systemctl restart app
docker ps
docker logs app-container
tail -f /var/log/app/production.log
sudo apt update
sudo apt upgrade -y
df -h
free -m
htop
exit
ssh admin@production-db.internal
cat /opt/app/config.json
vim /opt/app/.env
./deploy.sh
curl https://api.stripe.com/v1/charges
aws s3 ls s3://production-backups/
aws ec2 describe-instances
'''

fs['/home/ubuntu/.bash_history'] = {
    'type': 'file',
    'content': bash_history,
    'size': len(bash_history),
    'mtime': (datetime.now() - timedelta(hours=2)).timestamp()
}

# SSH authorized keys
authorized_keys = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCx... ubuntu@ip-10-0-1-42\n'
fs['/home/ubuntu/.ssh/authorized_keys'] = {
    'type': 'file',
    'content': authorized_keys,
    'size': len(authorized_keys),
    'mtime': (datetime.now() - timedelta(days=45)).timestamp()
}

# Auth log with realistic entries
auth_log = f'''Nov 15 08:23:15 ip-10-0-1-42 sshd[1234]: Accepted publickey for ubuntu from 203.0.113.45 port 52341 ssh2: RSA
Nov 15 09:15:42 ip-10-0-1-42 sudo: ubuntu : TTY=pts/0 ; PWD=/home/ubuntu ; USER=root ; COMMAND=/usr/bin/apt update
Nov 15 10:30:11 ip-10-0-1-42 sshd[1456]: Accepted publickey for ubuntu from 203.0.113.45 port 52387 ssh2: RSA
Nov 15 11:00:22 ip-10-0-1-42 CRON[2345]: pam_unix(cron:session): session opened for user root
Nov 15 12:15:33 ip-10-0-1-42 sshd[3456]: Accepted publickey for ubuntu from 203.0.113.45 port 52401 ssh2: RSA
'''

fs['/var/log/auth.log'] = {
    'type': 'file',
    'content': auth_log,
    'size': len(auth_log),
    'mtime': (datetime.now() - timedelta(hours=1)).timestamp()
}

# Fake AWS credentials (honeytoken!)
aws_creds = '''[default]
aws_access_key_id = AKIA3OEXAMPLEKEY123
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = us-east-1

[production]
aws_access_key_id = AKIA3PRODKEY456789
aws_secret_access_key = ProdSecretKey123456789ExampleSecret
region = us-east-1
'''

fs['/home/ubuntu/.aws/credentials'] = {
    'type': 'file',
    'content': aws_creds,
    'size': len(aws_creds),
    'mtime': (datetime.now() - timedelta(days=30)).timestamp()
}

# Application config with secrets (honeytoken!)
app_config = '''{
  "app_name": "production-api",
  "environment": "production",
  "database": {
    "host": "production-db.c9akr8fi.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "name": "prod_app",
    "user": "app_admin",
    "password": "P@ssw0rd_Prod_DB_2024!"
  },
  "redis": {
    "host": "production-redis.abc123.cache.amazonaws.com",
    "port": 6379,
    "password": "Redis_P@ss_2024!"
  },
  "api_keys": {
    "stripe": "sk_live_EXAMPLE123456789_HONEYTOKEN_FAKE",
    "sendgrid": "SG_EXAMPLE_HONEYTOKEN_KEY_NOT_REAL",
    "twilio": "ACEXAMPLE0000HONEYTOKEN000000FAKE"
  },
  "jwt_secret": "super-secret-jwt-key-production-2024"
}
'''

fs['/opt/app/config.json'] = {
    'type': 'file',
    'content': app_config,
    'size': len(app_config),
    'mtime': (datetime.now() - timedelta(days=90)).timestamp()
}

# Docker compose file
docker_compose = '''version: '3.8'
services:
  app:
    image: mycompany/production-api:v1.2.3
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - DB_HOST=production-db.internal
'''

fs['/opt/app/docker-compose.yml'] = {
    'type': 'file',
    'content': docker_compose,
    'size': len(docker_compose),
    'mtime': (datetime.now() - timedelta(days=60)).timestamp()
}

# Save filesystem
os.makedirs('honeyfs', exist_ok=True)
with open('honeyfs/fs-ubuntu22-aws.pickle', 'wb') as f:
    pickle.dump(fs, f)

print("✓ Realistic filesystem created: honeyfs/fs-ubuntu22-aws.pickle")
EOF

echo -e "${GREEN}✓ Filesystem created${NC}"

echo -e "${YELLOW}Step 2: Creating realistic process list${NC}"
cat > processes-aws.txt << 'EOF'
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 168756 12024 ?        Ss   Nov10   0:42 /sbin/init
root       234  0.0  0.0  20476  8456 ?        S<s  Nov10   0:00 /lib/systemd/systemd-journald -o journal
systemd+   456  0.0  0.0  98732  5234 ?        Ssl  Nov10   0:15 /usr/sbin/rsyslogd -n -iNONE
root       567  0.0  0.1 186432 16789 ?        Ssl  Nov10   1:23 /usr/bin/python3 /usr/bin/amazon-ssm-agent
root       678  0.0  0.2 1256789 23456 ?       Ssl  Nov10   2:34 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root       789  0.0  0.1 112344 18901 ?        Ssl  Nov10   0:45 /usr/bin/containerd
root       890  0.0  0.0  77664  8234 ?        Ss   Nov10   0:12 /usr/sbin/sshd -D
root       901  0.0  0.0  65432  7890 ?        Ss   Nov10   0:05 /usr/sbin/cron -f
ubuntu    1234  0.0  0.0  21456  5432 ?        S    10:23   0:00 sshd: ubuntu@pts/0
ubuntu    1235  0.0  0.0  23456  6543 pts/0    Ss   10:23   0:00 -bash
root      2345  0.1  1.2 345678 98765 ?        Ssl  Nov11   8:45 docker-containerd-shim -namespace moby
root      2346  0.0  0.5 123456 45678 ?        Sl   Nov11   2:15 nginx: master process nginx -g daemon off
www-data  2347  0.0  0.2 123789 23456 ?        S    Nov11   0:30 nginx: worker process
www-data  2348  0.0  0.2 123789 23456 ?        S    Nov11   0:30 nginx: worker process
ubuntu    5678  0.0  0.0  38456  3214 pts/0    R+   11:45   0:00 ps aux
EOF
echo -e "${GREEN}✓ Process list created${NC}"

echo -e "${YELLOW}Step 3: Creating realistic web content${NC}"
mkdir -p web_content
cd web_content

# Index page
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production API Gateway - MyCompany</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .status { color: #28a745; font-weight: bold; }
        .warning { background: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 20px 0; }
        ul { list-style: none; padding: 0; }
        li { margin: 10px 0; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        footer { margin-top: 40px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>MyCompany Production API Gateway</h1>
    <p class="status">● All Systems Operational</p>
    <p>Last deployment: 2024-11-10 14:23:15 UTC</p>
    <p>Build: <code>v1.2.3-a4f8d9c</code></p>

    <div class="warning">
        <strong>⚠️ Authorized Personnel Only</strong><br>
        This system is for authorized use only. All activity is monitored and logged.
    </div>

    <h2>Available Endpoints</h2>
    <ul>
        <li>📊 <a href="/api/v1/status">API Status</a></li>
        <li>📈 <a href="/api/v1/metrics">System Metrics</a></li>
        <li>📚 <a href="/api/v1/docs">API Documentation</a></li>
        <li>🔒 <a href="/admin">Admin Panel</a> (Requires Authentication)</li>
    </ul>

    <h2>System Information</h2>
    <ul>
        <li>Region: us-east-1</li>
        <li>Environment: Production</li>
        <li>Instance: i-0abc123def456789</li>
    </ul>

    <footer>
        &copy; 2024 MyCompany Inc. | <a href="/robots.txt">robots.txt</a> | <a href="/sitemap.xml">sitemap</a>
    </footer>
</body>
</html>
EOF

# robots.txt with interesting paths
cat > robots.txt << 'EOF'
User-agent: *
Disallow: /admin/
Disallow: /api/internal/
Disallow: /.git/
Disallow: /.env
Disallow: /backup/
Disallow: /config/
Disallow: /credentials/
Allow: /api/v1/
EOF

# .env file (honeytoken!)
cat > .env << 'EOF'
APP_NAME=ProductionAPI
APP_ENV=production
APP_KEY=base64:abcdef1234567890PRODUCTIONKEY==
APP_DEBUG=false
APP_URL=https://api.mycompany.com

DB_CONNECTION=mysql
DB_HOST=production-db.c9akr8fi.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_DATABASE=prod_app
DB_USERNAME=app_admin
DB_PASSWORD=P@ssw0rd_Prod_DB_2024!

REDIS_HOST=production-redis.abc123.cache.amazonaws.com
REDIS_PASSWORD=Redis_P@ss_2024!
REDIS_PORT=6379

AWS_ACCESS_KEY_ID=AKIA3OPRODKEY456789
AWS_SECRET_ACCESS_KEY=ProdSecretKey123456789ExampleSecret
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=mycompany-production-data

STRIPE_KEY=sk_live_EXAMPLE_HONEYTOKEN_FAKE_KEY_00001
STRIPE_SECRET=sk_live_EXAMPLE_HONEYTOKEN_FAKE_SECRET_00002

SENDGRID_API_KEY=SG_EXAMPLE_HONEYTOKEN_NOT_REAL_KEY

JWT_SECRET=super-secret-jwt-key-production-2024
EOF

cd "$PROJECT_ROOT"
echo -e "${GREEN}✓ Web content created${NC}"

echo -e "${YELLOW}Step 4: Creating deployment instructions${NC}"
cat > ANTI_DETECTION_DEPLOY.md << 'EOF'
# Anti-Detection Deployment Instructions

## Files Created

1. `honeyfs/fs-ubuntu22-aws.pickle` - Realistic filesystem for Cowrie
2. `processes-aws.txt` - Realistic process list
3. `web_content/` - Realistic web application content
4. `config/cowrie_realistic.cfg` - Hardened Cowrie configuration

## Deployment Steps

### 1. Copy Files to EC2 Instance

```bash
# Copy filesystem and configs
scp -i your-key.pem honeyfs/fs-ubuntu22-aws.pickle ubuntu@<EC2-IP>:/tmp/
scp -i your-key.pem processes-aws.txt ubuntu@<EC2-IP>:/tmp/
scp -i your-key.pem -r web_content ubuntu@<EC2-IP>:/tmp/
```

### 2. Deploy on EC2

SSH into your EC2 instance and run:

```bash
# Install Cowrie (if not already installed)
sudo apt update
sudo apt install -y python3-virtualenv git

# Clone Cowrie
git clone https://github.com/cowrie/cowrie /opt/cowrie
cd /opt/cowrie

# Setup virtualenv
virtualenv cowrie-env
source cowrie-env/bin/activate
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Copy realistic filesystem
sudo mkdir -p /opt/cowrie/share/cowrie
sudo cp /tmp/fs-ubuntu22-aws.pickle /opt/cowrie/share/cowrie/
sudo cp /tmp/processes-aws.txt /opt/cowrie/share/cowrie/

# Copy realistic config
sudo cp /path/to/cowrie_realistic.cfg /opt/cowrie/etc/cowrie.cfg

# Start Cowrie
bin/cowrie start

# Setup nginx with realistic content
sudo apt install -y nginx
sudo cp -r /tmp/web_content/* /var/www/html/
sudo systemctl restart nginx
```

### 3. Start Traffic Normalizer

From your control machine:

```bash
python src/traffic_normalizer.py <EC2-IP> &
```

### 4. Verify Deployment

```bash
# Test SSH honeypot
ssh -p 2222 ubuntu@<EC2-IP>

# Test web honeypot
curl http://<EC2-IP>/
curl http://<EC2-IP>/.env
```

## Success Indicators

- SSH banner shows "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
- Web server doesn't reveal "nginx" in headers
- Filesystem has realistic .bash_history
- Fake credentials are accessible
- Process list looks like real Ubuntu system

EOF

echo -e "${GREEN}✓ Deployment instructions created${NC}"

echo ""
echo "=================================="
echo -e "${GREEN}Anti-Detection Setup Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Review ANTI_DETECTION_DEPLOY.md for deployment instructions"
echo "2. Copy files to your EC2 honeypot instance"
echo "3. Start traffic normalizer for realistic background activity"
echo "4. Run experiments and monitor dwell time metrics"
echo ""
echo "Files created:"
echo "  - honeyfs/fs-ubuntu22-aws.pickle (realistic filesystem)"
echo "  - processes-aws.txt (realistic process list)"
echo "  - web_content/ (realistic web content with honeytokens)"
echo "  - ANTI_DETECTION_DEPLOY.md (deployment guide)"
echo ""
