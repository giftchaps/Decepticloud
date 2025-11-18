# Script to generate comprehensive research data
param(
    [string]$EC2Host,
    [string]$KeyFile,
    [int]$Duration = 300,
    [string]$AttackType = "mixed"
)

Write-Host "=== Generating Research Attack Data ===" -ForegroundColor Green

if (-not $EC2Host) {
    Write-Host "ERROR: -EC2Host parameter required" -ForegroundColor Red
    exit 1
}

Write-Host "Target: $EC2Host" -ForegroundColor Cyan
Write-Host "Duration: $Duration seconds" -ForegroundColor Cyan
Write-Host "Attack Type: $AttackType" -ForegroundColor Cyan

# Activate Python environment
& .\.venv\Scripts\Activate.ps1

# Generate attack traffic
python -c "
import paramiko
import requests
import time
import random
import threading

def ssh_attacks(host, duration):
    print('Starting SSH attack simulation...')
    usernames = ['admin', 'root', 'user', 'test', 'guest', 'administrator', 'oracle', 'postgres']
    passwords = ['password', '123456', 'admin', 'root', 'test', 'password123', 'qwerty', '12345']
    
    end_time = time.time() + duration
    attack_count = 0
    
    while time.time() < end_time:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            user = random.choice(usernames)
            pwd = random.choice(passwords)
            
            ssh.connect(host, port=2222, username=user, password=pwd, timeout=5)
            attack_count += 1
        except:
            attack_count += 1
            pass
        
        time.sleep(random.uniform(0.5, 3))
    
    print(f'SSH attacks completed: {attack_count} attempts')

def web_attacks(host, duration):
    print('Starting web attack simulation...')
    usernames = ['admin', 'administrator', 'root', 'user', 'test']
    passwords = ['password', 'admin', '123456', 'password123', 'root']
    paths = ['/', '/admin', '/login', '/wp-admin', '/administrator']
    
    end_time = time.time() + duration
    attack_count = 0
    
    while time.time() < end_time:
        try:
            # Random path access
            path = random.choice(paths)
            requests.get(f'http://{host}{path}', timeout=5)
            
            # Login attempts
            if random.random() < 0.7:  # 70% login attempts
                data = {
                    'username': random.choice(usernames),
                    'password': random.choice(passwords)
                }
                requests.post(f'http://{host}/login', data=data, timeout=5)
            
            attack_count += 1
        except:
            attack_count += 1
            pass
        
        time.sleep(random.uniform(1, 4))
    
    print(f'Web attacks completed: {attack_count} attempts')

# Run attacks based on type
host = '$EC2Host'
duration = $Duration

if '$AttackType' == 'ssh':
    ssh_attacks(host, duration)
elif '$AttackType' == 'web':
    web_attacks(host, duration)
else:  # mixed
    # Run both attack types in parallel
    ssh_thread = threading.Thread(target=ssh_attacks, args=(host, duration))
    web_thread = threading.Thread(target=web_attacks, args=(host, duration))
    
    ssh_thread.start()
    web_thread.start()
    
    ssh_thread.join()
    web_thread.join()

print('Research attack simulation completed!')
"

Write-Host "`nAttack simulation completed!" -ForegroundColor Green
Write-Host "Check your experiment logs for captured attack data." -ForegroundColor Cyan