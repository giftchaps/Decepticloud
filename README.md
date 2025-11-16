# DeceptiCloud

An Autonomous RL Framework for Adaptive Cloud Honeynets.

This repository contains the DeceptiCloud project: an experimental system that uses a Deep Q-Network (DQN) agent to dynamically manage cloud-based honeypots (SSH Cowrie and Web nginx) in response to detected attacker behavior in real-time.

## Key Features

- **Dual Honeypot Support**: Deploys both SSH (Cowrie) and Web (nginx) honeypots
- **Multi-Attack Detection**: Monitors and responds to both SSH brute-force and web attacks
- **Advanced Reward Function**: Incentivizes matching honeypot types to attack patterns
- **Model Persistence**: Save and load trained DQN models
- **Comprehensive Analysis**: Jupyter notebook with statistical tests and visualizations
- **Baseline Comparison**: Static experiment script for control group analysis
- **Realistic Attack Simulation**: Integration with industry-standard attack frameworks (Stratus Red Team, CALDERA, Pacu)
- **MITRE ATT&CK Mapping**: Attack scenarios mapped to adversary tactics and techniques
- **Configurable Scenarios**: 6 predefined attack scenarios from stealthy to aggressive

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

## Core Components

- `src/agent.py` — DQN Agent with model save/load functionality
- `src/environment.py` — Cloud environment supporting dual honeypot deployment and multi-attack detection
- `src/attacker.py` — Dual attacker simulation (SSH brute-force + web probing)
- `src/aws_utils.py` — AWS utilities for SSM and S3 integration
- `src/cloud_control.py` — SSM-based command execution
- `infra/main.tf` — Terraform infrastructure as code
- `notebooks/01_data_analysis.ipynb` — Complete analysis with statistical tests
- `scripts/run_static_experiment.py` — Baseline static honeypot experiment

## PowerShell Scripts

- `scripts/setup_infrastructure.ps1` — Complete infrastructure deployment
- `scripts/terraform_init.ps1` — Initialize Terraform
- `scripts/terraform_apply.ps1` — Deploy/plan infrastructure
- `scripts/terraform_destroy.ps1` — Clean up resources
- `scripts/run_experiment.ps1` — Run DeceptiCloud experiment
- `scripts/run_smoke_check.ps1` — Quick validation test

See `scripts/README.md` for detailed usage.

## Running Experiments

### Basic Experiments (Simple Attacks)

**Adaptive (DQN) Experiment:**
```bash
python main.py
```

**Static Baseline Experiments:**
```bash
# SSH-only baseline
python scripts/run_static_experiment.py --honeypot ssh --episodes 5

# Web-only baseline
python scripts/run_static_experiment.py --honeypot web --episodes 5

# No honeypot baseline
python scripts/run_static_experiment.py --honeypot none --episodes 5
```

### Realistic Experiments (Industry-Standard Attack Frameworks) ⭐

**Recommended for research validation:**

```bash
# Set environment variables
export EC2_HOST="your-ec2-ip"
export EC2_KEY_FILE="/path/to/key.pem"

# Adaptive RL with mixed attack scenario (4 hours)
python scripts/run_realistic_experiment.py --scenario mixed --duration 4

# Static SSH baseline with same attacks
python scripts/run_realistic_experiment.py --mode static --honeypot ssh --scenario mixed --duration 4

# Static web baseline
python scripts/run_realistic_experiment.py --mode static --honeypot web --scenario mixed --duration 4

# Cloud-native attacks (AWS-specific exploitation)
python scripts/run_realistic_experiment.py --scenario cloud_native --duration 6

# Aggressive multi-vector attack (stress test)
python scripts/run_realistic_experiment.py --scenario aggressive --duration 2

# Stealthy long-duration campaign (24 hours)
python scripts/run_realistic_experiment.py --scenario stealthy --duration 24
```

**Available Attack Scenarios:**
- `ssh_focused` - SSH brute-force and lateral movement
- `web_focused` - Web reconnaissance and API enumeration
- `mixed` - Multi-vector realistic adversary (recommended)
- `cloud_native` - AWS-specific exploitation (IAM, S3, EC2)
- `aggressive` - High-intensity attack for stress testing
- `stealthy` - Low and slow long-duration campaign

See `docs/ATTACK_FRAMEWORKS.md` for detailed information about attack frameworks and `config/attack_scenarios.yaml` for configuration.

**Analysis:**
```bash
jupyter notebook notebooks/01_data_analysis.ipynb
```

The analysis notebook includes:
- Reward trajectory visualization
- Action distribution analysis
- Attack detection statistics
- Statistical comparison (t-test, Mann-Whitney U)
- Effect size calculation

## State Representation

The agent observes a 3-dimensional state:
- `[0]` SSH attack detected (0/1)
- `[1]` Web attack detected (0/1)
- `[2]` Current honeypot deployed (0=None, 1=Cowrie, 2=Nginx)

## Action Space

- `0` - Do nothing / Stop all honeypots
- `1` - Deploy Cowrie SSH honeypot (port 2222)
- `2` - Deploy nginx web honeypot (port 80)

## Reward Function

- **+10** when attack type matches deployed honeypot
- **-1** when honeypot runs without matching traffic (resource waste)
- **-2** when attack occurs but no honeypot is deployed (missed opportunity)

See `GUIDE.md` for the full recommended workflow.