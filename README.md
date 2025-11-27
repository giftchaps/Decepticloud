# DeceptiCloud

An Autonomous RL Framework for Adaptive Cloud Honeynets.

This repository contains the DeceptiCloud project: an experimental system that uses a Deep Q-Network (DQN) agent to dynamically manage cloud-based honeypots (SSH Cowrie and Web nginx) in response to detected attacker behavior in real-time.

---

## 🚀 Quick Start - LOCAL TESTING FIRST!

**Before deploying to AWS, test everything locally with Docker (FREE, no AWS costs).**

### One-Command Testing

**Windows PowerShell:**
```powershell
.\scripts\test_complete_local.ps1
```

**Linux/Mac:**
```bash
bash scripts/test_complete_local.sh
```

**That's it!** This will:
- ✅ Setup environment
- ✅ Start honeypots in Docker
- ✅ Test connectivity
- ✅ Generate attack traffic
- ✅ Run RL agent
- ✅ Show results

### Manual Testing (If Automated Fails)

```bash
# 1. Setup
bash scripts/setup_local_test.sh

# 2. Start honeypots
docker-compose -f docker-compose.local.yml up -d

# 3. Test honeypots
ssh -p 2222 root@localhost          # password: password
curl http://localhost:8080/.env     # See honeytokens

# 4. Train RL agent
python main_local.py --episodes 10

# 5. Simulate attacks (in another terminal)
python scripts/simulate_attacks.py --duration 300

# 6. View results
cat results/local_episodes.csv
```

---

## 📚 Documentation Structure

### For Local Testing (START HERE!)

1. **[TESTING_QUICK_REFERENCE.md](TESTING_QUICK_REFERENCE.md)** - Essential commands at a glance
2. **[COMPLETE_TESTING_GUIDE.md](COMPLETE_TESTING_GUIDE.md)** - Full step-by-step guide with troubleshooting
3. **[WINDOWS_QUICKSTART.md](WINDOWS_QUICKSTART.md)** - Windows-specific guide

### For AWS Deployment (AFTER local testing succeeds)

4. **[docs/aws/PRODUCTION_QUICK_START.md](docs/aws/PRODUCTION_QUICK_START.md)** - AWS deployment quick start
5. **[docs/aws/PRODUCTION_DEPLOYMENT.md](docs/aws/PRODUCTION_DEPLOYMENT.md)** - Detailed AWS production guide

### Advanced Features (Optional)

6. **[docs/advanced/ANTI_DETECTION.md](docs/advanced/ANTI_DETECTION.md)** - Honeypot hardening techniques
7. **[docs/advanced/ATTACK_FRAMEWORKS.md](docs/advanced/ATTACK_FRAMEWORKS.md)** - Industry-standard attack integration

---

## 🎯 Recommended Workflow

### Phase 1: Local Testing (This Week)

1. Run automated test: `bash scripts/test_complete_local.sh`
2. If successful, do full training with attacks
3. Analyze results
4. Validate everything works

### Phase 2: AWS Deployment (Next Week)

1. Read `docs/aws/PRODUCTION_QUICK_START.md`
2. Deploy infrastructure with Terraform
3. Run production experiments
4. Collect data for research

### Phase 3: Research & Documentation (Final)

1. Gather results from AWS experiments
2. Analyze RL vs static honeypots
3. Document findings
4. Write research paper

---

## 📊 Key Features

**Local Testing:**
- ✅ Docker-based honeypots (SSH + Web)
- ✅ Automated testing scripts
- ✅ Attack traffic simulation
- ✅ RL agent training (main_local.py)
- ✅ Results in CSV files
- ✅ No AWS costs

**Production Deployment:**
- ✅ Terraform infrastructure as code
- ✅ VPC isolation and security
- ✅ CloudWatch monitoring
- ✅ CloudTrail honeytoken tracking
- ✅ Automated cost controls
- ✅ SNS alerting

**Advanced Features:**
- ✅ Anti-detection measures
- ✅ Realistic attack frameworks (Stratus Red Team, CALDERA)
- ✅ MITRE ATT&CK mapping
- ✅ Dwell time tracking
- ✅ Traffic normalization

---

## 🛠️ Prerequisites

### For Local Testing

- **Docker Desktop** (Windows/Mac) or docker.io (Linux)
- **Python 3.8+**
- **pip** (Python package manager)

### For AWS Deployment (Later)

- **AWS Account**
- **Terraform**
- **AWS CLI configured**

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
DeceptiCloud/
├── 📄 README.md                           ← YOU ARE HERE
├── 📄 TESTING_QUICK_REFERENCE.md          ← Essential commands
├── 📄 COMPLETE_TESTING_GUIDE.md           ← Full testing guide
├── 📄 WINDOWS_QUICKSTART.md               ← Windows guide
│
├── 🐍 main_local.py                       ← LOCAL: RL agent
├── 🐍 main.py                             ← AWS: RL agent
├── 🐳 docker-compose.local.yml            ← LOCAL: Honeypots
│
├── 📁 scripts/                            ← Testing scripts
│   ├── test_complete_local.sh             ← Automated test (Linux/Mac)
│   ├── test_complete_local.ps1            ← Automated test (Windows)
│   ├── test_local_honeypots.py            ← Validation tests
│   ├── simulate_attacks.py                ← Attack generator
│   ├── setup_local_test.sh                ← Environment setup
│   └── cost_control.py                    ← AWS cost management
│
├── 📁 src/                                ← Core code
│   ├── agent.py                           ← DQN agent
│   ├── environment.py                     ← Honeypot environment
│   ├── attacker.py                        ← Attack simulation
│   └── ...
│
├── 📁 docs/
│   ├── 📁 aws/                            ← AWS deployment
│   │   ├── PRODUCTION_QUICK_START.md
│   │   └── PRODUCTION_DEPLOYMENT.md
│   └── 📁 advanced/                       ← Advanced features
│       ├── ANTI_DETECTION.md
│       └── ATTACK_FRAMEWORKS.md
│
├── 📁 infra/                              ← AWS Terraform
│   └── main.tf
│
├── 📁 notebooks/                          ← Analysis
│   └── 01_data_analysis.ipynb
│
└── 📁 config/                             ← Configuration
    └── attack_scenarios.yaml
```

---

## 🔬 What This Project Does

### Problem

Traditional static honeypots are:
- ❌ Resource inefficient (run all the time)
- ❌ Easy to fingerprint
- ❌ Don't adapt to attack patterns

### Solution

DeceptiCloud uses **Reinforcement Learning** to:
- ✅ Deploy honeypots **only when needed**
- ✅ Match honeypot type to detected attacks (SSH vs Web)
- ✅ Learn optimal deployment strategy
- ✅ Maximize attacker engagement

### Research Question

**"Are RL-based adaptive honeynets more effective than static honeynets?"**

You'll measure:
- Resource efficiency (cost savings)
- Attack capture rate
- Attacker dwell time
- Detection avoidance

---

## 📈 How the RL Agent Works

### State (What the agent sees)

```
[ssh_attack_detected, web_attack_detected, current_honeypot]
Example: [1, 0, 1] = SSH attack detected, Cowrie honeypot deployed
```

### Actions (What the agent can do)

- **Action 0:** Do nothing / Stop all honeypots
- **Action 1:** Deploy Cowrie SSH honeypot (port 2222)
- **Action 2:** Deploy nginx web honeypot (port 80)

### Rewards (What the agent learns from)

- **+10:** Attack type matches deployed honeypot ✅
- **-1:** Honeypot running but no matching traffic (waste)
- **-2:** Attack occurs but wrong/no honeypot deployed (missed)

### Learning

The DQN agent learns to:
1. Deploy SSH honeypot when SSH attacks detected
2. Deploy web honeypot when web attacks detected
3. Stop honeypots when no attacks (save resources)
4. Maximize total reward over time

---

## 🧪 Testing Scenarios

### Local Testing (Free, Fast)

```bash
# Train agent with simulated attacks
python main_local.py --episodes 20
```

**What you'll see:**
- Agent starts random (epsilon=1.0)
- Learns from experience
- Deploys correct honeypots
- Gets positive rewards

### AWS Production (Real Data)

```bash
# Deploy to AWS, expose to internet, collect real attacks
terraform apply
python main.py --episodes 100
```

**What you'll measure:**
- Real attacker behavior
- Resource costs
- Dwell time metrics
- Comparison with static baseline

---

## 📊 Expected Results

After local testing, you should see:

**Episode 1:** Total Reward = -14 (random actions)
**Episode 10:** Total Reward = +8 (starting to learn)
**Episode 20:** Total Reward = +25 (learned optimal policy)

**Files generated:**
- `results/local_episodes.csv` - Episode summaries
- `results/local_timesteps.csv` - Detailed logs
- `models/local_dqn_episode_*.pth` - Saved models

---

## 🐛 Troubleshooting

### "Docker not found"

**Install Docker Desktop:**
- Windows/Mac: https://www.docker.com/products/docker-desktop
- Linux: `sudo apt-get install docker.io docker-compose`

### "Containers won't start"

```bash
docker-compose -f docker-compose.local.yml restart
```

### "No attacks detected"

Make sure to run attack simulator while training:

```bash
# Terminal 1
python main_local.py --episodes 10

# Terminal 2
python scripts/simulate_attacks.py --continuous
```

### More Help

See **[COMPLETE_TESTING_GUIDE.md](COMPLETE_TESTING_GUIDE.md)** - Section "Troubleshooting" for detailed solutions.

---

## 🎓 Research Paper Support

This project is designed to support your research on RL-based adaptive honeynets.

### Data You'll Collect

**From Local Testing:**
- RL agent learning curves
- Action distributions
- Reward statistics
- Validation that system works

**From AWS Production:**
- Real attack data (10,000+ attempts expected)
- Resource utilization (EC2 costs)
- Dwell time metrics
- Static vs RL comparison

### Analysis Tools

**Jupyter Notebooks:**
```bash
jupyter notebook notebooks/01_data_analysis.ipynb
```

**Statistical Tests:**
- t-test (RL vs static rewards)
- Mann-Whitney U (non-parametric)
- Effect size (Cohen's d)

### Research Workflow

1. **Week 1-2:** Local testing, validate system
2. **Week 3-4:** AWS deployment, data collection
3. **Week 5-6:** Analysis, visualization
4. **Week 7-8:** Write findings, document

---

## 🤝 Contributing

This is a research project. If you use it:
1. Test locally first
2. Document any issues
3. Share your findings
4. Cite appropriately

---

## 📄 License

See LICENSE file.

---

## 🆘 Getting Help

1. **Quick commands:** [TESTING_QUICK_REFERENCE.md](TESTING_QUICK_REFERENCE.md)
2. **Full guide:** [COMPLETE_TESTING_GUIDE.md](COMPLETE_TESTING_GUIDE.md)
3. **Windows users:** [WINDOWS_QUICKSTART.md](WINDOWS_QUICKSTART.md)
4. **AWS deployment:** [docs/aws/PRODUCTION_QUICK_START.md](docs/aws/PRODUCTION_QUICK_START.md)

---

## ✅ Success Checklist

- [ ] Docker installed and running
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Automated test passes (`bash scripts/test_complete_local.sh`)
- [ ] Can connect to SSH honeypot (`ssh -p 2222 root@localhost`)
- [ ] Can see honeytokens (`curl http://localhost:8080/.env`)
- [ ] RL agent shows positive rewards (+10)
- [ ] Results saved to `results/local_episodes.csv`

**If all ✅, you're ready for AWS deployment!**

---

**🚀 Ready to start? Run:** `bash scripts/test_complete_local.sh`
