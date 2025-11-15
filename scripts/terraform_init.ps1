# PowerShell script to initialize Terraform
param(
    [string]$Region = "us-east-1",
    [switch]$Upgrade
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here\..\infra

Write-Host "=== DeceptiCloud Terraform Init ===" -ForegroundColor Green
Write-Host "Initializing Terraform in $PWD (region=$Region)" -ForegroundColor Yellow

# Check if terraform is installed
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Terraform not found. Please install Terraform first." -ForegroundColor Red
    Write-Host "Download from: https://www.terraform.io/downloads" -ForegroundColor Yellow
    exit 1
}

# Initialize terraform
if ($Upgrade) {
    & terraform init -upgrade
} else {
    & terraform init
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Initialization Complete ===" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Plan: .\scripts\terraform_apply.ps1 -KeyName <your-key> -Plan"
    Write-Host "2. Apply: .\scripts\terraform_apply.ps1 -KeyName <your-key> -AutoApprove"
    Write-Host "3. Destroy: .\scripts\terraform_destroy.ps1 -AutoApprove"
} else {
    Write-Host "Initialization failed. Check the output above for errors." -ForegroundColor Red
}