# PowerShell helper to create venv, install deps, and run the experiment
param(
    [string]$KeyFile = "path\to\your\key.pem",
    [string]$EC2Host = "YOUR_EC2_IP_ADDRESS",
    [string]$User = "ubuntu",
    [switch]$UseSSM,
    [switch]$DryRun,
    [string]$SSMInstanceId,
    [string]$AWSRegion
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here

if (-Not (Test-Path -Path ".venv")) {
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt

# Set environment variables for the run
if ($UseSSM) { $env:DECEPTICLOUD_USE_SSM = "1" }
if ($SSMInstanceId) { $env:DECEPTICLOUD_SSM_INSTANCE = $SSMInstanceId }
if ($AWSRegion) { $env:AWS_REGION = $AWSRegion }
if ($DryRun) { $env:DECEPTICLOUD_DRY_RUN = "1" }

# Optional: set an S3 bucket to upload results after the run by setting
# the environment variable DECEPTICLOUD_RESULTS_BUCKET before invoking this script.

# Export the EC2 host/key for the script
$env:EC2_HOST = $EC2Host
$env:EC2_USER = $User
$env:EC2_KEY_FILE = $KeyFile

python .\main.py
