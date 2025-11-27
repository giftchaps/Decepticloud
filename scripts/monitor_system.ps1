param(
    [Parameter(Mandatory=$true)]
    [string]$EC2Host,
    
    [Parameter(Mandatory=$true)]
    [string]$KeyFile,
    
    [string]$Action = "dashboard",
    
    [int]$Hours = 24
)

$ErrorActionPreference = "Stop"

Write-Host "DeceptiCloud Monitoring System" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

switch ($Action.ToLower()) {
    "dashboard" {
        Write-Host "Creating real-time dashboard..." -ForegroundColor Yellow
        python -c "
from src.monitoring import monitor
dashboard_path = monitor.create_dashboard()
print(f'Dashboard created: {dashboard_path}')
import webbrowser
webbrowser.open(dashboard_path)
"
    }
    
    "attacks" {
        Write-Host "Fetching attack summary for last $Hours hours..." -ForegroundColor Yellow
        python -c "
from src.monitoring import monitor
import json
summary = monitor.get_attack_summary($Hours)
print(json.dumps(summary, indent=2))
"
    }
    
    "learning" {
        Write-Host "Fetching learning progress..." -ForegroundColor Yellow
        python -c "
from src.monitoring import monitor
import json
metrics = monitor.get_learning_progress($Hours)
for metric, values in metrics.items():
    print(f'{metric}: {len(values)} data points')
    if values:
        latest = values[-1][1] if values else 'N/A'
        print(f'  Latest value: {latest}')
"
    }
    
    "live-logs" {
        Write-Host "Showing live honeypot logs from EC2..." -ForegroundColor Yellow
        Write-Host "Connecting to $EC2Host..." -ForegroundColor Cyan
        
        $sshCommand = "ssh -i `"$KeyFile`" -o StrictHostKeyChecking=no ubuntu@$EC2Host"
        $dockerCommand = "docker logs -f cowrie_honeypot --tail 50"
        
        Write-Host "Command: $sshCommand `"$dockerCommand`"" -ForegroundColor Gray
        Invoke-Expression "$sshCommand `"$dockerCommand`""
    }
    
    "attack-test" {
        Write-Host "Testing attack detection from different IP..." -ForegroundColor Yellow
        Write-Host "This will attempt SSH connection to trigger honeypot" -ForegroundColor Red
        
        # Test connection to honeypot
        $testCommand = "ssh -i `"$KeyFile`" -o StrictHostKeyChecking=no -o ConnectTimeout=5 testuser@$EC2Host -p 2222"
        Write-Host "Testing: $testCommand" -ForegroundColor Gray
        
        try {
            Invoke-Expression $testCommand
        } catch {
            Write-Host "Connection attempt completed (expected to fail)" -ForegroundColor Green
        }
        
        Write-Host "Check dashboard for new attack entry" -ForegroundColor Cyan
    }
    
    "cloudwatch" {
        Write-Host "Opening CloudWatch console..." -ForegroundColor Yellow
        $region = "us-east-1"
        $cwUrl = "https://$region.console.aws.amazon.com/cloudwatch/home?region=$region#logsV2:log-groups/log-group/%252Fdecepticloud%252Fhoneypot"
        Start-Process $cwUrl
        
        $metricsUrl = "https://$region.console.aws.amazon.com/cloudwatch/home?region=$region#metricsV2:graph=~();namespace=DeceptiCloud"
        Start-Process $metricsUrl
    }
    
    "setup-monitoring" {
        Write-Host "Setting up CloudWatch monitoring..." -ForegroundColor Yellow
        python -c "
from src.monitoring import monitor
monitor.setup_cloudwatch_logging()
print('CloudWatch logging configured')
"
    }
    
    "real-time" {
        Write-Host "Starting real-time monitoring loop..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Red
        
        while ($true) {
            Clear-Host
            Write-Host "DeceptiCloud Real-Time Monitor - $(Get-Date)" -ForegroundColor Green
            Write-Host "=========================================" -ForegroundColor Green
            
            # Show attack summary
            python -c "
from src.monitoring import monitor
summary = monitor.get_attack_summary(1)  # Last hour
print(f'Attacks (last hour): {summary.get(\"total_attacks\", 0)}')
print(f'Unique IPs: {summary.get(\"unique_attackers\", 0)}')
if summary.get('attacker_ips'):
    print('Recent IPs:', ', '.join(summary['attacker_ips'][-5:]))
"
            
            Write-Host "`nPress Ctrl+C to stop, refreshing in 30 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
    }
    
    default {
        Write-Host "Available actions:" -ForegroundColor Yellow
        Write-Host "  dashboard     - Create HTML dashboard" -ForegroundColor White
        Write-Host "  attacks       - Show attack summary" -ForegroundColor White
        Write-Host "  learning      - Show learning progress" -ForegroundColor White
        Write-Host "  live-logs     - Stream live honeypot logs" -ForegroundColor White
        Write-Host "  attack-test   - Test attack detection" -ForegroundColor White
        Write-Host "  cloudwatch    - Open CloudWatch console" -ForegroundColor White
        Write-Host "  setup-monitoring - Configure CloudWatch" -ForegroundColor White
        Write-Host "  real-time     - Real-time monitoring loop" -ForegroundColor White
    }
}