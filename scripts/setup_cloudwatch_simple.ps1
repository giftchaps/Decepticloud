param(
    [string]$Region = "us-east-1"
)

Write-Host "Setting up CloudWatch for DeceptiCloud" -ForegroundColor Green

# Check AWS CLI
try {
    aws --version | Out-Null
    Write-Host "AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "ERROR: AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Create log group
Write-Host "Creating log group..." -ForegroundColor Yellow
aws logs create-log-group --log-group-name "/decepticloud/honeypot" --region $Region 2>$null
Write-Host "Log group created" -ForegroundColor Green

# Create dashboard
Write-Host "Creating dashboard..." -ForegroundColor Yellow
$dashboard = '{"widgets":[{"type":"metric","x":0,"y":0,"width":12,"height":6,"properties":{"metrics":[["DeceptiCloud","AttackCount"]],"view":"timeSeries","region":"' + $Region + '","title":"Attacks"}}]}'
$dashboard | Out-File -FilePath "dashboard.json" -Encoding UTF8
aws cloudwatch put-dashboard --dashboard-name "DeceptiCloud-Research" --dashboard-body file://dashboard.json --region $Region
Remove-Item "dashboard.json" -Force
Write-Host "Dashboard created" -ForegroundColor Green

Write-Host "CloudWatch setup complete!" -ForegroundColor Green
$url = "https://$Region.console.aws.amazon.com/cloudwatch/home?region=$Region"
Write-Host "Console URL: $url" -ForegroundColor Cyan