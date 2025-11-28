#!/usr/bin/env python3
"""
Enhanced Attack Simulator for DeceptiCloud Research

This simulator generates realistic attack patterns that the RL agent can learn from:
- Adaptive attack intensity based on honeypot responses
- Multiple attack vectors (SSH brute force, web scanning, etc.)
- Realistic timing patterns to test deception effectiveness
- Behavioral adaptation to avoid detection
"""

import time
import random
import threading
import subprocess
import requests
import paramiko
import argparse
from datetime import datetime
import sys

class EnhancedAttackSimulator:
    def __init__(self, target_host="localhost", ssh_port=2222, web_port=80):
        self.target_host = target_host
        self.ssh_port = ssh_port
        self.web_port = web_port
        
        # Attack behavior parameters
        self.attack_intensity = 1.0  # Start with low intensity
        self.dwell_time = 0
        self.detection_avoidance = 0.5  # How much to avoid detection
        self.attack_success_rate = 0.0
        
        # Attack patterns
        self.ssh_usernames = ['root', 'admin', 'user', 'test', 'ubuntu', 'centos', 'oracle']
        self.ssh_passwords = ['123456', 'password', 'admin', 'root', '12345', 'qwerty', 'test']
        self.web_paths = [
            '/', '/admin', '/login', '/wp-admin', '/phpmyadmin', 
            '/.env', '/config.php', '/database.sql', '/backup.zip',
            '/api/v1/users', '/admin/config', '/test.php'
        ]
        
        self.running = False
        self.stats = {
            'ssh_attempts': 0,
            'ssh_successes': 0,
            'web_requests': 0,
            'web_responses': 0,
            'detection_events': 0,
            'adaptation_events': 0
        }
        
        print(f"[Simulator] Enhanced attack simulator initialized")
        print(f"[Simulator] Target: {target_host}:{ssh_port} (SSH), {target_host}:{web_port} (Web)")
    
    def _adaptive_delay(self):
        """Calculate delay based on detection avoidance and intensity"""
        base_delay = 2.0 / self.attack_intensity
        avoidance_factor = 1.0 + (self.detection_avoidance * 3.0)
        delay = base_delay * avoidance_factor
        
        # Add randomness to avoid pattern detection
        delay += random.uniform(0, delay * 0.5)
        return max(0.5, min(30.0, delay))  # Clamp between 0.5 and 30 seconds
    
    def _check_honeypot_response(self):
        """Check if honeypots are responding and adapt behavior"""
        ssh_active = False
        web_active = False
        
        # Check SSH honeypot
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=self.target_host,
                port=self.ssh_port,
                username='test',
                password='test',
                timeout=5,
                look_for_keys=False,
                allow_agent=False
            )
            ssh_active = True
            client.close()
        except:
            pass
        
        # Check web honeypot
        try:
            response = requests.get(f"http://{self.target_host}:{self.web_port}/", timeout=5)
            if response.status_code in [200, 404, 403]:
                web_active = True
        except:
            pass
        
        # Adapt behavior based on honeypot presence
        if ssh_active or web_active:
            self.dwell_time += 1
            if self.dwell_time > 5:  # If we've been engaging for a while
                self.detection_avoidance = min(1.0, self.detection_avoidance + 0.1)
                self.stats['adaptation_events'] += 1
                print(f"[Simulator] Adapting behavior - increasing stealth (avoidance: {self.detection_avoidance:.2f})")
        else:
            # No honeypots active, increase intensity to probe
            self.attack_intensity = min(3.0, self.attack_intensity + 0.2)
            self.dwell_time = 0
        
        return ssh_active, web_active
    
    def _ssh_attack_thread(self):
        """SSH brute force attack thread with adaptive behavior"""
        print("[Simulator] Starting SSH attack thread...")
        
        while self.running:
            try:
                # Check if we should attack based on adaptive behavior
                if random.random() > self.detection_avoidance:
                    username = random.choice(self.ssh_usernames)
                    password = random.choice(self.ssh_passwords)
                    
                    print(f"[SSH Attack] Attempting {username}:{password} -> {self.target_host}:{self.ssh_port}")
                    
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    try:
                        client.connect(
                            hostname=self.target_host,
                            port=self.ssh_port,
                            username=username,
                            password=password,
                            timeout=10,
                            look_for_keys=False,
                            allow_agent=False
                        )
                        
                        # If we get here, login succeeded (shouldn't happen in honeypot)
                        self.stats['ssh_successes'] += 1
                        self.attack_success_rate = self.stats['ssh_successes'] / max(1, self.stats['ssh_attempts'])
                        print(f"[SSH Attack] SUCCESS! Logged in as {username}")
                        
                        # Execute some commands to increase dwell time
                        stdin, stdout, stderr = client.exec_command('whoami')
                        time.sleep(1)
                        stdin, stdout, stderr = client.exec_command('ls -la')
                        time.sleep(1)
                        
                        client.close()
                        
                    except paramiko.AuthenticationException:
                        # Expected for honeypot
                        pass
                    except Exception as e:
                        print(f"[SSH Attack] Connection error: {e}")
                    finally:
                        try:
                            client.close()
                        except:
                            pass
                    
                    self.stats['ssh_attempts'] += 1
                
                # Adaptive delay
                delay = self._adaptive_delay()
                time.sleep(delay)
                
            except Exception as e:
                print(f"[SSH Attack] Thread error: {e}")
                time.sleep(5)
    
    def _web_attack_thread(self):
        """Web scanning attack thread with adaptive behavior"""
        print("[Simulator] Starting web attack thread...")
        
        while self.running:
            try:
                # Check if we should attack based on adaptive behavior
                if random.random() > (self.detection_avoidance * 0.7):  # Web attacks are less stealthy
                    path = random.choice(self.web_paths)
                    url = f"http://{self.target_host}:{self.web_port}{path}"
                    
                    print(f"[Web Attack] Requesting {url}")
                    
                    try:
                        # Randomize user agent to avoid detection
                        user_agents = [
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                        ]
                        
                        headers = {
                            'User-Agent': random.choice(user_agents),
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                        }
                        
                        response = requests.get(url, headers=headers, timeout=10)
                        self.stats['web_responses'] += 1
                        
                        print(f"[Web Attack] Response: {response.status_code} ({len(response.content)} bytes)")
                        
                        # If we get interesting responses, increase dwell time
                        if response.status_code in [200, 403]:
                            time.sleep(random.uniform(1, 3))  # Simulate reading content
                        
                    except requests.exceptions.RequestException as e:
                        print(f"[Web Attack] Request failed: {e}")
                    
                    self.stats['web_requests'] += 1
                
                # Adaptive delay
                delay = self._adaptive_delay() * 0.8  # Web attacks slightly faster
                time.sleep(delay)
                
            except Exception as e:
                print(f"[Web Attack] Thread error: {e}")
                time.sleep(5)
    
    def _monitoring_thread(self):
        """Monitor attack effectiveness and adapt strategy"""
        print("[Simulator] Starting monitoring thread...")
        
        while self.running:
            try:
                # Check honeypot responses and adapt
                ssh_active, web_active = self._check_honeypot_response()
                
                # Print status every 30 seconds
                print(f"\n[Simulator] Status Report:")
                print(f"  SSH Honeypot Active: {ssh_active}")
                print(f"  Web Honeypot Active: {web_active}")
                print(f"  Attack Intensity: {self.attack_intensity:.2f}")
                print(f"  Detection Avoidance: {self.detection_avoidance:.2f}")
                print(f"  Dwell Time: {self.dwell_time}")
                print(f"  SSH Attempts: {self.stats['ssh_attempts']}")
                print(f"  Web Requests: {self.stats['web_requests']}")
                print(f"  Adaptations: {self.stats['adaptation_events']}")
                
                time.sleep(30)
                
            except Exception as e:
                print(f"[Monitoring] Thread error: {e}")
                time.sleep(10)
    
    def start_attacks(self, duration=300):
        """Start all attack threads for specified duration"""
        print(f"[Simulator] Starting enhanced attack simulation for {duration} seconds...")
        
        self.running = True
        
        # Start attack threads
        ssh_thread = threading.Thread(target=self._ssh_attack_thread, daemon=True)
        web_thread = threading.Thread(target=self._web_attack_thread, daemon=True)
        monitor_thread = threading.Thread(target=self._monitoring_thread, daemon=True)
        
        ssh_thread.start()
        web_thread.start()
        monitor_thread.start()
        
        try:
            # Run for specified duration
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\n[Simulator] Interrupted by user")
        finally:
            self.running = False
            print("\n[Simulator] Stopping attack simulation...")
            
            # Wait a bit for threads to finish
            time.sleep(2)
            
            # Print final statistics
            print(f"\n[Simulator] Final Statistics:")
            print(f"  SSH Attempts: {self.stats['ssh_attempts']}")
            print(f"  SSH Successes: {self.stats['ssh_successes']}")
            print(f"  Web Requests: {self.stats['web_requests']}")
            print(f"  Web Responses: {self.stats['web_responses']}")
            print(f"  Adaptation Events: {self.stats['adaptation_events']}")
            print(f"  Final Intensity: {self.attack_intensity:.2f}")
            print(f"  Final Avoidance: {self.detection_avoidance:.2f}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Attack Simulator for DeceptiCloud')
    parser.add_argument('--target', default='localhost', help='Target host')
    parser.add_argument('--ssh-port', type=int, default=2222, help='SSH port')
    parser.add_argument('--web-port', type=int, default=80, help='Web port')
    parser.add_argument('--duration', type=int, default=300, help='Attack duration in seconds')
    
    args = parser.parse_args()
    
    print("=== Enhanced DeceptiCloud Attack Simulator ===")
    print(f"Target: {args.target}")
    print(f"SSH Port: {args.ssh_port}")
    print(f"Web Port: {args.web_port}")
    print(f"Duration: {args.duration} seconds")
    print("=" * 50)
    
    simulator = EnhancedAttackSimulator(
        target_host=args.target,
        ssh_port=args.ssh_port,
        web_port=args.web_port
    )
    
    simulator.start_attacks(duration=args.duration)

if __name__ == "__main__":
    main()