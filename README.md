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
- `src/agent.py` — DQNAgent implementation.
- `src/environment.py` — CloudHoneynetEnv that connects to an EC2 instance via SSH and controls Docker honeypots.
- `src/attacker.py` — simple scripted attacker that generates SSH login attempts.
- `infra/main.tf` — Terraform script to create an EC2 instance and security group for the lab.
- `notebooks/01_data_analysis.ipynb` — notebook for plotting results.

## PowerShell Scripts

- `scripts/setup_infrastructure.ps1` — Complete infrastructure deployment
- `scripts/terraform_init.ps1` — Initialize Terraform
- `scripts/terraform_apply.ps1` — Deploy/plan infrastructure
- `scripts/terraform_destroy.ps1` — Clean up resources
- `scripts/run_experiment.ps1` — Run DeceptiCloud experiment
- `scripts/run_smoke_check.ps1` — Quick validation test

See `scripts/README.md` for detailed usage.

See `GUIDE.md` for the full recommended workflow.