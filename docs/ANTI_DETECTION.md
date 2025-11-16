# Honeypot Anti-Detection and Dwell Time Maximization

## Overview

The effectiveness of honeypots is measured by **dwell time** - how long attackers interact before detecting deception. This document covers techniques to make DeceptiCloud honeypots indistinguishable from real systems.

## The Detection Problem

Attackers use multiple techniques to identify honeypots:
- **Fingerprinting**: Known signatures in default configurations
- **Behavioral Analysis**: Unrealistic system responses
- **Network Analysis**: Suspicious timing patterns, lack of real users
- **Content Analysis**: Empty filesystems, fake data
- **Service Enumeration**: Missing or suspicious services
- **Timing Analysis**: Too-fast responses, lack of system load

---

## Anti-Detection Strategy

### 1. Cowrie SSH Honeypot Hardening

#### Problem: Default Cowrie Fingerprints
```bash
# Attackers detect Cowrie by:
- Banner: "SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2"
- Fake filesystem has unrealistic timestamps
- Missing common files (/var/log/auth.log, .bash_history)
- Commands return too quickly (no CPU load simulation)
- No real users logged in (w, who commands show empty)
```

#### Solution: Realistic Cowrie Configuration

**File: `config/cowrie_realistic.cfg`**
```ini
[honeypot]
# Randomize hostname per deployment
hostname = ${random_aws_hostname}

# Realistic SSH banner (match actual AWS Ubuntu instances)
ssh_version_string = SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6

# Enable all authentication methods
auth_class = UserDB
auth_class_parameters = userdb.txt

# Realistic delays (simulate system load)
backend_ssh_exec_delay = 0.2-2.0  # Random delay for commands

[shell]
# Use realistic filesystem (captured from real Ubuntu 22.04 AWS instance)
filesystem = /opt/cowrie/honeyfs/ubuntu22-aws.pickle

# Process list from real system
processes = /opt/cowrie/etc/processes-aws.txt

# Kernel version matching AWS AMI
kernel_version = 5.15.0-1052-aws
kernel_build_string = #57-Ubuntu SMP Tue Nov 14 10:54:31 UTC 2023

# Realistic hardware info
hardware_platform = x86_64
operating_system = GNU/Linux

[output_jsonlog]
# Log everything for analysis
logfile = /var/log/cowrie/cowrie.json

[backend_pool]
# Make command execution realistic
pool_only = false
pool_max_vms = 5
vm_dirty_defer = true

[proxy]
# Optional: Proxy some commands to real low-interaction VM
backend = pool
backend_ssh_host = localhost
backend_ssh_port = 2223
```

#### Realistic Filesystem Population

**File: `scripts/setup_realistic_cowrie.sh`**
```bash
#!/bin/bash
# Create realistic filesystem for Cowrie

COWRIE_FS="/opt/cowrie/honeyfs"
mkdir -p "$COWRIE_FS"

# Copy filesystem structure from real Ubuntu 22.04
# (Run this on a real AWS EC2 instance first)
python3 << 'EOF'
import pickle
import os
from datetime import datetime, timedelta

# Create realistic filesystem with proper timestamps
fs = {
    '/': {'type': 'directory', 'mtime': datetime.now() - timedelta(days=180)},
    '/home/ubuntu': {'type': 'directory', 'mtime': datetime.now() - timedelta(days=30)},
    '/home/ubuntu/.bash_history': {
        'type': 'file',
        'content': '''sudo apt update
sudo apt upgrade -y
docker ps
docker run -d nginx
curl https://api.github.com/repos/my-app/releases
git clone https://github.com/mycompany/production-app.git
cd production-app
./deploy.sh
sudo systemctl restart nginx
tail -f /var/log/nginx/access.log
''',
        'mtime': datetime.now() - timedelta(hours=2)
    },
    '/home/ubuntu/.ssh/authorized_keys': {
        'type': 'file',
        'content': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDc... ubuntu@ip-10-0-1-42',
        'mtime': datetime.now() - timedelta(days=45)
    },
    '/var/log/auth.log': {
        'type': 'file',
        'content': '''Nov 15 10:23:45 ip-10-0-1-42 sshd[1234]: Accepted publickey for ubuntu from 203.0.113.45 port 52341 ssh2
Nov 15 10:25:12 ip-10-0-1-42 sudo: ubuntu : TTY=pts/0 ; PWD=/home/ubuntu ; USER=root ; COMMAND=/usr/bin/apt update
Nov 15 11:30:22 ip-10-0-1-42 sshd[1456]: Accepted publickey for ubuntu from 203.0.113.45 port 52387 ssh2
''',
        'mtime': datetime.now() - timedelta(hours=1)
    },
    '/etc/passwd': {
        'type': 'file',
        'content': '''root:x:0:0:root:/root:/bin/bash
ubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash
systemd-timesync:x:100:102:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin
''',
        'mtime': datetime.now() - timedelta(days=120)
    },
    '/var/www/html/index.html': {
        'type': 'file',
        'content': '<html><body><h1>Production API Server</h1></body></html>',
        'mtime': datetime.now() - timedelta(days=60)
    },
    '/home/ubuntu/.aws/credentials': {
        'type': 'file',
        'content': '''[default]
aws_access_key_id = AKIA3OEXAMPLEKEY123
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
region = us-east-1
''',
        'mtime': datetime.now() - timedelta(days=30)
    },
    '/opt/app/config.json': {
        'type': 'file',
        'content': '''{
  "database": {
    "host": "production-db.internal",
    "user": "app_user",
    "password": "P@ssw0rd_Prod_2024!"
  },
  "api_keys": {
    "stripe": "sk_live_51ABC123...",
    "sendgrid": "SG.xyz789..."
  }
}''',
        'mtime': datetime.now() - timedelta(days=90)
    }
}

# Add realistic cron jobs
fs['/var/spool/cron/crontabs/ubuntu'] = {
    'type': 'file',
    'content': '''# Run backup daily
0 2 * * * /opt/scripts/backup.sh
# Health check every 5 minutes
*/5 * * * * curl -s http://localhost:8080/health
''',
    'mtime': datetime.now() - timedelta(days=15)
}

# Save filesystem
with open('ubuntu22-aws.pickle', 'wb') as f:
    pickle.dump(fs, f)
print("Realistic filesystem created!")
EOF
```

#### Realistic Process List

**File: `config/processes-aws.txt`**
```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 168756 12024 ?        Ss   Nov10   0:42 /sbin/init
root       234  0.0  0.0  20476  8456 ?        S<s  Nov10   0:00 /lib/systemd/systemd-journald
root       456  0.0  0.0  98732  5234 ?        Ssl  Nov10   0:15 /usr/sbin/rsyslogd
root       567  0.0  0.1 186432 16789 ?        Ssl  Nov10   1:23 /usr/bin/python3 /usr/bin/amazon-ssm-agent
root       678  0.0  0.2 1256789 23456 ?       Ssl  Nov10   2:34 /usr/bin/dockerd
ubuntu    1234  0.0  0.0  21456  5432 ?        S    10:23   0:00 sshd: ubuntu@pts/0
ubuntu    1235  0.0  0.0  23456  6543 pts/0    Ss   10:23   0:00 -bash
root      2345  0.1  1.2 345678 98765 ?        Ssl  Nov11   8:45 /usr/bin/docker-containerd
root      3456  0.0  0.5 123456 45678 ?        Sl   Nov12   2:15 docker run -d nginx
ubuntu    5678  0.0  0.0  38456  3214 pts/0    R+   11:45   0:00 ps aux
```

---

### 2. Nginx Web Honeypot Hardening

#### Problem: Default Nginx is Obvious
```
- Default welcome page
- Server header reveals "nginx/1.24.0"
- No real application content
- Missing common files (robots.txt, favicon.ico)
- No SSL/TLS
- Unrealistic response times
```

#### Solution: Realistic Web Application Simulation

**File: `config/nginx_deception.conf`**
```nginx
# Hide nginx version
server_tokens off;
more_clear_headers Server;
more_set_headers 'Server: Apache/2.4.52 (Ubuntu)';  # Pretend to be Apache

# Add realistic headers
more_set_headers 'X-Powered-By: PHP/8.1.2';
more_set_headers 'X-Frame-Options: SAMEORIGIN';

server {
    listen 80;
    server_name production-api.example.internal;

    root /var/www/html;
    index index.php index.html;

    # Log everything
    access_log /var/log/nginx/access.log combined;
    error_log /var/log/nginx/error.log;

    # Realistic robots.txt
    location = /robots.txt {
        return 200 "User-agent: *\nDisallow: /admin/\nDisallow: /api/internal/\nDisallow: /.git/\n";
    }

    # Fake admin panel (credential harvesting)
    location /admin {
        auth_basic "Production Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://localhost:8080;  # Backend honeypot
    }

    # Fake API endpoints with realistic responses
    location /api/v1/ {
        # Add artificial delay (simulate database query)
        echo_sleep 0.2;

        if ($request_method = GET) {
            return 200 '{"status":"ok","version":"1.2.3","environment":"production"}';
        }
    }

    # Common vulnerability paths (LFI/RFI honeytokens)
    location ~ \.(git|env|aws|config\.json)$ {
        # Log the attempt but return fake content
        access_log /var/log/nginx/sensitive_access.log combined;

        # Fake AWS credentials (honeytokens)
        if ($request_uri ~ "\.aws/credentials") {
            return 200 "[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE\naws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n";
        }
    }

    # Fake phpMyAdmin (common attack target)
    location /phpmyadmin {
        proxy_pass http://localhost:8081;  # Fake PHPMyAdmin honeypot
    }

    # WordPress simulation
    location /wp-admin {
        proxy_pass http://localhost:8082;  # Fake WordPress
    }

    # Delay responses randomly to simulate load
    location / {
        set $delay 0.1;
        if ($http_user_agent ~* (bot|crawler|spider)) {
            set $delay 0.5;
        }
        echo_sleep $delay;
        try_files $uri $uri/ =404;
    }
}
```

**File: `scripts/setup_realistic_web_content.sh`**
```bash
#!/bin/bash
# Populate nginx with realistic content

WEB_ROOT="/var/www/html"
mkdir -p "$WEB_ROOT"

# Realistic index page
cat > "$WEB_ROOT/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Production API Gateway</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <h1>API Gateway - Production Environment</h1>
    <p>Last deployment: 2024-11-10 14:23 UTC</p>
    <p>Status: <span style="color:green">●</span> All systems operational</p>
    <ul>
        <li><a href="/api/v1/status">API Status</a></li>
        <li><a href="/api/v1/metrics">Metrics</a></li>
        <li><a href="/admin">Admin Panel</a> (Authorized Personnel Only)</li>
    </ul>
    <!-- Build: prod-v1.2.3-a4f8d9c -->
</body>
</html>
EOF

# Fake configuration files (honeytokens)
mkdir -p "$WEB_ROOT/.git"
cat > "$WEB_ROOT/.git/config" << 'EOF'
[core]
	repositoryformatversion = 0
	filemode = true
[remote "origin"]
	url = https://github.com/mycompany/production-api.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
	remote = origin
	merge = refs/heads/master
[user]
	name = devops-bot
	email = devops@example.com
EOF

# Fake .env with credentials (honeytoken)
cat > "$WEB_ROOT/.env" << 'EOF'
APP_ENV=production
APP_KEY=base64:abcdef1234567890EXAMPLE==
DB_CONNECTION=mysql
DB_HOST=production-db.internal.example.com
DB_PORT=3306
DB_DATABASE=prod_app
DB_USERNAME=app_admin
DB_PASSWORD=P@ssw0rd_Prod_2024!

AWS_ACCESS_KEY_ID=AKIA3OEXAMPLEKEY456
AWS_SECRET_ACCESS_KEY=abcdef1234567890EXAMPLESECRETKEY

STRIPE_SECRET=sk_live_51ABC123XYZ789...
SENDGRID_API_KEY=SG.xyz789ABC123...

# Redis cache
REDIS_HOST=production-redis.internal
REDIS_PASSWORD=redis_P@ss2024!
EOF

# Realistic favicon
echo "data:image/x-icon;base64,..." > "$WEB_ROOT/favicon.ico"

# Fake sitemap
cat > "$WEB_ROOT/sitemap.xml" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://api.example.com/</loc><changefreq>daily</changefreq></url>
  <url><loc>https://api.example.com/api/v1/status</loc><changefreq>hourly</changefreq></url>
  <url><loc>https://api.example.com/docs</loc><changefreq>weekly</changefreq></url>
</urlset>
EOF

echo "Realistic web content deployed!"
```

---

### 3. Advanced Deception Techniques

#### A. Honeytokens (Breadcrumbs)

Fake credentials and data that attract attackers and generate high-fidelity alerts.

**Implementation:**
```python
# File: src/honeytokens.py

HONEYTOKENS = {
    'aws_credentials': {
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'alert_on_use': True
    },
    'database_credentials': {
        'host': 'production-db.internal.example.com',
        'user': 'app_admin',
        'password': 'P@ssw0rd_Prod_2024!',
        'database': 'prod_app'
    },
    'api_keys': {
        'stripe': 'sk_live_51ABC123XYZ789EXAMPLE',
        'sendgrid': 'SG.xyz789ABC123EXAMPLE'
    }
}

def monitor_honeytoken_usage():
    """
    Monitor AWS CloudTrail for usage of fake credentials.
    If attacker tries to use them, we get high-confidence alert.
    """
    import boto3

    cloudtrail = boto3.client('cloudtrail')

    # Check for any API calls using honeytoken access key
    events = cloudtrail.lookup_events(
        LookupAttributes=[
            {'AttributeKey': 'AccessKeyId',
             'AttributeValue': HONEYTOKENS['aws_credentials']['access_key']}
        ]
    )

    if events['Events']:
        print("🚨 ALERT: Honeytoken AWS credential used!")
        print(f"Source IP: {events['Events'][0]['SourceIPAddress']}")
        print(f"Action: {events['Events'][0]['EventName']}")
        return True
    return False
```

#### B. Active Deception - Fake Services

Run additional fake services to increase realism.

**File: `docker-compose.deception.yml`**
```yaml
version: '3.8'

services:
  # Main SSH honeypot
  cowrie:
    image: cowrie/cowrie:latest
    ports:
      - "2222:2222"
    volumes:
      - ./config/cowrie_realistic.cfg:/cowrie/cowrie.cfg
      - ./honeyfs/ubuntu22-aws.pickle:/cowrie/honeyfs/ubuntu22-aws.pickle
      - ./logs/cowrie:/cowrie/var/log/cowrie
    restart: unless-stopped

  # Main web honeypot
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./config/nginx_deception.conf:/etc/nginx/conf.d/default.conf
      - ./web_content:/var/www/html
      - ./logs/nginx:/var/log/nginx
    restart: unless-stopped

  # Fake MySQL (port scan decoy)
  fake-mysql:
    image: alpine:latest
    command: nc -l -p 3306 -k
    ports:
      - "3306:3306"
    restart: unless-stopped

  # Fake Redis (another decoy)
  fake-redis:
    image: alpine:latest
    command: nc -l -p 6379 -k -e echo "+PONG"
    ports:
      - "6379:6379"
    restart: unless-stopped

  # Fake PHPMyAdmin (credential harvester)
  fake-phpmyadmin:
    image: nginx:alpine
    volumes:
      - ./fake_services/phpmyadmin:/usr/share/nginx/html
    ports:
      - "8081:80"
    restart: unless-stopped

  # Simulated real user activity
  user-simulator:
    image: alpine:latest
    command: >
      sh -c "while true; do
        ssh -p 2222 ubuntu@cowrie 'ls; whoami; date' 2>/dev/null || true;
        curl -s http://nginx/api/v1/status >/dev/null 2>&1 || true;
        sleep $((RANDOM % 300 + 60));
      done"
    restart: unless-stopped
```

#### C. Traffic Normalization

Make honeypot traffic indistinguishable from real systems.

```python
# File: src/traffic_normalizer.py

import random
import time
import threading

class TrafficNormalizer:
    """
    Generates realistic background traffic to honeypots
    to mask their nature from network analysis.
    """

    def __init__(self, ssh_host, web_host):
        self.ssh_host = ssh_host
        self.web_host = web_host
        self.running = False

    def simulate_legitimate_ssh_sessions(self):
        """Simulate periodic legitimate SSH logins."""
        import paramiko

        while self.running:
            try:
                # Random delay between sessions (1-6 hours)
                time.sleep(random.randint(3600, 21600))

                # Login as 'ubuntu' with key
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ssh_host, port=2222,
                           username='ubuntu',
                           key_filename='/opt/fake_keys/ubuntu.pem')

                # Execute realistic commands
                commands = [
                    'uptime',
                    'df -h',
                    'docker ps',
                    'tail -n 20 /var/log/syslog',
                    'free -m'
                ]

                for cmd in random.sample(commands, k=random.randint(2, 4)):
                    ssh.exec_command(cmd)
                    time.sleep(random.uniform(2, 10))

                ssh.close()

            except Exception:
                pass

    def simulate_legitimate_web_traffic(self):
        """Simulate periodic legitimate web requests."""
        import requests

        while self.running:
            try:
                time.sleep(random.randint(60, 600))  # 1-10 minutes

                # Realistic user agent
                ua = random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'curl/7.68.0',
                    'python-requests/2.28.1'
                ])

                # Normal endpoints
                endpoints = ['/api/v1/status', '/api/v1/metrics', '/health']

                requests.get(
                    f'http://{self.web_host}{random.choice(endpoints)}',
                    headers={'User-Agent': ua},
                    timeout=5
                )

            except Exception:
                pass

    def start(self):
        """Start background traffic generation."""
        self.running = True

        threading.Thread(target=self.simulate_legitimate_ssh_sessions,
                        daemon=True).start()
        threading.Thread(target=self.simulate_legitimate_web_traffic,
                        daemon=True).start()

        print("Traffic normalizer started - generating realistic background traffic")

    def stop(self):
        """Stop background traffic."""
        self.running = False
```

---

### 4. Anti-Fingerprinting Checklist

**Before Deployment:**

- [ ] Change default Cowrie SSH banner
- [ ] Populate realistic filesystem with proper timestamps
- [ ] Add realistic user .bash_history files
- [ ] Configure realistic process list (ps aux)
- [ ] Add fake AWS credentials (honeytokens)
- [ ] Remove nginx version headers
- [ ] Add realistic web content (not default pages)
- [ ] Deploy honeytokens (.env, .git/config, .aws/credentials)
- [ ] Configure realistic response delays
- [ ] Add fake services (MySQL, Redis ports)
- [ ] Start traffic normalizer (simulated legitimate users)
- [ ] Verify no cowrie/honeypot strings in process names
- [ ] Test from attacker perspective

---

### 5. Dwell Time Metrics

**Track these metrics to measure effectiveness:**

```python
# File: src/dwell_time_metrics.py

class DwellTimeMetrics:
    """Track honeypot dwell time and detection rates."""

    def __init__(self):
        self.sessions = {}

    def session_start(self, session_id, source_ip):
        """Record session start."""
        self.sessions[session_id] = {
            'start': time.time(),
            'source_ip': source_ip,
            'commands': [],
            'detection_indicators': []
        }

    def log_command(self, session_id, command):
        """Log attacker command."""
        if session_id in self.sessions:
            self.sessions[session_id]['commands'].append(command)

            # Check for honeypot detection attempts
            detection_keywords = [
                'cowrie', 'honeypot', 'kippo', 'dionaea',
                'ps aux | grep python', '/proc/self/cwd',
                'uname -a | grep -i honey'
            ]

            if any(kw in command.lower() for kw in detection_keywords):
                self.sessions[session_id]['detection_indicators'].append(command)

    def session_end(self, session_id):
        """Calculate dwell time when session ends."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            dwell_time = time.time() - session['start']

            # Was honeypot detected?
            detected = len(session['detection_indicators']) > 0

            return {
                'dwell_time_seconds': dwell_time,
                'dwell_time_minutes': dwell_time / 60,
                'commands_executed': len(session['commands']),
                'detected': detected,
                'source_ip': session['source_ip']
            }
```

---

## Integration with DeceptiCloud

Update the RL reward function to optimize for dwell time:

```python
# Enhanced reward function in src/environment.py

def calculate_reward_with_dwell_time(self, next_state, dwell_time_minutes):
    """
    Reward function that considers both attack matching AND dwell time.

    Longer dwell time = more valuable intelligence gathered
    """
    reward = 0
    ssh_attack = int(next_state[0])
    web_attack = int(next_state[1])

    # Base rewards for matching
    if ssh_attack == 1 and self.current_honeypot == 1:
        reward += 10
    if web_attack == 1 and self.current_honeypot == 2:
        reward += 10

    # Penalty for running idle honeypot
    if self.current_honeypot != 0:
        if self.current_honeypot == 1 and ssh_attack == 0:
            reward -= 1
        elif self.current_honeypot == 2 and web_attack == 0:
            reward -= 1

    # BONUS: Reward for long dwell time (attacker didn't detect honeypot)
    if dwell_time_minutes > 10:
        reward += 5  # Successful deception!
    if dwell_time_minutes > 30:
        reward += 10  # Excellent deception!

    # PENALTY: Short session (likely detected)
    if dwell_time_minutes < 2 and (ssh_attack or web_attack):
        reward -= 5  # Attacker detected and left quickly

    return reward
```

---

## Recommended Deployment

1. **Use realistic configurations** (provided above)
2. **Deploy traffic normalizer** to generate background activity
3. **Enable honeytokens** and monitor for usage
4. **Track dwell time metrics** as primary success indicator
5. **Update configurations** based on detection patterns

## Success Criteria

- Average dwell time > 15 minutes (good)
- Average dwell time > 30 minutes (excellent)
- Detection rate < 10% (most attackers don't realize it's a honeypot)
- Honeytoken usage rate > 20% (attackers find and attempt to use fake credentials)

This makes DeceptiCloud honeypots production-grade and maximizes intelligence gathering time.
