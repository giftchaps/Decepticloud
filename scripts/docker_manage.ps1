# Docker management script for DeceptiCloud honeypots
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "build")]
    [string]$Action,
    
    [ValidateSet("ssh", "web", "all")]
    [string]$Service = "all"
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$dockerDir = Join-Path (Split-Path -Parent $here) "docker"
Set-Location $dockerDir

Write-Host "=== DeceptiCloud Docker Management ===" -ForegroundColor Green

switch ($Action) {
    "build" {
        Write-Host "Building honeypot containers..." -ForegroundColor Yellow
        docker-compose build
    }
    "start" {
        Write-Host "Starting honeypot containers..." -ForegroundColor Yellow
        if ($Service -eq "all") {
            docker-compose up -d
        } else {
            docker-compose up -d "$Service-honeypot"
        }
    }
    "stop" {
        Write-Host "Stopping honeypot containers..." -ForegroundColor Yellow
        if ($Service -eq "all") {
            docker-compose down
        } else {
            docker-compose stop "$Service-honeypot"
        }
    }
    "restart" {
        Write-Host "Restarting honeypot containers..." -ForegroundColor Yellow
        if ($Service -eq "all") {
            docker-compose restart
        } else {
            docker-compose restart "$Service-honeypot"
        }
    }
    "status" {
        Write-Host "Container status:" -ForegroundColor Yellow
        docker-compose ps
    }
    "logs" {
        Write-Host "Container logs:" -ForegroundColor Yellow
        if ($Service -eq "all") {
            docker-compose logs -f
        } else {
            docker-compose logs -f "$Service-honeypot"
        }
    }
}

if ($LASTEXITCODE -eq 0 -and $Action -ne "logs") {
    Write-Host "`nOperation completed successfully!" -ForegroundColor Green
    if ($Action -eq "start") {
        Write-Host "SSH Honeypot: localhost:2222" -ForegroundColor Cyan
        Write-Host "Web Honeypot: http://localhost" -ForegroundColor Cyan
    }
}