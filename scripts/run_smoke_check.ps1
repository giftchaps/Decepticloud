param(
    [string]$EC2Host = "YOUR_EC2_IP_ADDRESS",
    [string]$User = "ubuntu",
    [string]$KeyFile = "C:\path\to\key.pem",
    [switch]$UseSSM,
    [string]$SSMInstanceId,
    [string]$AWSRegion,
    [switch]$DryRun
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here

. .\.venv\Scripts\Activate.ps1

$cmd = "python .\scripts\smoke_check.py"
if ($UseSSM) { $cmd += " --use-ssm" }
if ($SSMInstanceId) { $cmd += " --ssm-instance-id $SSMInstanceId" }
if ($AWSRegion) { $cmd += " --region $AWSRegion" }
if (-not $UseSSM) { $cmd += " --host $EC2Host --user $User --key `"$KeyFile`"" }
if ($DryRun) { $cmd += " --dry-run" }

Write-Host "Running: $cmd"
Invoke-Expression $cmd
