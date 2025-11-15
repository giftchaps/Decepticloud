# PowerShell script to destroy Terraform resources
param(
    [switch]$AutoApprove,
    [switch]$Force
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here\..\infra

Write-Host "=== DeceptiCloud Terraform Destroy ===" -ForegroundColor Red

if (-not $Force) {
    Write-Host "WARNING: This will destroy all AWS resources created by Terraform!" -ForegroundColor Yellow
    $confirm = Read-Host "Are you sure? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "Destroying Terraform resources..." -ForegroundColor Yellow

if ($AutoApprove) {
    & terraform destroy -auto-approve
} else {
    & terraform destroy
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Resources Destroyed ===" -ForegroundColor Green
    Write-Host "All AWS resources have been cleaned up."
} else {
    Write-Host "`nDestroy failed. Check the output above for errors." -ForegroundColor Red
}