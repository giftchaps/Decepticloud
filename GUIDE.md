DeceptiCloud — Setup & Experiment Guide

Purpose
- This document contains a step-by-step setup, run, and experiment protocol for the DeceptiCloud project. It also lists practical requirements, reproducibility notes, data collection guidelines, tuning tips, and recommended next steps to meet the research objectives.

Important safety note
- This project touches live cloud infrastructure and network services. Never expose sensitive credentials. Use a disposable AWS account or strict IAM/Networking rules during experiments. Do not run live attack tools outside an isolated lab you control.

Prerequisites (local)
- OS: Windows, macOS, or Linux (PowerShell examples are provided for Windows).
- Python 3.8+ (virtualenv recommended).
- Terraform (for infra automation) installed and configured with AWS credentials.
- AWS account with permission to create EC2 instances, security groups, and keypairs.
- An SSH keypair (.pem) available in AWS; keep local copy for SSH.

Python dependencies (install locally)
- From the repository root run (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
```

(If on macOS/Linux replace activate commands accordingly.)

AWS / Terraform setup
1. Open `infra/main.tf` and set `key_name` to the name of your AWS keypair (created in the AWS console or via `aws ec2 create-key-pair`).
2. Optionally change `region` and `ami` to match your account/region.
3. From `c:\Users\gift2\OneDrive\Desktop\Research\Decepticloud\infra` run:

```powershell
terraform init
terraform apply
```

4. After `apply` completes, note the EC2 public IP (or use the Terraform output `public_ip`).
5. Ensure the instance is reachable from your IP on ports 22, 80, and 2222 (the security group in `main.tf` currently allows 0.0.0.0/0; restrict to your IP in production).

EC2 instance post-creation checks
- The Terraform `user_data` installs Docker and adds the ubuntu user to the `docker` group. Reboot/login may be required.
- SSH in to verify Docker is running:

```powershell
ssh -i C:\path\to\your\key.pem ubuntu@<EC2_PUBLIC_IP>
# then on the instance
sudo systemctl status docker
```

Configuring the experiment
1. Edit `main.py` and set the three variables:
- `EC2_HOST` — the public IP of your EC2 instance.
- `EC2_USER` — typically `ubuntu` for Ubuntu AMIs, `ec2-user` for Amazon Linux.
- `EC2_KEY_FILE` — local path to your `.pem` key (absolute path on Windows: e.g., `C:\Users\you\keys\mykey.pem`).
2. Confirm `requirements.txt` packages installed in your active virtualenv.
3. Optional but recommended: Create an S3 bucket or local folder to collect logs and results. The easiest for testing is to write a CSV to the repository folder.

Quick smoke run (no attacker thread)
- To verify SSH connectivity and that the environment can start/stop containers, set `run_attacker_thread` call off (comment out) and run `python .\main.py` to ensure `CloudHoneynetEnv` can SSH and execute Docker commands.

Running the full experiment (adaptive agent)
- Make sure your EC2 instance has Docker installed and outbound access as needed.
- Start the experiment:

```powershell
python .\main.py
```

- The script will:
  - Start a background attacker thread (scripted) that hits the honeypot port 2222.
  - Instantiate the DQN agent and run episodes.
  - For each timestep the agent chooses an action and the environment executes Docker commands on the EC2 instance.

Data collection & logging (recommended)
- The default `main.py` prints per-episode totals. For reproducible experiments, record the following each episode to a CSV or JSONL file:
  - Episode number
  - Timestep count
  - Per-timestep actions
  - Per-timestep rewards
  - Cumulative total reward
  - Timestamps
  - Any detected attacker events (timestamp, source IP if available)

- Example snippet to append per-episode results to CSV (drop into `main.py` after each episode):

```python
import csv
with open('results.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([e+1, total_reward, agent.epsilon])
```

Experiment protocol (Control vs Adaptive)
1. Control (Static) run:
   - Deploy a static honeypot (always Cowrie or always Web) and run `attacker.py` for N hours (24 recommended) and record "interactions captured" metrics.
2. Adaptive run (DeceptiCloud):
   - Run `main.py` (adaptive agent) while the same `attacker.py` generates traffic for N hours. Record the same metrics.
3. Repeat both runs several times (3+ runs per condition) to reduce variance.
4. Metrics to collect:
   - Total interactions captured (connections, sessions)
   - Unique attacker IPs
   - Average session duration
   - Commands executed by attacker (if logged) or honeypot events
   - Resource cost (EC2 uptime or Docker resource cost estimate)
   - Reward traces and agent epsilon over time

Evaluating results
- Use the notebook `notebooks/01_data_analysis.ipynb` to load `results.csv` / detailed logs and compute:
  - Mean and standard deviation per metric across runs
  - Simple bar charts comparing Control vs Adaptive
  - Time series of cumulative interactions
- Use statistical tests (t-test or non-parametric test like Mann-Whitney U) to show significance if sample sizes are adequate.

Reward engineering & tuning (practical tips)
- Start simple: +10 for attacker matched to honeypot type, -1 per idle honeypot timestep.
- Monitor reward traces: if the agent collapses to "always idle" or "always one honeypot", adjust gamma/epsilon or the reward magnitudes.
- Try shaping rewards gradually: give small positive reward for any attack observed (to encourage exploration) and larger reward for matching honeypot types.
- Hyperparameters to grid-search (suggested ranges):
  - Learning rate: [1e-3, 1e-4]
  - Gamma: [0.9, 0.99]
  - Epsilon decay: [0.99, 0.999]
  - Replay memory size and batch size

Reproducibility checklist
- Pin package versions in `requirements.txt` (current file lists package names only). Example pinned versions recommended for experiment reproducibility.
- Store the Git commit hash and the `main.py` config values alongside results.
- Save the Terraform state or record the AMI and security group settings used.
- Optionally snapshot EC2 images (AMIs) used in experiments.

Extensions and improvements (recommended next steps)
- Replace the scripted attacker with a more realistic agent (e.g., CALDERA, an ARL adversary, or recorded real-world traffic).
- Move logs and results to S3 and use CloudWatch for continuous monitoring.
- Add a small REST API on the EC2 instance to accept orchestration commands (instead of SSH exec) for reliability and observability.
- Add unit/integration tests that mock the SSH client and Docker commands.
- Harden the environment: restrict security group CIDRs, use VPC flow logs, and isolate the lab network.

SSM and S3 (cloud-friendly improvements)
-
 If you use AWS, prefer AWS SSM RunCommand over raw SSH for automation. Advantages:
  - No need to manage long-lived SSH keys or open additional ports.
  - Works with IAM-based instance profiles and is auditable via CloudTrail.

 How to enable SSM in this repo:
 1. Ensure the EC2 instance has the SSM Agent installed (many official AMIs include it) and an IAM instance profile that allows `ssm:SendCommand` and `ssm:GetCommandInvocation`.
 2. In `main.py`, set `USE_SSM = True` and provide `SSM_INSTANCE_ID` (or leave it blank and the script will attempt to auto-detect the instance id from the public IP using AWS APIs). Set `AWS_REGION` if needed.

 S3 Upload of results
 - To keep experiments durable and centralized, set the environment variable `DECEPTICLOUD_RESULTS_BUCKET` to an S3 bucket you control before starting `main.py`. At the end of the experiment `main.py` will upload the `results/` folder to `s3://<bucket>/decepticloud_results/`.

 Automation helper
 - A PowerShell helper `scripts/run_experiment.ps1` is included to create a virtualenv, install dependencies, and run the experiment on Windows.

IAM policy & instance profile (SSM + S3)
 - A sample IAM policy for an EC2 instance role that allows SSM RunCommand and S3 uploads is included at `infra/ssm_s3_role_policy.json`.
 - Before using it, open the JSON and replace `REPLACE_WITH_YOUR_BUCKET` with the name of your S3 bucket.
 - To apply it manually (example using AWS CLI):

```powershell
# 1. Create an IAM policy from the JSON
aws iam create-policy --policy-name DeceptiCloudSSMS3Policy --policy-document file://infra/ssm_s3_role_policy.json

# 2. Create an instance role and attach the policy (simplified example)
aws iam create-role --role-name DeceptiCloudInstanceRole --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
aws iam attach-role-policy --role-name DeceptiCloudInstanceRole --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/DeceptiCloudSSMS3Policy

# 3. Create instance profile and add role
aws iam create-instance-profile --instance-profile-name DeceptiCloudInstanceProfile
aws iam add-role-to-instance-profile --instance-profile-name DeceptiCloudInstanceProfile --role-name DeceptiCloudInstanceRole

# 4. When launching the EC2 instance (via console or Terraform), attach the instance profile `DeceptiCloudInstanceProfile`.
```

Dry-run mode (safe verification)
 - A `dry-run` mode is available to verify behavior without executing remote commands. Set the environment variable `DECEPTICLOUD_DRY_RUN=1` before running `main.py`, or use the PowerShell helper with `-DryRun`.
 - In dry-run mode the environment will print the exact Docker/command lines it would execute but will not run them. This is the safest way to verify orchestration before using real infrastructure.


Ethics and legal
- Only run attack simulations in your own lab environment or explicit written consent.
- Avoid targeting third-party services or systems.

Troubleshooting
- SSH connection fails: verify `EC2_KEY_FILE` path and file permissions and that the keypair matches the EC2 instance `key_name`.
- Docker not starting: check `sudo systemctl status docker` in the instance and view `journalctl -u docker`.
- Cowrie container not starting: try running the image manually and inspect logs with `docker logs cowrie_honeypot`.

Smoke-check utility
-
 Use the included smoke-check tool to verify connectivity and Docker readiness before running experiments.

 SSH mode (default):
 - Run a quick local check via SSH (requires your `EC2_KEY_FILE`):

```powershell
.\scripts\run_smoke_check.ps1 -TargetHost "<EC2_PUBLIC_IP>" -User "ubuntu" -KeyFile "C:\path\to\key.pem"
```

 SSM mode (recommended on AWS):
 - Ensure the instance has SSM agent and an instance profile with the policy in `infra/ssm_s3_role_policy.json`.
 - Run the smoke-check via SSM by specifying the instance id and region:

```powershell
.\scripts\run_smoke_check.ps1 -UseSSM -SSMInstanceId "i-0123456789abcdef0" -AWSRegion "us-east-1"
```

 Dry-run
 - To only print the commands the smoke-check would run (safe verification), pass `-DryRun` to the wrapper or set `DECEPTICLOUD_DRY_RUN=1`.


How I recommend you proceed next (practical minimal plan)
1. Pin package versions in `requirements.txt` and create a Python virtualenv.
2. Configure and run Terraform to create the instance.
3. Smoke test SSH + Docker actions by running `main.py` with attacker thread disabled.
4. Run short adaptive experiment (1–2 hours) and collect `results.csv`.
5. Run equivalent static experiment for the same time window.
6. Analyze results in `notebooks/01_data_analysis.ipynb` and iterate on reward function.

Contact / notes
- If you want, I can: add automated CSV logging to `main.py`, pin dependency versions, or add a small `scripts/` folder with helper commands to run Terraform and experiments.

License / citations
- Include appropriate citations for Cowrie, DQN, and any other third-party projects used in the final write-up.
