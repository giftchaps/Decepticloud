# Complete Local Testing Guide

This guide walks you through testing DeceptiCloud locally from start to finish with all scripts and commands.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Manual Testing (Step-by-Step)](#manual-testing-step-by-step)
4. [Automated Testing](#automated-testing)
5. [Training the RL Agent](#training-the-rl-agent)
6. [Attack Simulation](#attack-simulation)
7. [Viewing Results](#viewing-results)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

**Windows:**
1. **Docker Desktop**: https://www.docker.com/products/docker-desktop
2. **Python 3.8+**: https://www.python.org/downloads/
3. **Git**: https://git-scm.com/downloads

**Linux/Mac:**
```bash
# Docker
sudo apt-get install docker.io docker-compose  # Ubuntu/Debian
brew install docker docker-compose  # macOS

# Python
sudo apt-get install python3 python3-pip  # Ubuntu/Debian
brew install python3  # macOS
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python --version

# Check you're in the right directory
ls main_local.py  # Should exist
```

---

## Quick Start (5 Minutes)

### Windows PowerShell

```powershell
# 1. Run automated test script
.\scripts\test_complete_local.ps1

# That's it! The script will:
# - Setup environment
# - Start honeypots
# - Test connectivity
# - Generate attacks
# - Run RL agent
# - Show results
```

### Linux/Mac

```bash
# 1. Run automated test script
bash scripts/test_complete_local.sh

# That's it! Same as Windows
```

**What you'll see:**
- ✓ Honeypots starting
- ✓ Tests passing
- ✓ Attack traffic generated
- ✓ RL agent training
- ✓ Results saved

**Skip to [Viewing Results](#viewing-results) when done!**

---

## Manual Testing (Step-by-Step)

If you want to understand each step or the automated script fails.

### Step 1: Setup Environment

**Windows:**
```powershell
# Create directories
New-Item -ItemType Directory -Path data\cowrie\logs,data\cowrie\downloads,data\nginx\logs,data\nginx\content -Force

# Create web content
@"
<!DOCTYPE html>
<html>
<head><title>API Gateway</title></head>
<body><h1>Production API Gateway</h1></body>
</html>
"@ | Out-File data\nginx\content\index.html -Encoding UTF8

# Create honeytoken file
@"
AWS_ACCESS_KEY_ID=AKIA3OEXAMPLEKEY123
DB_PASSWORD=HONEYTOKEN_FAKE
"@ | Out-File data\nginx\content\.env -Encoding UTF8
```

**Linux/Mac:**
```bash
bash scripts/setup_local_test.sh
```

### Step 2: Start Honeypots

```bash
# Start both honeypots
docker-compose -f docker-compose.local.yml up -d

# Wait 30 seconds for initialization
sleep 30

# Check status
docker ps
```

**Expected output:**
```
CONTAINER ID   IMAGE               STATUS         PORTS                    NAMES
abc123...      cowrie/cowrie       Up (healthy)   0.0.0.0:2222->2222/tcp   cowrie_honeypot_local
def456...      nginx:alpine        Up (healthy)   0.0.0.0:8080->80/tcp     nginx_honeypot_local
```

### Step 3: Test SSH Honeypot

```bash
# Connect to SSH honeypot
ssh -p 2222 root@localhost
# Password: password

# Try these commands:
whoami
ls -la
cat /etc/passwd
cat /home/ubuntu/.aws/credentials  # Honeytoken!
exit
```

### Step 4: Test Web Honeypot

**Browser:**
- Visit: http://localhost:8080
- Visit: http://localhost:8080/.env (honeytokens!)
- Visit: http://localhost:8080/robots.txt

**Command Line:**
```bash
# Test main page
curl http://localhost:8080/

# Test honeytoken
curl http://localhost:8080/.env

# Should see fake AWS credentials
```

### Step 5: View Initial Logs

```bash
# SSH honeypot logs
docker logs cowrie_honeypot_local

# Web honeypot logs
docker logs nginx_honeypot_local
```

---

## Automated Testing

Run comprehensive automated tests:

```bash
python scripts/test_local_honeypots.py
```

**What it tests:**
- ✓ Docker containers running
- ✓ SSH honeypot connectivity
- ✓ Web honeypot content
- ✓ Honeytoken accessibility
- ✓ Log generation
- ✓ Attack simulation

**Output:**
```
============================================================
DeceptiCloud Local Honeypot Test
============================================================

TEST 1: Docker Container Status
✓ cowrie_honeypot_local: healthy
✓ nginx_honeypot_local: healthy

TEST 2: SSH Honeypot (Cowrie) - localhost:2222
✓ SSH connection established
✓ Command 'whoami' executed successfully

TEST 3: Web Honeypot (nginx) - localhost:8080
✓ Index page accessible (status: 200)
✓ Honeytoken (.env) accessible with fake credentials!

TEST SUMMARY
Total Tests: 5
  ✓ Passed:  5

✓ ALL TESTS PASSED - Deployment is production-ready!
```

---

## Training the RL Agent

### Basic Training

```bash
# Train for 10 episodes
python main_local.py --episodes 10 --timesteps 24
```

### With Attack Simulation (Recommended!)

**Terminal 1 - Start Training:**
```bash
python main_local.py --episodes 10 --timesteps 24
```

**Terminal 2 - Simulate Attacks:**
```bash
# Run attack simulator while training
python scripts/simulate_attacks.py --duration 600 --intensity medium
```

**What happens:**
1. RL agent starts training
2. Agent deploys honeypots based on learned policy
3. Attack simulator generates realistic traffic
4. Agent detects attacks and learns
5. Rewards increase over time

**Expected Output (Terminal 1):**
```
Episode 1/10, Timestep 1/24
[Action] Deploying Cowrie SSH honeypot...
[Detection] SSH attack detected in Cowrie logs
[Reward] +10: SSH attack captured by Cowrie!  ← Good!

Episode 1/10, Timestep 2/24
[Action] Deploying nginx web honeypot...
[Detection] Web attack detected in nginx logs
[Reward] +10: Web attack captured by nginx!  ← Good!

Episode 1/10, Timestep 3/24
[Action] Stopping all honeypots...
[Reward] 0: No activity
```

### Advanced Training Options

```bash
# Long training run
python main_local.py --episodes 50 --timesteps 48

# Quick test
python main_local.py --episodes 2 --timesteps 5

# Custom target
python main_local.py --episodes 10 --target 192.168.1.100
```

---

## Attack Simulation

Generate realistic attack traffic for testing.

### Basic Simulation

```bash
# Medium intensity for 5 minutes
python scripts/simulate_attacks.py --duration 300 --intensity medium
```

### Intensity Levels

**Low Intensity:**
```bash
python scripts/simulate_attacks.py --intensity low --duration 300
```
- 2 SSH brute force attempts
- 5 web enumeration requests
- 2 SQL injection attempts
- 1 credential stuffing attempt

**Medium Intensity (Default):**
```bash
python scripts/simulate_attacks.py --intensity medium --duration 300
```
- 5 SSH brute force attempts
- 10 web enumeration requests
- 5 SQL injection attempts
- 3 credential stuffing attempts

**High Intensity:**
```bash
python scripts/simulate_attacks.py --intensity high --duration 600
```
- 10 SSH brute force attempts
- 20 web enumeration requests
- 10 SQL injection attempts
- 5 credential stuffing attempts

### Continuous Mode

```bash
# Run until you stop it (Ctrl+C)
python scripts/simulate_attacks.py --continuous --intensity high
```

### Manual Attack Simulation

**SSH Attacks:**
```bash
# Brute force
for user in root admin ubuntu; do
  for pass in password 123456 admin; do
    ssh -p 2222 $user@localhost
  done
done
```

**Web Attacks:**
```bash
# Enumeration
for path in / /admin /.env /.git/config /backup.sql; do
  curl http://localhost:8080$path
done

# SQL injection
curl "http://localhost:8080/api?id=1' OR '1'='1"
```

---

## Viewing Results

### Training Results

**CSV Files:**
```bash
# Timestep-level data
cat results/local_timesteps.csv

# Episode-level data
cat results/local_episodes.csv
```

**Columns in local_timesteps.csv:**
- Episode, Timestep, Action, Reward, SSH_Attack, Web_Attack, Timestamp

**Columns in local_episodes.csv:**
- Episode, Total_Reward, Epsilon, Timestamp

### Plot Results

**Using Python:**
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('results/local_episodes.csv')

# Plot total rewards
plt.figure(figsize=(10,6))
plt.plot(df['Episode'], df['Total_Reward'], marker='o')
plt.xlabel('Episode')
plt.ylabel('Total Reward')
plt.title('RL Agent Learning Progress')
plt.grid(True)
plt.savefig('results/learning_curve.png')
plt.show()
```

### Honeypot Logs

**Cowrie SSH Logs (JSON):**
```bash
# View all logs
docker logs cowrie_honeypot_local

# View JSON logs (if jq installed)
docker exec cowrie_honeypot_local cat /cowrie/cowrie-git/var/log/cowrie/cowrie.json | jq

# Count login attempts
docker exec cowrie_honeypot_local cat /cowrie/cowrie-git/var/log/cowrie/cowrie.json | grep "login" | wc -l

# View from mounted volume
cat data/cowrie/logs/cowrie.json
```

**nginx Web Logs:**
```bash
# View access log
docker logs nginx_honeypot_local

# View from mounted volume
cat data/nginx/logs/access.log

# Count requests
wc -l data/nginx/logs/access.log

# Filter for honeytokens
grep ".env" data/nginx/logs/access.log
```

### Saved Models

```bash
# List saved models
ls -lh models/

# Models saved every 5 episodes
models/local_dqn_episode_5.pth
models/local_dqn_episode_10.pth
```

---

## Troubleshooting

### Issue: Docker not found

**Solution:**
```bash
# Windows: Install Docker Desktop
# https://www.docker.com/products/docker-desktop

# Linux:
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Containers won't start

**Check Docker:**
```bash
# Is Docker running?
docker ps

# Check Docker Compose
docker-compose -f docker-compose.local.yml ps

# View errors
docker-compose -f docker-compose.local.yml logs
```

**Restart containers:**
```bash
docker-compose -f docker-compose.local.yml restart
```

**Clean restart:**
```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

### Issue: Port already in use

**Find what's using the port:**
```bash
# Windows
netstat -ano | findstr :2222
netstat -ano | findstr :8080

# Linux/Mac
lsof -i :2222
lsof -i :8080
```

**Change ports** in `docker-compose.local.yml`:
```yaml
services:
  cowrie:
    ports:
      - "2223:2222"  # Changed from 2222
```

### Issue: SSH connection refused

**Wait for Cowrie to start:**
```bash
# Check container status
docker ps

# Wait 30 seconds
sleep 30

# Try again
ssh -p 2222 root@localhost
```

**Check Cowrie logs:**
```bash
docker logs cowrie_honeypot_local
```

### Issue: No attacks detected

**Make sure to generate attacks while training!**

**Option 1 - Run attack simulator:**
```bash
python scripts/simulate_attacks.py --duration 300
```

**Option 2 - Manual attacks:**
```bash
# SSH
ssh -p 2222 root@localhost

# Web
curl http://localhost:8080/.env
```

### Issue: Agent gets negative rewards

**Problem:** No attacks happening, so honeypots waste resources.

**Solution:** Run attack simulator in parallel:
```bash
# Terminal 1
python main_local.py --episodes 10

# Terminal 2
python scripts/simulate_attacks.py --continuous
```

### Issue: Permission denied (Linux)

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/

# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

---

## Best Practices

### 1. Always Run Attack Simulator During Training

```bash
# Terminal 1
python main_local.py --episodes 20

# Terminal 2
python scripts/simulate_attacks.py --continuous --intensity medium
```

### 2. Check Logs Regularly

```bash
# Quick health check
docker ps
docker logs --tail 20 cowrie_honeypot_local
docker logs --tail 20 nginx_honeypot_local
```

### 3. Save Your Models

```bash
# Models are saved automatically every 5 episodes
ls models/

# Back them up
cp -r models/ models_backup/
```

### 4. Clean Up When Done

```bash
# Stop containers (keep data)
docker-compose -f docker-compose.local.yml stop

# Remove containers (keep data)
docker-compose -f docker-compose.local.yml down

# Remove everything including data
docker-compose -f docker-compose.local.yml down -v
rm -rf data/
```

---

## Complete Workflow Example

Here's a complete testing session:

```bash
# 1. Setup
bash scripts/setup_local_test.sh

# 2. Start honeypots
docker-compose -f docker-compose.local.yml up -d
sleep 30

# 3. Test manually
ssh -p 2222 root@localhost  # Password: password
curl http://localhost:8080/.env

# 4. Run automated tests
python scripts/test_local_honeypots.py

# 5. Start training (Terminal 1)
python main_local.py --episodes 20 --timesteps 24

# 6. Simulate attacks (Terminal 2)
python scripts/simulate_attacks.py --duration 1200 --intensity medium

# 7. View results
cat results/local_episodes.csv
docker logs cowrie_honeypot_local | grep -i "login"

# 8. Clean up
docker-compose -f docker-compose.local.yml down
```

---

## Next Steps

After successful local testing:

1. **Analyze Results**
   ```bash
   jupyter notebook notebooks/01_data_analysis.ipynb
   ```

2. **Tune Hyperparameters**
   - Edit `main_local.py`
   - Adjust learning rate, epsilon decay, etc.

3. **Deploy to AWS**
   ```bash
   # See PRODUCTION_QUICK_START.md
   cd infra
   terraform apply
   ```

4. **Run Production Experiments**
   ```bash
   python main.py --episodes 100
   ```

---

## Quick Reference

### Essential Commands

```bash
# Start everything
docker-compose -f docker-compose.local.yml up -d

# Check status
docker ps

# View logs
docker logs -f cowrie_honeypot_local
docker logs -f nginx_honeypot_local

# Test honeypots
ssh -p 2222 root@localhost
curl http://localhost:8080/.env

# Train agent
python main_local.py --episodes 10

# Simulate attacks
python scripts/simulate_attacks.py --duration 300

# Stop everything
docker-compose -f docker-compose.local.yml down
```

### Port Reference

- **2222** - SSH honeypot (Cowrie)
- **8080** - Web honeypot (nginx)
- **22** - Not used (avoid conflict with host SSH)
- **80** - Not used (avoid conflict with host web servers)

### File Locations

- **Cowrie logs**: `data/cowrie/logs/cowrie.json`
- **nginx logs**: `data/nginx/logs/access.log`
- **Training results**: `results/local_*.csv`
- **Models**: `models/local_dqn_episode_*.pth`
- **Test results**: `local_test_results_*.json`

---

## Support

If you encounter issues not covered here:

1. Check **LOCAL_TESTING.md** for detailed troubleshooting
2. Check **WINDOWS_QUICKSTART.md** for Windows-specific help
3. Review Docker logs for errors
4. Ensure all prerequisites are installed
5. Try the automated test script first

**Happy Testing! 🚀**
