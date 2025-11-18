# DeceptiCloud Scripts

PowerShell scripts for managing DeceptiCloud infrastructure and experiments.

## Infrastructure Management

### Quick Setup (Recommended)
```powershell
# Complete infrastructure setup with S3 bucket
.\scripts\setup_infrastructure.ps1 -KeyName "my-ec2-key" -CreateS3Bucket -S3BucketName "decepticloud-results-unique-name"

# Basic setup without S3
.\scripts\setup_infrastructure.ps1 -KeyName "my-ec2-key"
```

### Manual Steps
```powershell
# 1. Initialize Terraform
.\scripts\terraform_init.ps1

# 2. Plan deployment
.\scripts\terraform_apply.ps1 -KeyName "my-ec2-key" -Plan

# 3. Apply configuration
.\scripts\terraform_apply.ps1 -KeyName "my-ec2-key" -AutoApprove

# 4. Destroy when done
.\scripts\terraform_destroy.ps1 -AutoApprove
```

## Experiment Management

### Run Experiment
```powershell
# Basic SSH connection
.\scripts\run_experiment.ps1 -EC2Host "1.2.3.4" -KeyFile "path\to\key.pem"

# Using AWS SSM (no SSH key needed)
.\scripts\run_experiment.ps1 -UseSSM -SSMInstanceId "i-1234567890abcdef0" -AWSRegion "us-east-1"

# Dry run (test without actual deployment)
.\scripts\run_experiment.ps1 -EC2Host "1.2.3.4" -KeyFile "path\to\key.pem" -DryRun
```

### Smoke Test
```powershell
.\scripts\run_smoke_check.ps1
```

### Docker Management
```powershell
# Build honeypot containers
.\scripts\docker_manage.ps1 -Action build

# Start all honeypots
.\scripts\docker_manage.ps1 -Action start

# Start specific honeypot
.\scripts\docker_manage.ps1 -Action start -Service ssh
.\scripts\docker_manage.ps1 -Action start -Service web

# View logs
.\scripts\docker_manage.ps1 -Action logs -Service ssh

# Stop containers
.\scripts\docker_manage.ps1 -Action stop
```

## Parameters

### setup_infrastructure.ps1
- `-KeyName` (required): EC2 key pair name
- `-Region`: AWS region (default: us-east-1)
- `-InstanceType`: EC2 instance type (default: t2.micro)
- `-CreateS3Bucket`: Create S3 bucket for results
- `-S3BucketName`: S3 bucket name (required if CreateS3Bucket)
- `-SkipInit`: Skip terraform init step

### terraform_apply.ps1
- `-KeyName` (required): EC2 key pair name
- `-Region`: AWS region (default: us-east-1)
- `-InstanceType`: EC2 instance type (default: t2.micro)
- `-CreateS3Bucket`: Create S3 bucket
- `-S3BucketName`: S3 bucket name
- `-AutoApprove`: Skip confirmation prompts
- `-Plan`: Only run terraform plan

### run_experiment.ps1
- `-EC2Host`: EC2 public IP address
- `-KeyFile`: Path to SSH private key
- `-User`: SSH username (default: ubuntu)
- `-UseSSM`: Use AWS SSM instead of SSH
- `-SSMInstanceId`: EC2 instance ID for SSM
- `-AWSRegion`: AWS region for SSM
- `-DryRun`: Test mode without actual deployment