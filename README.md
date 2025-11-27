# DeceptiCloud

An Autonomous RL Framework for Adaptive Cloud Honeynets.

This repository contains the DeceptiCloud project: an experimental system that uses a Deep Q-Network (DQN) agent to manage a cloud-based honeynet (deploying either an SSH honeypot or a web honeypot) in response to detected attacker behavior.

## Quick Start

**Automated Setup (Recommended):**
```powershell
# 1. Deploy infrastructure
.\scripts\setup_infrastructure.ps1 -KeyName "your-ec2-key"

# 2. Run experiment (use public_ip from step 1)
.\scripts\run_experiment.ps1 -EC2Host "<public_ip>" -KeyFile "path\to\key.pem"
```

**Manual Setup:**
- Create AWS resources: `terraform init && terraform apply` in `infra/`
- Edit `main.py` and set `EC2_HOST`, `EC2_USER`, and `EC2_KEY_FILE`
- Install deps: `pip install -r requirements.txt`
- Run: `python main.py`

Detailed step-by-step setup, experiment protocol, data collection guidance, tuning tips, and reproducibility checklist are in `GUIDE.md` (recommended read before running experiments).

Files:
- `src/agent.py` — DQNAgent with CloudWatch learning metrics
- `src/environment.py` — CloudHoneynetEnv with real attack detection and reward tracking
- `src/adversarial_attacker.py` — RL-based adversarial attacker
- `src/monitoring.py` — CloudWatch integration and dashboard generation
- `src/cost_tracker.py` — AWS cost analysis for economic research
- `infra/main.tf` — Terraform script for EC2 and security groups
- `notebooks/01_data_analysis.ipynb` — Research data analysis and visualization

## PowerShell Scripts

**Infrastructure:**
- `scripts/setup_infrastructure.ps1` — Complete infrastructure deployment
- `scripts/terraform_init.ps1` — Initialize Terraform
- `scripts/terraform_apply.ps1` — Deploy/plan infrastructure
- `scripts/terraform_destroy.ps1` — Clean up resources

**Experiments:**
- `scripts/run_experiment.ps1` — Run DeceptiCloud experiment
- `scripts/run_smoke_check.ps1` — Quick validation test
- `scripts/docker_manage.ps1` — Docker honeypot management

**Monitoring:**
- `scripts/setup_cloudwatch.ps1` — Configure CloudWatch monitoring
- `scripts/monitor_system.ps1` — Real-time monitoring and dashboards
- `scripts/attack_simulator.ps1` — Test attack detection

See `scripts/README.md` for detailed usage.

## Docker Honeypots

Local testing with Docker containers:
```powershell
# Build and start honeypots
.\scripts\docker_manage.ps1 -Action build
.\scripts\docker_manage.ps1 -Action start

# Test endpoints
# SSH: localhost:2222
# Web: http://localhost

# View logs
.\scripts\docker_manage.ps1 -Action logs

# Stop containers
.\scripts\docker_manage.ps1 -Action stop
```

See `GUIDE.md` for the full recommended workflow.

## Monitoring & Visualization

View real-time attacks, rewards, and learning progress:

```powershell
# Setup CloudWatch monitoring
.\scripts\setup_cloudwatch.ps1

# View real-time dashboard
.\scripts\monitor_system.ps1 -EC2Host "<public_ip>" -KeyFile "<key.pem>" -Action dashboard

# Monitor live honeypot logs
.\scripts\monitor_system.ps1 -EC2Host "<public_ip>" -KeyFile "<key.pem>" -Action live-logs

# Test attack detection
.\scripts\attack_simulator.ps1 -TargetHost "<public_ip>" -AttackType ssh -Duration 120

# View CloudWatch console
.\scripts\monitor_system.ps1 -EC2Host "<public_ip>" -KeyFile "<key.pem>" -Action cloudwatch
```

**What you can see:**
- Real-time attack detection with attacker IPs
- RL agent learning progress (epsilon decay, Q-values, loss)
- Reward system in action
- Honeypot deployment decisions
- Attack patterns and honeypot effectiveness
- CloudWatch metrics and alarms

**Testing autonomous behavior:**
- Run attack simulator from different machines/IPs
- Watch agent adapt honeypot deployment
- Monitor reward changes based on attack patterns
- Verify learning through epsilon decay and Q-value evolution