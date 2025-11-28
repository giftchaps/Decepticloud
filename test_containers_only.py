#!/usr/bin/env python3
"""
Simple test to keep honeypot containers running without RL agent interference.
This allows you to test attack simulation against stable honeypots.
"""

import subprocess
import time
import signal
import sys

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def start_honeypots():
    """Start both honeypot containers"""
    print("[Test] Starting honeypot containers...")
    
    # Stop any existing containers
    run_command("docker stop cowrie_honeypot_local nginx_honeypot_local 2>nul")
    run_command("docker rm cowrie_honeypot_local nginx_honeypot_local 2>nul")
    
    # Start Cowrie SSH honeypot
    cmd1 = "docker run -d --name cowrie_honeypot_local -p 2222:2222 cowrie/cowrie:latest"
    stdout1, stderr1 = run_command(cmd1)
    if stderr1:
        print(f"[Test] SSH honeypot error: {stderr1}")
    else:
        print("[Test] SSH honeypot started on port 2222")
    
    # Start nginx web honeypot
    cmd2 = "docker run -d --name nginx_honeypot_local -p 80:80 nginx:alpine"
    stdout2, stderr2 = run_command(cmd2)
    if stderr2:
        print(f"[Test] Web honeypot error: {stderr2}")
    else:
        print("[Test] Web honeypot started on port 80")
    
    return True

def check_containers():
    """Check if containers are running"""
    stdout, _ = run_command("docker ps --format 'table {{.Names}}\\t{{.Status}}'")
    print(f"[Test] Container status:\n{stdout}")
    return stdout

def cleanup():
    """Stop and remove containers"""
    print("\n[Test] Cleaning up containers...")
    run_command("docker stop cowrie_honeypot_local nginx_honeypot_local 2>nul")
    run_command("docker rm cowrie_honeypot_local nginx_honeypot_local 2>nul")
    print("[Test] Cleanup complete")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[Test] Received interrupt signal...")
    cleanup()
    sys.exit(0)

def main():
    """Main test function"""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=== DeceptiCloud Container Test ===")
    print("This will start honeypot containers and keep them running.")
    print("Press Ctrl+C to stop and cleanup.")
    print()
    
    # Start containers
    if not start_honeypots():
        print("[Test] Failed to start containers")
        return
    
    print("\n[Test] Containers started successfully!")
    print("[Test] You can now:")
    print("  - Test SSH: ssh root@localhost -p 2222")
    print("  - Test Web: curl http://localhost")
    print("  - Run attack simulation: python scripts\\simulate_attacks.py")
    print()
    
    # Keep running and show status every 30 seconds
    try:
        while True:
            print(f"\n[Test] Status check at {time.strftime('%H:%M:%S')}:")
            check_containers()
            
            # Check for any stopped containers and restart them
            stdout, _ = run_command("docker ps -a --filter 'name=honeypot_local' --format '{{.Names}} {{.Status}}'")
            if "Exited" in stdout:
                print("[Test] Detected stopped containers, restarting...")
                start_honeypots()
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()