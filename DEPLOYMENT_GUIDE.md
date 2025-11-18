# DeceptiCloud Cloud Deployment Guide

Complete step-by-step guide to deploy DeceptiCloud on AWS for research testing.

## Prerequisites Setup

### 1. Install Required Tools
```powershell
# Install AWS CLI
winget install Amazon.AWSCLI

# Install Terraform
winget install Hashicorp.Terraform

# Verify installations
aws --version
terraform --version
```

### 2. AWS Account Setup
1. Create AWS account (free tier eligible)
2. Create IAM user with programmatic access
3. Attach policies: `EC2FullAccess`, `IAMFullAccess`, `S3FullAccess`
4. Download access keys

### 3. Configure AWS CLI
```powershell
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)
```

### 4. Create EC2 Key Pair
```powershell
# Create key pair
aws ec2 create-key-pair --key-name decepticloud-key --query 'KeyMaterial' --output text > decepticloud-key.pem

# Set permissions (Windows)
icacls decepticloud-key.pem /inheritance:r /grant:r "%USERNAME%:R"
```

## Cloud Infrastructure Deployment

### 5. Initialize and Deploy Infrastructure
```powershell
# Navigate to project
cd C:\Users\gift2\OneDrive\Desktop\Research\Decepticloud

# Initialize Terraform
.\scripts\terraform_init.ps1

# Deploy infrastructure
.\scripts\terraform_apply.ps1 -KeyName "decepticloud-key" -AutoApprove

# Note the public_ip output - you'll need this!
```

### 6. Verify EC2 Instance
```powershell
# Test SSH connection
ssh -i decepticloud-key.pem ubuntu@<PUBLIC_IP>

# If successful, exit and continue
exit
```

## Honeypot Container Setup

### 7. Prepare Docker Images on EC2
```powershell
# Copy Docker files to EC2
scp -i decepticloud-key.pem -r docker ubuntu@<PUBLIC_IP>:~/

# SSH into instance
ssh -i decepticloud-key.pem ubuntu@<PUBLIC_IP>

# On EC2 instance:
cd docker
sudo docker-compose build
sudo docker images  # Verify images built
exit
```

## Python Environment Setup

### 8. Setup Local Python Environment
```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Research Experiment Execution

### 9. Configure Experiment Parameters
```powershell
# Set environment variables
$env:EC2_HOST = "<YOUR_PUBLIC_IP>"
$env:EC2_USER = "ubuntu"
$env:EC2_KEY_FILE = "decepticloud-key.pem"
$env:AWS_REGION = "us-east-1"
```

### 10. Run Research Experiment
```powershell
# Run full experiment (5 episodes, 24 timesteps each)
python main.py

# For longer research run (modify episodes in main.py):
# EPISODES = 50  # For comprehensive research data
```

### 11. Generate Attack Traffic (Separate Terminal)
```powershell
# While experiment runs, generate realistic attack patterns
python -c "
import paramiko, time, random

def generate_attacks(host, duration=300):
    print('Generating attack traffic for research...')
    usernames = ['admin', 'root', 'user', 'test', 'guest']
    passwords = ['password', '123456', 'admin', 'root', 'test']
    
    for i in range(duration):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            user = random.choice(usernames)
            pwd = random.choice(passwords)
            ssh.connect(host, port=2222, username=user, password=pwd, timeout=5)
        except:
            pass
        time.sleep(random.uniform(1, 5))
    print('Attack simulation complete')

generate_attacks('$env:EC2_HOST')
"
```

## Research Data Collection

### 12. Collect Results
```powershell
# Results are automatically saved to results/ folder
ls results/
# - results_summary.csv (episode-level data)
# - results_per_timestep.csv (detailed timestep data)
```

### 13. Analyze Results
```powershell
# Start Jupyter for analysis
jupyter notebook notebooks/01_data_analysis.ipynb
```

## Research Validation Tests

### 14. Smoke Test Validation
```powershell
# Test all components
.\scripts\run_smoke_check.ps1 -EC2Host $env:EC2_HOST -KeyFile $env:EC2_KEY_FILE
```

### 15. Extended Research Run
```powershell
# For comprehensive research data (modify main.py):
# EPISODES = 100
# Then run:
python main.py

# This will generate extensive data for research analysis
```

## Cleanup (Important for Cost Control)

### 16. Stop Experiment and Cleanup
```powershell
# Stop all honeypots on EC2
ssh -i decepticloud-key.pem ubuntu@<PUBLIC_IP> "sudo docker stop \$(sudo docker ps -q)"

# Destroy AWS infrastructure
.\scripts\terraform_destroy.ps1 -AutoApprove

# Verify cleanup
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name]'
```

## Research Data Analysis

### 17. Key Metrics for Research
- **Learning Convergence**: Episode rewards over time
- **Action Selection**: Frequency of each honeypot deployment
- **Attack Detection Rate**: Successful vs missed attacks
- **Resource Efficiency**: Reward per action taken
- **Adaptation Speed**: How quickly agent learns optimal strategy

### 18. Expected Research Outcomes
- Demonstrate autonomous honeypot deployment
- Show RL agent learning optimal strategies
- Prove adaptive response to attack patterns
- Quantify improvement over static defenses

## Troubleshooting

### Common Issues:
1. **SSH Connection Failed**: Check security group allows port 22
2. **Docker Build Failed**: Ensure EC2 has enough disk space
3. **Experiment Timeout**: Increase timeouts in environment.py
4. **No Attack Detection**: Verify honeypot logs with `docker logs`

### Research Tips:
- Run multiple experiments with different parameters
- Compare random vs learned agent performance  
- Test different attack patterns
- Document all configuration changes

## Cost Estimation
- EC2 t2.micro: ~$0.0116/hour
- Expected research cost: $5-20 for comprehensive testing
- Always cleanup resources when done!