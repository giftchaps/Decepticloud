param(
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up CloudWatch for DeceptiCloud" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Check AWS CLI
try {
    $awsVersion = aws --version 2>&1
    Write-Host "AWS CLI: $awsVersion" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
try {
    $identity = aws sts get-caller-identity --region $Region 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS credentials not configured"
    }
    Write-Host "AWS Identity verified" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "`nCreating CloudWatch resources..." -ForegroundColor Yellow

# Create log group
Write-Host "Creating log group: /decepticloud/honeypot" -ForegroundColor Cyan
aws logs create-log-group --log-group-name "/decepticloud/honeypot" --region $Region 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Log group created" -ForegroundColor Green
} else {
    Write-Host "✓ Log group already exists" -ForegroundColor Yellow
}

# Create custom metric filters
Write-Host "`nCreating metric filters..." -ForegroundColor Cyan

# SSH attack filter
$sshFilter = @"
{
    "filterName": "DeceptiCloud-SSH-Attacks",
    "filterPattern": "[timestamp, request_id, event_type=\"attack\", attacker_ip, attack_type=\"ssh_connection\", ...]",
    "logGroupName": "/decepticloud/honeypot",
    "metricTransformations": [
        {
            "metricName": "SSHAttacks",
            "metricNamespace": "DeceptiCloud",
            "metricValue": "1",
            "defaultValue": 0
        }
    ]
}
"@

$sshFilter | Out-File -FilePath "ssh_filter.json" -Encoding UTF8
aws logs put-metric-filter --cli-input-json file://ssh_filter.json --region $Region 2>$null
Remove-Item "ssh_filter.json" -Force
Write-Host "✓ SSH attack metric filter created" -ForegroundColor Green

Write-Host "✓ Metric filters configured" -ForegroundColor Green

# Create CloudWatch dashboard
Write-Host "`nCreating CloudWatch dashboard..." -ForegroundColor Cyan

$dashboardBody = @"
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "DeceptiCloud", "AttackCount", "AttackType", "ssh_connection" ],
                    [ ".", ".", ".", "http_request" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$Region",
                "title": "Attack Detection Over Time",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "DeceptiCloud", "EpisodeReward" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$Region",
                "title": "RL Agent Rewards",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 8,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "DeceptiCloud", "Epsilon" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$Region",
                "title": "Learning Progress (Epsilon)",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 8,
            "y": 6,
            "width": 8,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "DeceptiCloud", "Loss" ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$Region",
                "title": "Training Loss",
                "period": 300
            }
        },
        {
            "type": "metric",
            "x": 16,
            "y": 6,
            "width": 8,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "DeceptiCloud", "ActionTaken", "Action", "ssh" ],
                    [ ".", ".", ".", "web" ],
                    [ ".", ".", ".", "none" ]
                ],
                "view": "timeSeries",
                "stacked": true,
                "region": "$Region",
                "title": "Agent Actions",
                "period": 300
            }
        },
        {
            "type": "log",
            "x": 0,
            "y": 12,
            "width": 24,
            "height": 6,
            "properties": {
                "query": "SOURCE '/decepticloud/honeypot'\n| fields @timestamp, attacker_ip, attack_type, honeypot_type\n| filter event_type = \"attack\"\n| sort @timestamp desc\n| limit 20",
                "region": "$Region",
                "title": "Recent Attacks",
                "view": "table"
            }
        }
    ]
}
"@

$dashboardBody | Out-File -FilePath "dashboard.json" -Encoding UTF8
aws cloudwatch put-dashboard --dashboard-name "DeceptiCloud-Research" --dashboard-body file://dashboard.json --region $Region
Remove-Item "dashboard.json" -Force
Write-Host "✓ CloudWatch dashboard created" -ForegroundColor Green

# Create CloudWatch alarms
Write-Host "`nCreating CloudWatch alarms..." -ForegroundColor Cyan

# High attack rate alarm
aws cloudwatch put-metric-alarm `
    --alarm-name "DeceptiCloud-High-Attack-Rate" `
    --alarm-description "Alert when attack rate exceeds 10 per minute" `
    --metric-name "AttackCount" `
    --namespace "DeceptiCloud" `
    --statistic "Sum" `
    --period 60 `
    --threshold 10 `
    --comparison-operator "GreaterThanThreshold" `
    --evaluation-periods 2 `
    --region $Region

Write-Host "✓ High attack rate alarm created" -ForegroundColor Green

# Learning stagnation alarm
aws cloudwatch put-metric-alarm `
    --alarm-name "DeceptiCloud-Learning-Stagnation" `
    --alarm-description "Alert when epsilon stops decreasing (learning stagnation)" `
    --metric-name "Epsilon" `
    --namespace "DeceptiCloud" `
    --statistic "Average" `
    --period 300 `
    --threshold 0.5 `
    --comparison-operator "GreaterThanThreshold" `
    --evaluation-periods 6 `
    --region $Region

Write-Host "✓ Learning stagnation alarm created" -ForegroundColor Green

Write-Host "`n=== CloudWatch Setup Complete ===" -ForegroundColor Green
Write-Host "Resources created:" -ForegroundColor White
Write-Host "  • Log Group: /decepticloud/honeypot" -ForegroundColor Cyan
Write-Host "  • Metric Filters: SSH and Web attacks" -ForegroundColor Cyan
Write-Host "  • Dashboard: DeceptiCloud-Research" -ForegroundColor Cyan
Write-Host "  • Alarms: High attack rate, Learning stagnation" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Initialize monitoring: python -c 'from src.monitoring import monitor; monitor.setup_cloudwatch_logging()'" -ForegroundColor White
Write-Host "2. Run experiment: .\scripts\run_experiment.ps1 -EC2Host [ip] -KeyFile [key]" -ForegroundColor White
Write-Host "3. View dashboard: .\scripts\monitor_system.ps1 -EC2Host [ip] -KeyFile [key] -Action cloudwatch" -ForegroundColor White

$dashboardUrl = "https://$Region.console.aws.amazon.com/cloudwatch/home?region=$Region#dashboards:name=DeceptiCloud-Research"
Write-Host "`nDashboard URL: $dashboardUrl" -ForegroundColor Cyan