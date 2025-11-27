# Windows Quick Start Guide

## What Happened When You Ran `python main.py`?

You ran the **AWS production version** which expects:
- An EC2 instance to SSH into
- AWS CloudWatch for metrics
- Honeypots deployed on EC2

But you're on Windows without Docker containers running locally, so:
- ❌ SSH connection to localhost:22 failed (doesn't exist on Windows)
- ❌ Honeypots never started (tried to deploy on EC2, not locally)
- ❌ Attacker couldn't connect to port 2222 (no honeypot listening)
- ⚠️ CloudWatch metrics failed (numpy float32 type issue)
- ✅ RL agent DID run and learn (but got negative rewards because no honeypots)

## The Solution: Use Local Docker Testing

### Option 1: Local Docker Testing (Recommended for Windows)

This is what you should do to test locally on your Windows machine.

#### Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows: https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Start Docker Desktop
4. Verify installation:
   ```powershell
   docker --version
   ```

#### Step 2: Set Up DeceptiCloud Honeypots

Open PowerShell in your DeceptiCloud directory:

```powershell
cd C:\Users\gift2\OneDrive\Desktop\Research\Decepticloud

# Run setup script (creates directories and content)
bash scripts/setup_local_test.sh

# If bash doesn't work, manually create directories:
mkdir data\cowrie\logs, data\cowrie\downloads, data\nginx\logs, data\nginx\content -Force
```

#### Step 3: Start Honeypots

```powershell
# Start both honeypots
docker-compose -f docker-compose.local.yml up -d

# Check they're running
docker-compose -f docker-compose.local.yml ps

# You should see:
# cowrie_honeypot_local     Up (healthy)
# nginx_honeypot_local      Up (healthy)
```

#### Step 4: Test Honeypots Manually

**Test SSH honeypot:**
```powershell
# Install SSH client if not available (Windows 10/11 has it built-in)
ssh -p 2222 root@localhost
# Password: password

# Try some commands:
whoami
ls
cat /etc/passwd
exit
```

**Test web honeypot:**
```powershell
# Test with browser or PowerShell
curl http://localhost:8080/
curl http://localhost:8080/.env  # See honeytokens!
```

#### Step 5: Run RL Agent (Local Version)

```powershell
# Use the LOCAL version of main.py
python main_local.py --episodes 5 --timesteps 24
```

**While training is running**, open another PowerShell window and simulate attacks:

```powershell
# Terminal 2: SSH attacks
ssh -p 2222 root@localhost
ssh -p 2222 admin@localhost
ssh -p 2222 ubuntu@localhost

# Terminal 2: Web attacks
curl http://localhost:8080/admin
curl http://localhost:8080/.env
curl http://localhost:8080/.git/config
```

This will generate attack traffic that the RL agent can detect and respond to!

#### Step 6: View Results

```powershell
# View logs
docker logs cowrie_honeypot_local
docker logs nginx_honeypot_local

# View training results
type results\local_timesteps.csv
type results\local_episodes.csv

# View saved models
dir models\
```

#### Step 7: Stop Honeypots When Done

```powershell
docker-compose -f docker-compose.local.yml down
```

### Option 2: Fix AWS Production Version (Advanced)

If you want to run the AWS version later, you need to:

1. **Deploy to AWS EC2**:
   ```powershell
   cd infra
   terraform init
   terraform apply
   ```

2. **Update main.py** with your EC2 IP address

3. **Run**: `python main.py`

But for now, **use Option 1** to test locally!

## Common Errors and Fixes

### Error: "Docker not found"

```
Solution: Install Docker Desktop for Windows
https://www.docker.com/products/docker-desktop
```

### Error: "Cannot connect to Docker daemon"

```
Solution: Start Docker Desktop application
```

### Error: "Port 2222 already in use"

```powershell
# Find what's using the port
netstat -ano | findstr :2222

# Stop the process or change port in docker-compose.local.yml
```

### Error: "Containers not starting"

```powershell
# Check Docker logs
docker-compose -f docker-compose.local.yml logs

# Restart containers
docker-compose -f docker-compose.local.yml restart

# Remove and recreate
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

### Error: "SSH connection refused"

```
Wait 30-60 seconds for Cowrie to fully start, then try again.

Check container status:
docker-compose -f docker-compose.local.yml ps

Check logs:
docker logs cowrie_honeypot_local
```

## Key Differences: main.py vs main_local.py

| Feature | main.py (AWS) | main_local.py (Local) |
|---------|---------------|----------------------|
| **Target** | EC2 instance | localhost |
| **Deployment** | SSH to EC2 | Docker Compose |
| **Honeypot Ports** | 2222, 80 | 2222, 8080 |
| **State Detection** | EC2 log files | Docker logs |
| **Metrics** | CloudWatch | CSV files |
| **Cost** | ~$40/month | Free |
| **Use Case** | Production research | Development/testing |

## Next Steps

1. **✅ Complete local testing** using `main_local.py`
2. **📊 Analyze results** in `results/` directory
3. **📈 Tune hyperparameters** if needed
4. **☁️ Deploy to AWS** when ready for production using `main.py`

## Quick Reference Commands

```powershell
# Start everything
bash scripts/setup_local_test.sh
docker-compose -f docker-compose.local.yml up -d
python main_local.py --episodes 10

# Test manually
ssh -p 2222 root@localhost
curl http://localhost:8080/.env

# View logs
docker logs -f cowrie_honeypot_local
docker logs -f nginx_honeypot_local

# Stop everything
docker-compose -f docker-compose.local.yml down
```

## Getting Help

If you still have issues:

1. Check **LOCAL_TESTING.md** for detailed guide
2. Check **PRODUCTION_QUICK_START.md** for AWS deployment
3. Check Docker Desktop is running
4. Check firewall isn't blocking ports 2222 and 8080

## What You Should See When It Works

```
DeceptiCloud: Local Docker Testing Mode
============================================================
Episodes: 5
Timesteps per episode: 24
Target: localhost
============================================================
✓ Docker found: Docker version 24.0.6

Initializing environment and agent...
[Environment] Local Docker environment initialized
[Environment] Target: localhost
[Environment] State size: 3, Action size: 3

Starting Training
============================================================

Episode 1/5, Timestep 1/24
[Action] Deploying Cowrie SSH honeypot...
[Action] ✓ Cowrie honeypot deployed
[Detection] SSH attack detected in Cowrie logs
[Reward] +10: SSH attack captured by Cowrie!

Episode 1/5, Timestep 2/24
...
```

Good luck! 🚀
