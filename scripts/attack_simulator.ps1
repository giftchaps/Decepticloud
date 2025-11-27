param(
    [Parameter(Mandatory=$true)]
    [string]$TargetHost,
    
    [string]$AttackType = "ssh",
    
    [int]$Duration = 60,
    
    [int]$Intensity = 5,
    
    [string]$SourceIP = "auto"
)

$ErrorActionPreference = "Stop"

Write-Host "DeceptiCloud Attack Simulator" -ForegroundColor Red
Write-Host "=============================" -ForegroundColor Red
Write-Host "Target: $TargetHost" -ForegroundColor Yellow
Write-Host "Attack Type: $AttackType" -ForegroundColor Yellow
Write-Host "Duration: $Duration seconds" -ForegroundColor Yellow
Write-Host "Intensity: $Intensity attempts per minute" -ForegroundColor Yellow

function Test-SSHHoneypot {
    param($TargetHost, $Attempts)
    
    Write-Host "Simulating SSH brute force attacks..." -ForegroundColor Cyan
    
    $usernames = @("admin", "root", "user", "test", "guest", "ubuntu", "ec2-user")
    $passwords = @("password", "123456", "admin", "root", "test", "guest")
    
    for ($i = 1; $i -le $Attempts; $i++) {
        $username = $usernames | Get-Random
        $password = $passwords | Get-Random
        
        Write-Host "[$i/$Attempts] Attempting SSH: $username@$TargetHost" -ForegroundColor Gray
        
        # Use plink (PuTTY) for SSH attempts if available, otherwise use built-in SSH
        try {
            if (Get-Command plink -ErrorAction SilentlyContinue) {
                $result = echo "y" | plink -ssh -P 2222 -l $username -pw $password $Host "exit" 2>&1
            } else {
                # Use PowerShell SSH (requires OpenSSH client)
                $env:SSH_ASKPASS = ""
                $result = ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -p 2222 "$username@$TargetHost" "exit" 2>&1
            }
        } catch {
            Write-Host "  Connection attempt failed (expected)" -ForegroundColor Green
        }
        
        # Random delay between attempts
        Start-Sleep -Seconds (Get-Random -Minimum 2 -Maximum 8)
    }
}

function Test-WebHoneypot {
    param($TargetHost, $Attempts)
    
    Write-Host "Simulating web attacks..." -ForegroundColor Cyan
    
    $paths = @(
        "/admin", "/login", "/wp-admin", "/phpmyadmin", "/admin.php",
        "/config.php", "/database.php", "/backup.sql", "/.env",
        "/api/users", "/api/admin", "/robots.txt", "/sitemap.xml"
    )
    
    $userAgents = @(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "curl/7.68.0", "python-requests/2.25.1", "Wget/1.20.3",
        "sqlmap/1.4.7", "Nikto/2.1.6"
    )
    
    for ($i = 1; $i -le $Attempts; $i++) {
        $path = $paths | Get-Random
        $userAgent = $userAgents | Get-Random
        $url = "http://$TargetHost$path"
        
        Write-Host "[$i/$Attempts] HTTP request: $url" -ForegroundColor Gray
        
        try {
            $response = Invoke-WebRequest -Uri $url -UserAgent $userAgent -TimeoutSec 5 -ErrorAction SilentlyContinue
            Write-Host "  Response: $($response.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "  Request failed (expected)" -ForegroundColor Green
        }
        
        # Random delay
        Start-Sleep -Seconds (Get-Random -Minimum 1 -Maximum 5)
    }
}

function Test-PortScan {
    param($TargetHost)
    
    Write-Host "Performing port scan..." -ForegroundColor Cyan
    
    $commonPorts = @(22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 2222, 3389, 5432, 3306)
    
    foreach ($port in $commonPorts) {
        Write-Host "Scanning port $port..." -ForegroundColor Gray
        
        try {
            $tcpClient = New-Object System.Net.Sockets.TcpClient
            $connect = $tcpClient.BeginConnect($TargetHost, $port, $null, $null)
            $wait = $connect.AsyncWaitHandle.WaitOne(1000, $false)
            
            if ($wait) {
                try {
                    $tcpClient.EndConnect($connect)
                    Write-Host "  Port ${port}: OPEN" -ForegroundColor Red
                } catch {
                    Write-Host "  Port ${port}: CLOSED" -ForegroundColor Green
                }
            } else {
                Write-Host "  Port ${port}: TIMEOUT" -ForegroundColor Yellow
            }
            
            $tcpClient.Close()
        } catch {
            Write-Host "  Port ${port}: ERROR" -ForegroundColor Gray
        }
        
        Start-Sleep -Milliseconds 100
    }
}

# Calculate attack frequency
$attackInterval = [math]::Max(1, 60 / $Intensity)
$totalAttacks = [math]::Ceiling($Duration / $attackInterval)

Write-Host "`nStarting attack simulation..." -ForegroundColor Red
Write-Host "Will perform $totalAttacks attacks over $Duration seconds" -ForegroundColor Yellow

# Perform initial reconnaissance
Write-Host "`n=== RECONNAISSANCE PHASE ===" -ForegroundColor Magenta
Test-PortScan -Host $TargetHost

# Main attack loop
Write-Host "`n=== ATTACK PHASE ===" -ForegroundColor Magenta
$startTime = Get-Date

switch ($AttackType.ToLower()) {
    "ssh" {
        Test-SSHHoneypot -Host $TargetHost -Attempts $totalAttacks
    }
    "web" {
        Test-WebHoneypot -Host $TargetHost -Attempts $totalAttacks
    }
    "mixed" {
        $sshAttacks = [math]::Ceiling($totalAttacks * 0.7)
        $webAttacks = $totalAttacks - $sshAttacks
        
        Write-Host "Mixed attack: $sshAttacks SSH + $webAttacks Web" -ForegroundColor Cyan
        Test-SSHHoneypot -Host $TargetHost -Attempts $sshAttacks
        Test-WebHoneypot -Host $TargetHost -Attempts $webAttacks
    }
    default {
        Write-Host "Unknown attack type: $AttackType" -ForegroundColor Red
        Write-Host "Available types: ssh, web, mixed" -ForegroundColor Yellow
        exit 1
    }
}

$endTime = Get-Date
$actualDuration = ($endTime - $startTime).TotalSeconds

Write-Host "`n=== ATTACK COMPLETED ===" -ForegroundColor Green
Write-Host "Duration: $([math]::Round($actualDuration, 1)) seconds" -ForegroundColor White
Write-Host "Total attacks: $totalAttacks" -ForegroundColor White
Write-Host "Average rate: $([math]::Round($totalAttacks / $actualDuration * 60, 1)) attacks/minute" -ForegroundColor White

Write-Host "`nCheck your DeceptiCloud dashboard for attack detection!" -ForegroundColor Cyan
Write-Host "Run: .\scripts\monitor_system.ps1 -EC2Host $TargetHost -KeyFile <keyfile> -Action dashboard" -ForegroundColor Yellow