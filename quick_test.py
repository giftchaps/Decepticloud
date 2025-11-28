#!/usr/bin/env python3
"""
Quick test to verify attack detection works
"""
import subprocess
import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.stderr.strip()
    except:
        return "", "timeout"

def test_attack_detection():
    print("=== Quick Attack Detection Test ===")
    
    # 1. Start containers
    print("[1] Starting containers...")
    run_command("docker-compose -f docker-compose.local.yml up -d")
    time.sleep(3)
    
    # 2. Check if containers are running
    stdout, _ = run_command('docker ps --filter "name=honeypot_local" --format "{{.Names}}"')
    print(f"[2] Running containers: {stdout}")
    
    # 3. Test SSH connection
    print("[3] Testing SSH attack...")
    ssh_cmd = 'echo "test" | ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@localhost -p 2222 2>/dev/null'
    stdout, stderr = run_command(ssh_cmd)
    print(f"[3] SSH result: stdout='{stdout}' stderr='{stderr}'")
    
    # 4. Test web request
    print("[4] Testing web attack...")
    web_cmd = "curl -m 5 http://localhost/admin 2>/dev/null"
    stdout, stderr = run_command(web_cmd)
    print(f"[4] Web result: stdout='{stdout}' stderr='{stderr}'")
    
    # 5. Check logs for attacks
    print("[5] Checking Cowrie logs...")
    log_cmd = "docker logs cowrie_honeypot_local --tail 10 2>/dev/null"
    stdout, stderr = run_command(log_cmd)
    if "connection" in stdout.lower() or "new connection" in stdout.lower():
        print("[5] ✅ SSH attack detected in logs!")
        print(f"    Sample: {stdout[-100:]}")
    else:
        print("[5] ❌ No SSH attack detected")
    
    print("[6] Checking nginx logs...")
    log_cmd = "docker logs nginx_honeypot_local --tail 10 2>/dev/null"
    stdout, stderr = run_command(log_cmd)
    if "GET" in stdout or "POST" in stdout:
        print("[6] ✅ Web attack detected in logs!")
        print(f"    Sample: {stdout[-100:]}")
    else:
        print("[6] ❌ No web attack detected")
    
    # 7. Test the detection logic
    print("[7] Testing detection logic...")
    from main_local import LocalDockerEnvironment
    
    env = LocalDockerEnvironment()
    state = env._get_state()
    print(f"[7] Current state: {state}")
    print(f"    attacker_detected={state[0]}, current_honeypot={state[1]}")
    print(f"    attack_intensity={state[2]}, dwell_time={state[3]}")
    
    if state[0] == 1:
        print("[7] ✅ Attack detection working!")
    else:
        print("[7] ❌ Attack detection not working")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_attack_detection()