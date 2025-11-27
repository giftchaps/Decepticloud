# DeceptiCloud Production Deployment Guide

This guide walks through deploying DeceptiCloud to AWS for real-world honeypot operations.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Infrastructure Deployment](#infrastructure-deployment)
3. [Honeytoken Monitoring Setup](#honeytoken-monitoring-setup)
4. [Cost Control Configuration](#cost-control-configuration)
5. [Testing and Validation](#testing-and-validation)
6. [Monitoring and Alerts](#monitoring-and-alerts)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- **Terraform** >= 1.0
- **AWS CLI** configured with credentials
- **Python 3.8+**
- **Docker** (for local testing)
- **SSH client**

### AWS Account Setup
1. **IAM Permissions**: Ensure your AWS user/role has permissions for:
   - EC2 (create instances, security groups, VPCs)
   - S3 (create buckets)
   - CloudWatch (logs, alarms)
   - CloudTrail (create trails)
   - SNS (create topics, subscriptions)
   - IAM (create roles, policies)

2. **AWS Key Pair**: Create an EC2 key pair for SSH access:
   ```bash
   aws ec2 create-key-pair --key-name decepticloud-key \
     --query 'KeyMaterial' --output text > ~/.ssh/decepticloud-key.pem
   chmod 400 ~/.ssh/decepticloud-key.pem
   ```

3. **Service Limits**: Verify you have quota for:
   - At least 1 VPC
   - At least 1 EC2 instance (t2.medium or larger recommended)
   - CloudTrail trails

### Local Setup
```bash
# Clone repository
git clone https://github.com/your-org/decepticloud.git
cd decepticloud

# Install Python dependencies
pip install -r requirements.txt

# Install Terraform (if not already installed)
# macOS
brew install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

## Infrastructure Deployment

### Step 1: Configure Terraform Variables

Create `infra/terraform.tfvars`:

```hcl
# AWS Region
region = "us-east-1"

# EC2 Configuration
instance_type = "t2.medium"  # Recommended for production
ami           = "ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS (update for your region)
key_name      = "decepticloud-key"

# S3 Configuration
create_s3_bucket = true
s3_bucket_name   = "decepticloud-results-YOUR_UNIQUE_ID"  # Must be globally unique

# Network Configuration (optional overrides)
# vpc_cidr        = "10.0.0.0/16"
# public_subnet   = "10.0.1.0/24"
# private_subnet  = "10.0.2.0/24"
```

**Important**: Update the AMI ID for your AWS region:
```bash
# Find latest Ubuntu 22.04 AMI for your region
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
  --output text
```

### Step 2: Initialize Terraform

```bash
cd infra
terraform init
```

### Step 3: Review Deployment Plan

```bash
terraform plan
```

Review the resources that will be created:
- VPC with public/private subnets
- EC2 instance for honeypots
- Security groups (SSH port 2222, HTTP port 80)
- S3 buckets (CloudTrail, results)
- CloudWatch log groups (VPC Flow Logs, CloudTrail)
- CloudTrail for honeytoken monitoring
- SNS topic for alerts
- IAM roles and policies

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. Deployment takes ~5-10 minutes.

**Save the outputs**:
```bash
terraform output > ../deployment_info.txt
```

Key outputs:
- `public_ip` - IP address of honeypot server
- `ssh_honeypot_url` - Command to test SSH honeypot
- `web_honeypot_url` - URL to test web honeypot
- `honeytoken_alerts_topic` - SNS topic for honeytoken alerts

### Step 5: Verify EC2 Instance

Wait for user_data script to complete (5-10 minutes):

```bash
# Get instance ID from Terraform output
INSTANCE_ID=$(terraform output -raw instance_id)

# Check system log for completion
aws ec2 get-console-output --instance-id $INSTANCE_ID | grep "DeceptiCloud honeypot deployment completed"
```

SSH into the instance to verify:
```bash
PUBLIC_IP=$(terraform output -raw public_ip)
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP

# Check Docker containers
docker ps

# Should see:
# - cowrie_honeypot (port 2222)
# - nginx_honeypot (port 80)

# Check logs
docker logs cowrie_honeypot
docker logs nginx_honeypot
```

## Honeytoken Monitoring Setup

### Step 1: Subscribe to Honeytoken Alerts

```bash
# Get SNS topic ARN from Terraform output
SNS_TOPIC=$(terraform output -raw honeytoken_alerts_topic)

# Subscribe your email
aws sns subscribe \
  --topic-arn $SNS_TOPIC \
  --protocol email \
  --notification-endpoint your-email@example.com
```

**Important**: Check your email and confirm the subscription!

### Step 2: Test Honeytoken Detection

The honeypots contain fake AWS credentials in multiple locations:
- `/home/ubuntu/.aws/credentials` (SSH honeypot)
- `/opt/app/config.json` (SSH honeypot)
- `/.env` (Web honeypot)

Fake credentials:
```
AKIA3OEXAMPLEKEY123
AKIA3PRODKEY456789
```

**Test Detection** (from external machine):
```bash
# This should trigger an alert when these credentials are used
aws configure set aws_access_key_id AKIA3OEXAMPLEKEY123
aws configure set aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Try to use them (will fail, but CloudTrail will log attempt)
aws s3 ls
```

You should receive an email alert within 1-2 minutes.

### Step 3: Configure CloudTrail Log Delivery to CloudWatch

Enable CloudTrail to send logs to CloudWatch for real-time monitoring:

```bash
# This is already configured in Terraform, but verify:
TRAIL_ARN=$(aws cloudtrail list-trails --query 'Trails[?Name==`decepticloud-honeytoken-trail`].TrailARN' --output text)
aws cloudtrail get-trail-status --name $TRAIL_ARN
```

## Cost Control Configuration

### Step 1: Set Up Billing Alarm

```bash
cd ../scripts
python cost_control.py setup-billing-alarm \
  --threshold 50 \
  --email your-email@example.com
```

This creates a CloudWatch alarm that alerts when estimated monthly charges exceed $50.

### Step 2: Configure Automated Cleanup

Create a cron job to run cost monitoring daily:

```bash
# Add to crontab (runs daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * cd /path/to/decepticloud/scripts && python cost_control.py monitor-costs >> /var/log/decepticloud-costs.log 2>&1
```

### Step 3: Review Current Costs

```bash
python cost_control.py monitor-costs
```

Expected monthly costs (us-east-1):
- EC2 t2.medium: ~$35/month (24/7)
- VPC: Free (within limits)
- CloudTrail: ~$2/month (first trail free, data events charged)
- S3 storage: ~$1/month (depends on log volume)
- CloudWatch: ~$2/month (log storage)

**Total: ~$40/month**

### Step 4: Configure Automatic Shutdown (Optional)

To save costs, automatically stop EC2 during non-testing hours:

```bash
# Stop instance at 6 PM weekdays
0 18 * * 1-5 aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Start instance at 8 AM weekdays
0 8 * * 1-5 aws ec2 start-instances --instance-ids $INSTANCE_ID
```

## Testing and Validation

### Test 1: SSH Honeypot

```bash
PUBLIC_IP=$(cd infra && terraform output -raw public_ip)

# Test SSH connection (should connect to Cowrie)
ssh -p 2222 ubuntu@$PUBLIC_IP

# Try some commands
whoami
cat /etc/passwd
cat /home/ubuntu/.aws/credentials  # Honeytoken!
cat /opt/app/config.json  # More honeytokens!
exit
```

**Expected Behavior**:
- Connection succeeds (fake authentication)
- Commands return realistic output
- Honeytokens are visible in fake files

### Test 2: Web Honeypot

```bash
# Test web server
curl http://$PUBLIC_IP/

# Test honeytoken exposure
curl http://$PUBLIC_IP/.env

# Test enumeration
curl http://$PUBLIC_IP/robots.txt
curl http://$PUBLIC_IP/admin
curl http://$PUBLIC_IP/.git/config
```

**Expected Behavior**:
- Index page shows "Production API Gateway"
- `.env` file contains fake credentials
- All requests logged for analysis

### Test 3: Attack Simulation

Run realistic attack simulation:

```bash
cd scripts
python run_realistic_experiment.py \
  --scenario ssh_focused \
  --target $PUBLIC_IP \
  --duration 300
```

**Check Logs**:
```bash
# SSH honeypot logs
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP
docker exec -it cowrie_honeypot cat /cowrie/cowrie-git/var/log/cowrie/cowrie.json | tail -20

# Web honeypot logs
docker exec -it nginx_honeypot cat /var/log/nginx/access.log | tail -20
```

### Test 4: Dwell Time Tracking

```bash
# Run experiment with dwell time tracking
cd src
python -c "
from dwell_time_tracker import get_tracker
import time

tracker = get_tracker()
tracker.session_start('test-session', '$PUBLIC_IP', 'ssh')
time.sleep(2)
tracker.log_command('test-session', 'whoami')
tracker.log_command('test-session', 'cat /etc/passwd')
metrics = tracker.session_end('test-session')
print(metrics)
"
```

### Test 5: RL Agent Training

```bash
cd ..
python main.py --episodes 100 --target $PUBLIC_IP
```

Verify:
- Agent creates Docker containers
- State detection works (SSH/web attacks)
- Rewards are calculated correctly
- Model saves to `models/dqn_honeypot_episode_*.pth`

## Monitoring and Alerts

### VPC Flow Logs

View network traffic:

```bash
# Get log group name
LOG_GROUP=$(cd infra && terraform output -raw vpc_flow_log_group)

# View recent flow logs
aws logs tail $LOG_GROUP --follow
```

Look for:
- Accepted connections to port 2222 (SSH honeypot)
- Accepted connections to port 80 (web honeypot)
- Rejected connections (potential scanning)

### CloudTrail Honeytoken Monitoring

View CloudTrail events:

```bash
# View recent CloudTrail events
aws cloudtrail lookup-events \
  --max-results 50 \
  --query 'Events[*].{Time:EventTime,User:Username,Event:EventName,IP:SourceIPAddress}'

# Filter for honeytoken access key usage
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA3OEXAMPLEKEY123
```

### Dwell Time Metrics

Analyze attacker engagement:

```bash
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP

# Export dwell time data
docker exec cowrie_honeypot python3 -c "
from src.dwell_time_tracker import get_tracker
tracker = get_tracker()
tracker.export_sessions_to_json('/tmp/dwell_time_report.json')
"

# Download report
docker cp cowrie_honeypot:/tmp/dwell_time_report.json ./
```

Analyze with Jupyter notebook:

```bash
jupyter notebook notebooks/01_data_analysis.ipynb
```

## Security Considerations

### 1. Honeypot Isolation

The honeypots are deployed in an isolated VPC with:
- **No access to production systems**
- **Restricted outbound traffic** (egress rules in security group)
- **Separate S3 buckets** for log storage

**Verify Isolation**:
```bash
# SSH into honeypot
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP

# Verify no access to AWS API (should fail)
aws s3 ls

# Verify restricted network access
ping 8.8.8.8  # Should work (internet access for updates)
```

### 2. Log Protection

CloudTrail and VPC Flow Logs are immutable:
- Stored in S3 with versioning
- CloudWatch retention configured (7-30 days)
- IAM policies restrict access

### 3. Honeytoken Safety

The fake credentials are:
- **Obviously fake** (contain "EXAMPLE" or "HONEYTOKEN")
- **Monitored via CloudTrail**
- **Not valid** for any AWS service

### 4. Prevent Honeypot Abuse

Monitor for:
- **DDoS attacks** (CloudWatch metrics)
- **Excessive resource usage** (billing alarms)
- **Malware hosting** (manual log review)

**Mitigation**:
```bash
# Enable rate limiting on EC2 (using iptables)
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP

sudo iptables -A INPUT -p tcp --dport 2222 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 2222 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 -j DROP
```

## Troubleshooting

### Issue: EC2 instance not accessible

**Check security group**:
```bash
aws ec2 describe-security-groups --group-ids $(cd infra && terraform output -raw security_group_id)
```

Verify rules allow:
- Port 22 (your IP for management)
- Port 2222 (0.0.0.0/0 for SSH honeypot)
- Port 80 (0.0.0.0/0 for web honeypot)

**Check instance status**:
```bash
INSTANCE_ID=$(cd infra && terraform output -raw instance_id)
aws ec2 describe-instance-status --instance-ids $INSTANCE_ID
```

### Issue: Docker containers not running

**SSH into instance and check**:
```bash
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP

# Check Docker service
sudo systemctl status docker

# Check containers
docker ps -a

# If containers exited, check logs
docker logs cowrie_honeypot
docker logs nginx_honeypot

# Restart containers
docker-compose -f /opt/decepticloud/docker-compose.yml up -d
```

### Issue: No logs in CloudWatch

**Verify VPC Flow Logs**:
```bash
aws ec2 describe-flow-logs
```

**Verify CloudTrail**:
```bash
aws cloudtrail get-trail-status --name decepticloud-honeytoken-trail
```

**Check IAM permissions**:
```bash
# Verify flow logs role
aws iam get-role --role-name DeceptiCloudVPCFlowLogsRole
```

### Issue: Honeytoken alerts not working

**Check SNS subscription**:
```bash
SNS_TOPIC=$(cd infra && terraform output -raw honeytoken_alerts_topic)
aws sns list-subscriptions-by-topic --topic-arn $SNS_TOPIC
```

Verify subscription status is "Confirmed" (not "PendingConfirmation").

**Check CloudWatch alarm**:
```bash
aws cloudwatch describe-alarms --alarm-names DeceptiCloud-Honeytoken-Usage-Detected
```

**Test metric filter**:
```bash
# Manually test metric filter by simulating log entry
aws logs put-log-events --log-group-name /aws/cloudtrail/decepticloud-honeytokens \
  --log-stream-name test-stream \
  --log-events timestamp=$(date +%s000),message='{"userIdentity":{"accessKeyId":"AKIA3OEXAMPLEKEY123"}}'
```

### Issue: High AWS costs

**Review current month charges**:
```bash
python scripts/cost_control.py monitor-costs --detailed
```

**Identify expensive resources**:
- EC2 instance running 24/7 (~$35/month for t2.medium)
- CloudTrail data events (can be expensive at scale)
- S3 storage (grows over time)

**Cost reduction options**:
1. Use t2.small instead of t2.medium ($17/month vs $35/month)
2. Disable CloudTrail data events (keep management events only)
3. Reduce log retention (7 days instead of 30)
4. Stop EC2 when not actively testing

**Emergency shutdown**:
```bash
INSTANCE_ID=$(cd infra && terraform output -raw instance_id)
aws ec2 stop-instances --instance-ids $INSTANCE_ID
```

## Cleanup and Teardown

When you're done with the honeypot deployment:

### Option 1: Stop Instance (preserve data)

```bash
cd infra
INSTANCE_ID=$(terraform output -raw instance_id)
aws ec2 stop-instances --instance-ids $INSTANCE_ID
```

Costs: ~$2/month (EBS storage only)

### Option 2: Destroy Everything

**Export data first**:
```bash
# Export logs from S3
CLOUDTRAIL_BUCKET=$(terraform output -raw cloudtrail_bucket)
aws s3 sync s3://$CLOUDTRAIL_BUCKET ./backup/cloudtrail/

# Export Cowrie logs
ssh -i ~/.ssh/decepticloud-key.pem ubuntu@$PUBLIC_IP
docker cp cowrie_honeypot:/cowrie/cowrie-git/var/log/cowrie ./backup/cowrie/
```

**Destroy infrastructure**:
```bash
terraform destroy
```

Type `yes` to confirm. This removes:
- EC2 instance
- VPC and subnets
- Security groups
- S3 buckets (if empty)
- CloudWatch logs
- CloudTrail
- IAM roles

**Manual cleanup** (if Terraform destroy fails):
```bash
# Delete S3 buckets (must be empty first)
aws s3 rm s3://$CLOUDTRAIL_BUCKET --recursive
aws s3 rb s3://$CLOUDTRAIL_BUCKET

# Delete CloudWatch log groups
aws logs delete-log-group --log-group-name /aws/vpc/decepticloud-flow-logs
aws logs delete-log-group --log-group-name /aws/cloudtrail/decepticloud-honeytokens
```

## Next Steps

1. **Run Experiments**: Use `scripts/run_realistic_experiment.py` to test different attack scenarios
2. **Analyze Results**: Use Jupyter notebooks in `notebooks/` to analyze dwell time and engagement
3. **Compare RL vs Static**: Run baseline experiments with `scripts/run_static_experiment.py`
4. **Tune RL Agent**: Adjust hyperparameters in `main.py` for better performance
5. **Add More Honeytokens**: Customize fake credentials and files for your threat model
6. **Integrate Threat Intel**: Add known attack IPs to watchlist

## Support and Documentation

- **Main README**: `../README.md`
- **Anti-Detection Guide**: `ANTI_DETECTION.md`
- **Attack Frameworks**: `ATTACK_FRAMEWORKS.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`

## Security Disclosure

If you discover a security issue with DeceptiCloud, please report it responsibly to: security@example.com

**Do not** publicly disclose security vulnerabilities before they are fixed.
