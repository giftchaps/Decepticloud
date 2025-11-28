#!/usr/bin/env python3
"""
Attack Simulation Script for DeceptiCloud Local Testing
Generates realistic attack traffic against local honeypots
"""

import time
import requests
import subprocess
import argparse
import random
import threading
from datetime import datetime

class AttackSimulator:
    def __init__(self, target_host="localhost", ssh_port=2222, web_port=8080):
        self.target_host = target_host
        self.ssh_port = ssh_port
        self.web_port = web_port
        self.attack_count = 0
        self.running = False
        
    def ssh_attack(self):
        """Simulate SSH brute force attacks"""
        usernames = ["root", "admin", "user", "test", "guest", "ubuntu"]
        passwords = ["password", "123456", "admin", "root", "test", "guest"]
        
        username = random.choice(usernames)
        password = random.choice(passwords)
        
        try:
            # Use subprocess to attempt SSH connection
            cmd = f'echo "{password}" | ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no -p {self.ssh_port} {username}@{self.target_host} "exit"'
            subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            self.attack_count += 1
            print(f"[SSH] Attack {self.attack_count}: {username}@{self.target_host}")
        except Exception as e:
            print(f"[SSH] Attack failed: {e}")
    
    def web_attack(self):
        """Simulate web attacks"""
        paths = [
            "/", "/admin", "/login", "/.env", "/config.php", 
            "/wp-admin", "/phpmyadmin", "/robots.txt", "/sitemap.xml",
            "/api/users", "/api/admin", "/backup.sql", "/.git/config"
        ]
        
        path = random.choice(paths)
        url = f"http://{self.target_host}:{self.web_port}{path}"
        
        try:
            response = requests.get(url, timeout=3)
            self.attack_count += 1
            print(f"[WEB] Attack {self.attack_count}: {url} -> {response.status_code}")
        except Exception as e:
            print(f"[WEB] Attack failed: {e}")
    
    def mixed_attack(self):
        """Randomly choose between SSH and web attacks"""
        if random.random() < 0.6:  # 60% SSH, 40% web
            self.ssh_attack()
        else:
            self.web_attack()
    
    def run_continuous(self, intensity="medium"):
        """Run continuous attacks until stopped"""
        print(f"Starting continuous attack simulation (intensity: {intensity})")
        print("Press Ctrl+C to stop")
        
        # Set attack intervals based on intensity
        intervals = {
            "low": (5, 10),      # 5-10 seconds between attacks
            "medium": (2, 5),    # 2-5 seconds between attacks  
            "high": (0.5, 2)     # 0.5-2 seconds between attacks
        }
        
        min_interval, max_interval = intervals.get(intensity, intervals["medium"])
        self.running = True
        
        try:
            while self.running:
                self.mixed_attack()
                sleep_time = random.uniform(min_interval, max_interval)
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print(f"\nAttack simulation stopped. Total attacks: {self.attack_count}")
            self.running = False
    
    def run_duration(self, duration_seconds, intensity="medium"):
        """Run attacks for a specific duration"""
        print(f"Running attack simulation for {duration_seconds} seconds (intensity: {intensity})")
        
        intervals = {
            "low": (3, 8),
            "medium": (1, 4),
            "high": (0.2, 1.5)
        }
        
        min_interval, max_interval = intervals.get(intensity, intervals["medium"])
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            self.mixed_attack()
            sleep_time = random.uniform(min_interval, max_interval)
            time.sleep(sleep_time)
        
        print(f"Attack simulation completed. Total attacks: {self.attack_count}")
        return self.attack_count

def main():
    parser = argparse.ArgumentParser(description='DeceptiCloud Attack Simulator')
    parser.add_argument('--target', default='localhost', help='Target host')
    parser.add_argument('--ssh-port', type=int, default=2222, help='SSH honeypot port')
    parser.add_argument('--web-port', type=int, default=8080, help='Web honeypot port')
    parser.add_argument('--duration', type=int, help='Duration in seconds')
    parser.add_argument('--continuous', action='store_true', help='Run continuously until stopped')
    parser.add_argument('--intensity', choices=['low', 'medium', 'high'], default='medium', help='Attack intensity')
    parser.add_argument('--type', choices=['ssh', 'web', 'mixed'], default='mixed', help='Attack type')
    
    args = parser.parse_args()
    
    simulator = AttackSimulator(args.target, args.ssh_port, args.web_port)
    
    print("=" * 50)
    print("DeceptiCloud Attack Simulator")
    print("=" * 50)
    print(f"Target: {args.target}")
    print(f"SSH Port: {args.ssh_port}")
    print(f"Web Port: {args.web_port}")
    print(f"Intensity: {args.intensity}")
    print(f"Type: {args.type}")
    print("=" * 50)
    
    if args.continuous:
        simulator.run_continuous(args.intensity)
    elif args.duration:
        simulator.run_duration(args.duration, args.intensity)
    else:
        # Default: run for 60 seconds
        simulator.run_duration(60, args.intensity)

if __name__ == "__main__":
    main()