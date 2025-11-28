#!/usr/bin/env python3
"""
Test script that keeps honeypots running while generating attacks
"""
import subprocess
import time
import threading

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

def keep_containers_running():
    """Keep containers running"""
    print("[Test] Starting containers...")
    run_command("docker-compose -f docker-compose.local.yml up -d")
    
    while True:
        time.sleep(10)
        # Check if containers are still running
        status = run_command('docker ps --filter "name=honeypot_local" --format "{{.Names}}"')
        if "cowrie_honeypot_local" not in status:
            print("[Test] Restarting Cowrie...")
            run_command("docker-compose -f docker-compose.local.yml up -d cowrie")
        if "nginx_honeypot_local" not in status:
            print("[Test] Restarting nginx...")
            run_command("docker-compose -f docker-compose.local.yml up -d nginx")

def generate_attacks():
    """Generate continuous attacks"""
    time.sleep(5)  # Wait for containers to start
    
    while True:
        # SSH attack
        print("[Attack] SSH attempt...")
        run_command("echo 'test' | ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no root@localhost -p 2222 2>/dev/null")
        
        # Web attack
        print("[Attack] Web request...")
        run_command("curl -m 3 http://localhost/admin 2>/dev/null")
        
        time.sleep(8)  # Attack every 8 seconds

if __name__ == "__main__":
    print("=== DeceptiCloud Attack Test ===")
    
    # Start container management thread
    container_thread = threading.Thread(target=keep_containers_running, daemon=True)
    container_thread.start()
    
    # Start attack thread
    attack_thread = threading.Thread(target=generate_attacks, daemon=True)
    attack_thread.start()
    
    try:
        # Run for 60 seconds
        for i in range(12):
            time.sleep(5)
            # Check logs
            logs = run_command("docker logs cowrie_honeypot_local --tail 3 2>/dev/null")
            if "connection" in logs.lower():
                print(f"[Success] Attack detected in logs!")
            print(f"[Status] Running... ({i*5}s)")
        
        print("\n[Test] Complete! Check logs:")
        print("docker logs cowrie_honeypot_local --tail 10")
        
    except KeyboardInterrupt:
        print("\n[Test] Stopped by user")