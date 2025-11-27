# DeceptiCloud Testing - Quick Reference Card

## 🚀 Fastest Way to Test (Recommended)

### Windows PowerShell
```powershell
.\scripts\test_complete_local.ps1
```

### Linux/Mac
```bash
bash scripts/test_complete_local.sh
```

**That's it!** The script does everything automatically.

---

## 📋 Manual Testing Commands

### 1. Setup
```bash
bash scripts/setup_local_test.sh
```

### 2. Start Honeypots
```bash
docker-compose -f docker-compose.local.yml up -d
```

### 3. Test Connectivity
```bash
# SSH honeypot
ssh -p 2222 root@localhost  # password: password

# Web honeypot
curl http://localhost:8080/.env
```

### 4. Run Automated Tests
```bash
python scripts/test_local_honeypots.py
```

### 5. Train RL Agent
```bash
python main_local.py --episodes 10
```

### 6. Simulate Attacks (While Training!)
```bash
# In another terminal
python scripts/simulate_attacks.py --duration 300 --intensity medium
```

### 7. View Results
```bash
cat results/local_episodes.csv
docker logs cowrie_honeypot_local
docker logs nginx_honeypot_local
```

### 8. Stop Honeypots
```bash
docker-compose -f docker-compose.local.yml down
```

---

## 🎯 Training with Attack Simulation (Recommended Workflow)

**Terminal 1 - Training:**
```bash
python main_local.py --episodes 20 --timesteps 24
```

**Terminal 2 - Attacks:**
```bash
python scripts/simulate_attacks.py --continuous --intensity medium
```

Press Ctrl+C in Terminal 2 when training completes.

---

## 🔍 Quick Health Check

```bash
# Are containers running?
docker ps

# Are ports open?
# Windows: Test-NetConnection localhost -Port 2222
# Linux/Mac: nc -zv localhost 2222

# View recent logs
docker logs --tail 20 cowrie_honeypot_local
docker logs --tail 20 nginx_honeypot_local
```

---

## 🛠️ Troubleshooting Quick Fixes

### Containers won't start
```bash
docker-compose -f docker-compose.local.yml restart
```

### Clean restart
```bash
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d
```

### View errors
```bash
docker-compose -f docker-compose.local.yml logs
```

---

## 📊 Attack Simulation Options

```bash
# Low intensity (gentle testing)
python scripts/simulate_attacks.py --intensity low --duration 300

# Medium intensity (default, recommended)
python scripts/simulate_attacks.py --intensity medium --duration 300

# High intensity (stress testing)
python scripts/simulate_attacks.py --intensity high --duration 600

# Continuous (run until stopped)
python scripts/simulate_attacks.py --continuous
```

---

## 📁 Important File Locations

| What | Where |
|------|-------|
| Training results | `results/local_episodes.csv` |
| Timestep details | `results/local_timesteps.csv` |
| Cowrie logs | `data/cowrie/logs/cowrie.json` |
| nginx logs | `data/nginx/logs/access.log` |
| Saved models | `models/local_dqn_episode_*.pth` |
| Test results | `local_test_results_*.json` |

---

## 🔌 Ports

- **2222** - SSH honeypot (Cowrie)
- **8080** - Web honeypot (nginx)

---

## 📚 Documentation

- **COMPLETE_TESTING_GUIDE.md** - Full step-by-step guide
- **LOCAL_TESTING.md** - Detailed local testing documentation
- **WINDOWS_QUICKSTART.md** - Windows-specific quick start
- **PRODUCTION_QUICK_START.md** - AWS deployment guide

---

## ✅ Success Indicators

**You'll know it's working when you see:**

1. **Containers healthy:**
   ```
   docker ps
   # Shows: Up (healthy) for both containers
   ```

2. **Positive rewards during training:**
   ```
   [Reward] +10: SSH attack captured by Cowrie!
   [Reward] +10: Web attack captured by nginx!
   ```

3. **Attacks in logs:**
   ```bash
   docker logs cowrie_honeypot_local | grep -i "login"
   # Shows: Multiple login attempts
   ```

---

## 🎓 Learning Path

1. **First Time:** Run automated test → Read COMPLETE_TESTING_GUIDE.md
2. **Second Time:** Manual testing → Understand each component
3. **Third Time:** Full training with attack simulation
4. **Ready:** Deploy to AWS (PRODUCTION_QUICK_START.md)

---

**Need Help?** Check COMPLETE_TESTING_GUIDE.md for detailed troubleshooting!
