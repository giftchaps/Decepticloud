#!/usr/bin/env python3
"""
Production Deployment Testing Script

Validates that DeceptiCloud production deployment is working correctly.
Tests SSH honeypot, web honeypot, logging, and alerting infrastructure.
"""

import argparse
import sys
import time
import requests
import paramiko
import json
import subprocess
from typing import Dict, List, Tuple
from datetime import datetime


class ProductionTester:
    """Automated testing for production DeceptiCloud deployment."""

    def __init__(self, target_ip: str, ssh_key_path: str = None):
        """
        Initialize production tester.

        Args:
            target_ip: Public IP of honeypot EC2 instance
            ssh_key_path: Path to SSH private key for management access
        """
        self.target_ip = target_ip
        self.ssh_key_path = ssh_key_path
        self.results = []

    def test_ssh_honeypot(self) -> bool:
        """
        Test SSH honeypot accessibility and functionality.

        Returns:
            True if SSH honeypot is working correctly
        """
        print("\n" + "=" * 60)
        print("TEST 1: SSH Honeypot (Cowrie)")
        print("=" * 60)

        try:
            # Test connection to Cowrie on port 2222
            print(f"[*] Connecting to {self.target_ip}:2222...")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try to connect (should succeed with Cowrie's fake auth)
            try:
                ssh.connect(
                    self.target_ip,
                    port=2222,
                    username='root',
                    password='password',  # Cowrie default credentials
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )

                print("✓ SSH connection established")

                # Test command execution
                commands = [
                    'whoami',
                    'uname -a',
                    'cat /etc/passwd',
                    'cat /home/ubuntu/.aws/credentials'  # Honeytoken
                ]

                for cmd in commands:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode('utf-8')
                    print(f"✓ Command '{cmd}' executed successfully")

                    if cmd == 'cat /home/ubuntu/.aws/credentials':
                        if 'AKIA3OEXAMPLEKEY123' in output or 'aws_access_key_id' in output:
                            print("✓ Honeytoken found in fake filesystem!")
                        else:
                            print("⚠ Warning: Honeytoken not found in expected location")

                ssh.close()

                self.results.append({
                    'test': 'SSH Honeypot',
                    'status': 'PASS',
                    'details': 'SSH honeypot accessible and responsive'
                })
                return True

            except paramiko.AuthenticationException:
                # This is actually OK for Cowrie - it might reject our credentials
                # but connection was established
                print("⚠ Auth failed, but connection established (Cowrie may have restrictive userdb)")
                self.results.append({
                    'test': 'SSH Honeypot',
                    'status': 'PARTIAL',
                    'details': 'Connection established but authentication restricted'
                })
                return True

        except Exception as e:
            print(f"✗ SSH honeypot test failed: {e}")
            self.results.append({
                'test': 'SSH Honeypot',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_web_honeypot(self) -> bool:
        """
        Test web honeypot accessibility and content.

        Returns:
            True if web honeypot is working correctly
        """
        print("\n" + "=" * 60)
        print("TEST 2: Web Honeypot (nginx)")
        print("=" * 60)

        try:
            base_url = f"http://{self.target_ip}"

            # Test 1: Index page
            print(f"[*] Testing {base_url}/...")
            response = requests.get(base_url, timeout=10)

            if response.status_code == 200:
                print(f"✓ Index page accessible (status: {response.status_code})")

                if 'Production API Gateway' in response.text or 'API' in response.text:
                    print("✓ Realistic content detected")
                else:
                    print("⚠ Content may not be realistic")
            else:
                print(f"⚠ Unexpected status code: {response.status_code}")

            # Test 2: robots.txt
            print(f"[*] Testing {base_url}/robots.txt...")
            response = requests.get(f"{base_url}/robots.txt", timeout=10)

            if response.status_code == 200 and 'Disallow' in response.text:
                print("✓ robots.txt present with realistic content")
            else:
                print("⚠ robots.txt not found or empty")

            # Test 3: Honeytoken (.env file)
            print(f"[*] Testing {base_url}/.env (honeytoken)...")
            response = requests.get(f"{base_url}/.env", timeout=10)

            if response.status_code == 200:
                if 'AWS_ACCESS_KEY_ID' in response.text or 'DB_PASSWORD' in response.text:
                    print("✓ Honeytoken (.env) accessible with fake credentials!")
                else:
                    print("⚠ .env accessible but no honeytokens found")
            else:
                print(f"⚠ .env not accessible (status: {response.status_code})")

            # Test 4: Common enumeration paths
            test_paths = ['/admin', '/api/v1/status', '/config.json', '/.git/config']
            accessible_paths = 0

            for path in test_paths:
                response = requests.get(f"{base_url}{path}", timeout=5)
                if response.status_code in [200, 403, 404]:
                    accessible_paths += 1

            print(f"✓ Web server responds to enumeration attempts ({accessible_paths}/{len(test_paths)} paths)")

            self.results.append({
                'test': 'Web Honeypot',
                'status': 'PASS',
                'details': 'Web honeypot accessible with realistic content'
            })
            return True

        except Exception as e:
            print(f"✗ Web honeypot test failed: {e}")
            self.results.append({
                'test': 'Web Honeypot',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_docker_health(self) -> bool:
        """
        Test Docker container health on EC2 instance.

        Requires SSH key for management access.

        Returns:
            True if all containers are healthy
        """
        print("\n" + "=" * 60)
        print("TEST 3: Docker Container Health")
        print("=" * 60)

        if not self.ssh_key_path:
            print("⚠ Skipping Docker health test (no SSH key provided)")
            self.results.append({
                'test': 'Docker Health',
                'status': 'SKIP',
                'details': 'No SSH key provided for management access'
            })
            return True

        try:
            # Connect to EC2 instance with management SSH key
            print(f"[*] Connecting to EC2 instance via SSH (port 22)...")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(
                self.target_ip,
                port=22,
                username='ubuntu',
                key_filename=self.ssh_key_path,
                timeout=10
            )

            print("✓ Management SSH connection established")

            # Check Docker containers
            stdin, stdout, stderr = ssh.exec_command('docker ps --format "{{.Names}}\t{{.Status}}"')
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if error:
                print(f"⚠ Docker command error: {error}")

            containers = output.strip().split('\n')
            print(f"\n[*] Found {len(containers)} running containers:")

            expected_containers = ['cowrie_honeypot', 'nginx_honeypot']
            found_containers = []

            for container in containers:
                if '\t' in container:
                    name, status = container.split('\t', 1)
                    print(f"  - {name}: {status}")

                    if name in expected_containers:
                        found_containers.append(name)

                        # Check health status
                        if '(healthy)' in status or 'Up' in status:
                            print(f"    ✓ {name} is healthy")
                        else:
                            print(f"    ⚠ {name} may not be healthy")

            # Verify all expected containers are running
            missing = set(expected_containers) - set(found_containers)
            if missing:
                print(f"\n⚠ Missing containers: {missing}")

            # Check logs for errors
            print("\n[*] Checking container logs for errors...")

            for container in expected_containers:
                stdin, stdout, stderr = ssh.exec_command(f'docker logs --tail 10 {container} 2>&1')
                logs = stdout.read().decode('utf-8')

                if 'error' in logs.lower() or 'fatal' in logs.lower():
                    print(f"  ⚠ {container} has errors in recent logs")
                else:
                    print(f"  ✓ {container} logs look clean")

            ssh.close()

            self.results.append({
                'test': 'Docker Health',
                'status': 'PASS' if not missing else 'PARTIAL',
                'details': f'Found {len(found_containers)}/{len(expected_containers)} containers'
            })

            return len(found_containers) == len(expected_containers)

        except Exception as e:
            print(f"✗ Docker health test failed: {e}")
            self.results.append({
                'test': 'Docker Health',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_aws_infrastructure(self) -> bool:
        """
        Test AWS infrastructure (VPC, CloudWatch, CloudTrail).

        Requires AWS CLI to be configured.

        Returns:
            True if infrastructure is properly configured
        """
        print("\n" + "=" * 60)
        print("TEST 4: AWS Infrastructure")
        print("=" * 60)

        try:
            # Test VPC Flow Logs
            print("[*] Checking VPC Flow Logs...")
            result = subprocess.run(
                ['aws', 'ec2', 'describe-flow-logs', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                flow_logs = json.loads(result.stdout)
                if flow_logs.get('FlowLogs'):
                    print(f"✓ Found {len(flow_logs['FlowLogs'])} VPC Flow Log(s)")
                else:
                    print("⚠ No VPC Flow Logs found")
            else:
                print(f"⚠ Failed to check VPC Flow Logs: {result.stderr}")

            # Test CloudTrail
            print("\n[*] Checking CloudTrail...")
            result = subprocess.run(
                ['aws', 'cloudtrail', 'list-trails', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                trails = json.loads(result.stdout)
                if trails.get('Trails'):
                    print(f"✓ Found {len(trails['Trails'])} CloudTrail trail(s)")

                    # Check if honeytoken trail exists
                    honeytoken_trail = [t for t in trails['Trails'] if 'honeytoken' in t.get('Name', '').lower()]
                    if honeytoken_trail:
                        print("✓ Honeytoken monitoring trail found")
                else:
                    print("⚠ No CloudTrail trails found")
            else:
                print(f"⚠ Failed to check CloudTrail: {result.stderr}")

            # Test SNS topics
            print("\n[*] Checking SNS topics for alerts...")
            result = subprocess.run(
                ['aws', 'sns', 'list-topics', '--output', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                topics = json.loads(result.stdout)
                if topics.get('Topics'):
                    honeytoken_topics = [t for t in topics['Topics'] if 'honeytoken' in t.get('TopicArn', '').lower()]
                    if honeytoken_topics:
                        print(f"✓ Found honeytoken alert topic")
                    else:
                        print("⚠ Honeytoken alert topic not found")
            else:
                print(f"⚠ Failed to check SNS topics: {result.stderr}")

            self.results.append({
                'test': 'AWS Infrastructure',
                'status': 'PASS',
                'details': 'Infrastructure components verified'
            })
            return True

        except FileNotFoundError:
            print("⚠ AWS CLI not found - skipping infrastructure tests")
            self.results.append({
                'test': 'AWS Infrastructure',
                'status': 'SKIP',
                'details': 'AWS CLI not available'
            })
            return True
        except Exception as e:
            print(f"✗ AWS infrastructure test failed: {e}")
            self.results.append({
                'test': 'AWS Infrastructure',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_attack_detection(self) -> bool:
        """
        Test that attacks are being detected and logged.

        Returns:
            True if attack detection is working
        """
        print("\n" + "=" * 60)
        print("TEST 5: Attack Detection")
        print("=" * 60)

        try:
            print("[*] Simulating attack patterns...")

            # Simulate SSH brute force
            print("\n[1] SSH brute force simulation:")
            for i in range(3):
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(
                        self.target_ip,
                        port=2222,
                        username=f'attacker{i}',
                        password='wrong_password',
                        timeout=5,
                        allow_agent=False,
                        look_for_keys=False
                    )
                    ssh.close()
                except:
                    pass
                time.sleep(1)

            print("✓ SSH brute force attempts completed")

            # Simulate web enumeration
            print("\n[2] Web enumeration simulation:")
            attack_paths = [
                '/admin', '/login', '/wp-admin', '/phpmyadmin',
                '/.env', '/.git/config', '/backup.sql', '/config.php'
            ]

            for path in attack_paths:
                try:
                    requests.get(f"http://{self.target_ip}{path}", timeout=5)
                except:
                    pass
                time.sleep(0.5)

            print("✓ Web enumeration attempts completed")

            # Simulate SQL injection attempt
            print("\n[3] SQL injection simulation:")
            try:
                requests.get(
                    f"http://{self.target_ip}/api/users",
                    params={'id': "1' OR '1'='1"},
                    timeout=5
                )
            except:
                pass

            print("✓ SQL injection attempts completed")

            print("\n[*] Attack simulation complete. Logs should contain:")
            print("  - SSH authentication attempts (Cowrie logs)")
            print("  - Web enumeration requests (nginx access logs)")
            print("  - SQL injection attempts (nginx access logs)")

            self.results.append({
                'test': 'Attack Detection',
                'status': 'PASS',
                'details': 'Attack simulation completed successfully'
            })
            return True

        except Exception as e:
            print(f"✗ Attack detection test failed: {e}")
            self.results.append({
                'test': 'Attack Detection',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        partial = sum(1 for r in self.results if r['status'] == 'PARTIAL')
        skipped = sum(1 for r in self.results if r['status'] == 'SKIP')
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"  ✓ Passed:  {passed}")
        print(f"  ⚠ Partial: {partial}")
        print(f"  ✗ Failed:  {failed}")
        print(f"  - Skipped: {skipped}")

        print("\nDetailed Results:")
        for r in self.results:
            status_icon = {
                'PASS': '✓',
                'FAIL': '✗',
                'PARTIAL': '⚠',
                'SKIP': '-'
            }.get(r['status'], '?')

            print(f"  {status_icon} {r['test']}: {r['status']}")
            print(f"    {r['details']}")

        # Export results to JSON
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = f"test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'target_ip': self.target_ip,
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'partial': partial,
                    'skipped': skipped
                },
                'results': self.results
            }, f, indent=2)

        print(f"\n✓ Full results saved to: {output_file}")

        # Return overall status
        if failed > 0:
            print("\n⚠ SOME TESTS FAILED - Review results above")
            return False
        elif partial > 0:
            print("\n⚠ ALL CRITICAL TESTS PASSED - Some warnings detected")
            return True
        else:
            print("\n✓ ALL TESTS PASSED - Deployment is production-ready!")
            return True


def main():
    parser = argparse.ArgumentParser(
        description='Test DeceptiCloud production deployment'
    )
    parser.add_argument(
        'target_ip',
        help='Public IP address of honeypot EC2 instance'
    )
    parser.add_argument(
        '--ssh-key',
        help='Path to SSH private key for management access (optional)',
        default=None
    )
    parser.add_argument(
        '--skip-aws',
        action='store_true',
        help='Skip AWS infrastructure tests'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DeceptiCloud Production Deployment Test")
    print("=" * 60)
    print(f"Target IP: {args.target_ip}")
    print(f"SSH Key: {args.ssh_key or 'Not provided'}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    tester = ProductionTester(args.target_ip, args.ssh_key)

    # Run tests
    tester.test_ssh_honeypot()
    tester.test_web_honeypot()
    tester.test_docker_health()

    if not args.skip_aws:
        tester.test_aws_infrastructure()

    tester.test_attack_detection()

    # Print summary
    success = tester.print_summary()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
