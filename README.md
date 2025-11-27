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
- **Anti-Detection Measures**: Honeypot hardening to maximize dwell time and avoid fingerprinting
- **Dwell Time Tracking**: Measure how long attackers engage before detecting deception
- **Traffic Normalization**: Background activity simulation for realistic appearance
- **Honeytokens**: Fake credentials and data to attract and track attackers

## Local Testing First (Recommended) 🔧

**Test honeypots locally with Docker before deploying to AWS** - no costs, instant feedback, easy debugging!

```bash
# 1. Setup (creates directories and content)
bash scripts/setup_local_test.sh

# 2. Start honeypots
docker-compose -f docker-compose.local.yml up -d

# 3. Test
python scripts/test_local_honeypots.py

# 4. Access honeypots
ssh -p 2222 root@localhost          # SSH honeypot (password: password)
curl http://localhost:8080/.env     # Web honeypot with honeytokens
```

### Automated Testing (Recommended!)

**Windows PowerShell:**
```powershell
# One command to test everything
.\scripts\test_complete_local.ps1
```

**Linux/Mac:**
```bash
# One command to test everything
bash scripts/test_complete_local.sh
```

**This will automatically:**
- ✅ Setup environment
- ✅ Start honeypots
- ✅ Test connectivity
- ✅ Generate attack traffic
- ✅ Run RL agent
- ✅ Show results

**See [COMPLETE_TESTING_GUIDE.md](COMPLETE_TESTING_GUIDE.md) for step-by-step manual testing.**

**See [LOCAL_TESTING.md](LOCAL_TESTING.md) for detailed documentation.**

**See [WINDOWS_QUICKSTART.md](WINDOWS_QUICKSTART.md) for Windows-specific guide.**

## Quick Start (AWS Deployment)

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

## Anti-Detection & Dwell Time Maximization

DeceptiCloud includes comprehensive anti-detection measures to make honeypots indistinguishable from real systems, maximizing attacker dwell time.

### Deploy Anti-Detection Measures

```bash
# Generate realistic honeypot content
bash scripts/deploy_anti_detection.sh

# This creates:
# - Realistic Cowrie filesystem with fake credentials
# - Realistic process lists
# - Web content with honeytokens (.env, .aws/credentials, etc.)
# - Deployment instructions
```

### Start Traffic Normalizer

```bash
# Generate realistic background traffic (masks honeypot nature)
python src/traffic_normalizer.py <EC2-IP> &
```

### Track Dwell Time

Dwell time metrics are automatically tracked and included in results:
- Average session duration
- Commands executed before detection
- Engagement score (0-100)
- Detection rate

See `docs/ANTI_DETECTION.md` for complete documentation on:
- Honeypot fingerprinting prevention
- Realistic filesystem configuration
- Honeytoken deployment
- Traffic normalization strategies
- Dwell time optimization

### Key Metrics

- **Dwell Time**: How long attackers interact before leaving (target: >15 min)
- **Detection Rate**: Percentage of attackers who identify honeypot (target: <10%)
- **Engagement Score**: Quality of interaction (0-100, target: >70)
- **Honeytoken Usage**: Attackers attempting to use fake credentials (target: >20%)

See `GUIDE.md` for the full recommended workflow.

## Production Deployment 🚀

DeceptiCloud is production-ready with full AWS infrastructure automation, monitoring, and cost controls.

### Quick Start (20 minutes)

```bash
# 1. Configure AWS and create key pair
aws configure
aws ec2 create-key-pair --key-name decepticloud-key \
  --query 'KeyMaterial' --output text > ~/.ssh/decepticloud-key.pem
chmod 400 ~/.ssh/decepticloud-key.pem

# 2. Deploy infrastructure
cd infra
terraform init
terraform apply -auto-approve

# 3. Test deployment
PUBLIC_IP=$(terraform output -raw public_ip)
cd ..
python scripts/test_production_deployment.py $PUBLIC_IP \
  --ssh-key ~/.ssh/decepticloud-key.pem

# 4. Set up monitoring
SNS_TOPIC=$(cd infra && terraform output -raw honeytoken_alerts_topic)
aws sns subscribe --topic-arn $SNS_TOPIC \
  --protocol email --notification-endpoint your-email@example.com
```

**See [PRODUCTION_QUICK_START.md](PRODUCTION_QUICK_START.md) for complete quick start guide.**

### Production Features

✅ **VPC Isolation** - Dedicated VPC with public/private subnets
✅ **Container Orchestration** - Docker Compose with health checks
✅ **Network Monitoring** - VPC Flow Logs for all traffic
✅ **Honeytoken Monitoring** - CloudTrail alerts on fake credential usage
✅ **Cost Controls** - Billing alarms and automated cleanup
✅ **Automated Deployment** - EC2 user_data bootstraps honeypots
✅ **Log Aggregation** - CloudWatch Logs with retention policies
✅ **SNS Alerting** - Real-time notifications for security events

### Infrastructure Components

**Compute:**
- EC2 instance (t2.medium recommended, ~$35/month)
- Cowrie SSH honeypot (Docker container, port 2222)
- nginx web honeypot (Docker container, port 80)

**Networking:**
- VPC with 10.0.0.0/16 CIDR
- Public subnet for honeypot exposure
- Private subnet for management (future)
- Internet Gateway for public access
- Security groups (SSH 2222, HTTP 80)

**Monitoring:**
- VPC Flow Logs (CloudWatch, 7-day retention)
- CloudTrail (S3 + CloudWatch, 30-day retention)
- CloudWatch metric filters for honeytoken usage
- SNS topics for alerts

**Storage:**
- S3 bucket for CloudTrail logs
- S3 bucket for experiment results (optional)
- EBS volumes for Docker persistence

**Expected Monthly Cost:** ~$40
- EC2 t2.medium: $35
- S3 storage: $1
- CloudWatch logs: $2
- CloudTrail: $2

**Cost Reduction:**
- Use t2.small (~$17/month)
- Stop instance when not testing (~$2/month for storage only)
- Reduce log retention to 7 days

### Testing Production Deployment

```bash
# Automated testing (validates all components)
python scripts/test_production_deployment.py $PUBLIC_IP \
  --ssh-key ~/.ssh/decepticloud-key.pem

# Manual testing
ssh -p 2222 root@$PUBLIC_IP  # Test SSH honeypot (password: password)
curl http://$PUBLIC_IP/      # Test web honeypot
curl http://$PUBLIC_IP/.env  # Test honeytoken exposure

# Run realistic attack simulation
python scripts/run_realistic_experiment.py \
  --scenario mixed --target $PUBLIC_IP --duration 300
```

### Monitoring Production Honeypots

**View Real-Time Logs:**
```bash
# VPC Flow Logs
aws logs tail /aws/vpc/decepticloud-flow-logs --follow

# Cowrie SSH logs
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP
docker logs -f cowrie_honeypot

# nginx web logs
docker logs -f nginx_honeypot
```

**Honeytoken Alerts:**
When attackers use fake AWS credentials from honeypots, you'll receive email alerts via SNS.

Fake credentials are in:
- `/home/ubuntu/.aws/credentials` (SSH honeypot)
- `/.env` (web honeypot)
- `/opt/app/config.json` (SSH honeypot)

**Cost Monitoring:**
```bash
python scripts/cost_control.py monitor-costs
```

### Production Documentation

📖 **[PRODUCTION_QUICK_START.md](PRODUCTION_QUICK_START.md)** - 20-minute quick start guide
📖 **[docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)** - Complete production guide with:
- Prerequisites and AWS setup
- Terraform infrastructure walkthrough
- Honeytoken monitoring configuration
- Cost control and billing alarms
- Testing and validation procedures
- Security considerations
- Troubleshooting guide
- Cleanup and teardown

### Production Architecture

```
┌─────────────────────────────────────────┐
│              AWS VPC                    │
│  ┌───────────────────────────────────┐  │
│  │      EC2 Instance (Ubuntu 22.04)  │  │
│  │  ┌──────────┐   ┌──────────┐     │  │
│  │  │ Cowrie   │   │  nginx   │     │  │
│  │  │SSH :2222 │   │Web :80   │     │  │
│  │  └──────────┘   └──────────┘     │  │
│  │         Docker + Health Checks    │  │
│  └───────────────────────────────────┘  │
│              ↓                          │
│      VPC Flow Logs                      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         CloudWatch + CloudTrail         │
│  - Network traffic logs                 │
│  - Honeytoken usage detection           │
│  - Billing alarms                       │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│           SNS Alerts → Email            │
└─────────────────────────────────────────┘
```

### Cleanup

**Stop instance (preserve data):**
```bash
INSTANCE_ID=$(cd infra && terraform output -raw instance_id)
aws ec2 stop-instances --instance-ids $INSTANCE_ID
# Cost: ~$2/month (EBS storage only)
```

**Destroy everything:**
```bash
cd infra
terraform destroy -auto-approve
# Cost: $0
```