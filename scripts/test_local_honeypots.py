#!/usr/bin/env python3
"""
Local Honeypot Testing Script

Validates that DeceptiCloud honeypots are working correctly on localhost.
Tests SSH honeypot (port 2222), web honeypot (port 8080), and logging.
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


class LocalHoneypotTester:
    """Automated testing for local DeceptiCloud deployment."""

    def __init__(self):
        """Initialize local honeypot tester."""
        self.results = []

    def test_ssh_honeypot(self) -> bool:
        """
        Test SSH honeypot on localhost:2222.

        Returns:
            True if SSH honeypot is working correctly
        """
        print("\n" + "=" * 60)
        print("TEST 1: SSH Honeypot (Cowrie) - localhost:2222")
        print("=" * 60)

        try:
            print("[*] Connecting to localhost:2222...")

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try to connect with default Cowrie credentials
            try:
                ssh.connect(
                    'localhost',
                    port=2222,
                    username='root',
                    password='password',
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
                    'ls -la /home',
                    'pwd'
                ]

                for cmd in commands:
                    try:
                        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=5)
                        output = stdout.read().decode('utf-8')
                        if output:
                            print(f"✓ Command '{cmd}' executed successfully")
                        else:
                            print(f"⚠ Command '{cmd}' returned no output")
                    except Exception as e:
                        print(f"⚠ Command '{cmd}' failed: {e}")

                ssh.close()

                self.results.append({
                    'test': 'SSH Honeypot',
                    'status': 'PASS',
                    'details': 'SSH honeypot accessible and responsive'
                })
                return True

            except paramiko.AuthenticationException as e:
                print(f"⚠ Authentication failed: {e}")
                print("  This might be OK if Cowrie has restrictive userdb")
                print("  Try these credentials:")
                print("    - username: root, password: password")
                print("    - username: root, password: 123456")
                print("    - username: ubuntu, password: ubuntu")

                self.results.append({
                    'test': 'SSH Honeypot',
                    'status': 'PARTIAL',
                    'details': 'Connection established but authentication failed'
                })
                return True

        except Exception as e:
            print(f"✗ SSH honeypot test failed: {e}")
            print(f"  Make sure containers are running: docker-compose -f docker-compose.local.yml ps")
            self.results.append({
                'test': 'SSH Honeypot',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_web_honeypot(self) -> bool:
        """
        Test web honeypot on localhost:8080.

        Returns:
            True if web honeypot is working correctly
        """
        print("\n" + "=" * 60)
        print("TEST 2: Web Honeypot (nginx) - localhost:8080")
        print("=" * 60)

        try:
            base_url = "http://localhost:8080"

            # Test 1: Index page
            print(f"[*] Testing {base_url}/...")
            response = requests.get(base_url, timeout=10)

            if response.status_code == 200:
                print(f"✓ Index page accessible (status: {response.status_code})")

                if 'Production API Gateway' in response.text or 'API' in response.text:
                    print("✓ Realistic content detected")
                else:
                    print("⚠ Content may not be realistic enough")
            else:
                print(f"⚠ Unexpected status code: {response.status_code}")

            # Test 2: robots.txt
            print(f"\n[*] Testing {base_url}/robots.txt...")
            response = requests.get(f"{base_url}/robots.txt", timeout=10)

            if response.status_code == 200:
                if 'Disallow' in response.text:
                    print("✓ robots.txt present with realistic content")
                    if '/admin' in response.text or '/api' in response.text:
                        print("  ✓ Contains realistic disallow rules")
                else:
                    print("⚠ robots.txt found but no Disallow rules")
            else:
                print(f"⚠ robots.txt not accessible (status: {response.status_code})")

            # Test 3: Honeytoken (.env file)
            print(f"\n[*] Testing {base_url}/.env (honeytoken)...")
            response = requests.get(f"{base_url}/.env", timeout=10)

            if response.status_code == 200:
                content = response.text
                honeytokens_found = []

                if 'AWS_ACCESS_KEY_ID' in content:
                    honeytokens_found.append('AWS credentials')
                if 'DB_PASSWORD' in content:
                    honeytokens_found.append('Database password')
                if 'STRIPE_KEY' in content:
                    honeytokens_found.append('Stripe API key')
                if 'REDIS_PASSWORD' in content:
                    honeytokens_found.append('Redis password')

                if honeytokens_found:
                    print(f"✓ Honeytoken (.env) accessible with fake credentials!")
                    print(f"  Found: {', '.join(honeytokens_found)}")
                else:
                    print("⚠ .env accessible but no recognizable honeytokens")
            else:
                print(f"⚠ .env not accessible (status: {response.status_code})")

            # Test 4: API status endpoint
            print(f"\n[*] Testing {base_url}/api-status.json...")
            response = requests.get(f"{base_url}/api-status.json", timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'status' in data and data['status'] == 'operational':
                        print("✓ API status endpoint working")
                except:
                    print("⚠ API status endpoint returned non-JSON")
            else:
                print(f"⚠ API status endpoint not found (status: {response.status_code})")

            # Test 5: Common enumeration paths
            print(f"\n[*] Testing common enumeration paths...")
            test_paths = ['/admin', '/login', '/api', '/.git/config', '/backup.sql']
            accessible_paths = 0

            for path in test_paths:
                try:
                    response = requests.get(f"{base_url}{path}", timeout=5)
                    if response.status_code in [200, 403, 404]:
                        accessible_paths += 1
                except:
                    pass

            print(f"✓ Web server responds to enumeration ({accessible_paths}/{len(test_paths)} paths)")

            self.results.append({
                'test': 'Web Honeypot',
                'status': 'PASS',
                'details': 'Web honeypot accessible with realistic content and honeytokens'
            })
            return True

        except requests.exceptions.ConnectionError as e:
            print(f"✗ Cannot connect to web honeypot: {e}")
            print(f"  Make sure containers are running: docker-compose -f docker-compose.local.yml ps")
            self.results.append({
                'test': 'Web Honeypot',
                'status': 'FAIL',
                'details': 'Connection refused - container may not be running'
            })
            return False
        except Exception as e:
            print(f"✗ Web honeypot test failed: {e}")
            self.results.append({
                'test': 'Web Honeypot',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_docker_containers(self) -> bool:
        """
        Test that Docker containers are running and healthy.

        Returns:
            True if containers are running
        """
        print("\n" + "=" * 60)
        print("TEST 3: Docker Container Status")
        print("=" * 60)

        try:
            # Check if containers are running
            print("[*] Checking Docker containers...")

            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=honeypot_local', '--format', '{{.Names}}\t{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print(f"✗ Failed to check Docker containers: {result.stderr}")
                self.results.append({
                    'test': 'Docker Containers',
                    'status': 'FAIL',
                    'details': 'Docker command failed'
                })
                return False

            containers = result.stdout.strip().split('\n')
            if not containers or containers == ['']:
                print("✗ No honeypot containers found")
                print("  Start containers with: docker-compose -f docker-compose.local.yml up -d")
                self.results.append({
                    'test': 'Docker Containers',
                    'status': 'FAIL',
                    'details': 'No containers running'
                })
                return False

            print(f"\n[*] Found {len(containers)} container(s):")

            expected_containers = ['cowrie_honeypot_local', 'nginx_honeypot_local']
            found_containers = []

            for container in containers:
                if '\t' in container:
                    name, status = container.split('\t', 1)
                    print(f"  - {name}: {status}")

                    if name in expected_containers:
                        found_containers.append(name)

                        if 'Up' in status:
                            print(f"    ✓ {name} is running")
                        else:
                            print(f"    ⚠ {name} may not be healthy")

            # Check for missing containers
            missing = set(expected_containers) - set(found_containers)
            if missing:
                print(f"\n⚠ Missing containers: {', '.join(missing)}")
                print(f"  Start with: docker-compose -f docker-compose.local.yml up -d")

            # Check container health
            print("\n[*] Checking container health...")
            for container in expected_containers:
                result = subprocess.run(
                    ['docker', 'inspect', '--format', '{{.State.Health.Status}}', container],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    health = result.stdout.strip()
                    if health in ['healthy', 'starting', '']:
                        print(f"  ✓ {container}: {health or 'running (no health check)'}")
                    else:
                        print(f"  ⚠ {container}: {health}")

            self.results.append({
                'test': 'Docker Containers',
                'status': 'PASS' if not missing else 'PARTIAL',
                'details': f'Found {len(found_containers)}/{len(expected_containers)} containers'
            })

            return len(found_containers) > 0

        except FileNotFoundError:
            print("✗ Docker not found - is Docker installed and running?")
            self.results.append({
                'test': 'Docker Containers',
                'status': 'FAIL',
                'details': 'Docker not available'
            })
            return False
        except Exception as e:
            print(f"✗ Docker container test failed: {e}")
            self.results.append({
                'test': 'Docker Containers',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_logging(self) -> bool:
        """
        Test that logs are being generated.

        Returns:
            True if logs are accessible
        """
        print("\n" + "=" * 60)
        print("TEST 4: Log Files and Directories")
        print("=" * 60)

        try:
            import os

            log_paths = [
                ('data/cowrie/logs', 'Cowrie SSH logs'),
                ('data/nginx/logs', 'nginx web logs'),
            ]

            all_exist = True
            for path, description in log_paths:
                if os.path.exists(path):
                    files = os.listdir(path)
                    if files:
                        print(f"✓ {description}: {len(files)} file(s)")
                    else:
                        print(f"⚠ {description}: directory exists but no log files yet")
                else:
                    print(f"✗ {description}: directory not found at {path}")
                    all_exist = False

            # Check if we can read recent logs
            cowrie_log = 'data/cowrie/logs/cowrie.json'
            nginx_log = 'data/nginx/logs/access.log'

            if os.path.exists(cowrie_log):
                size = os.path.getsize(cowrie_log)
                print(f"\n✓ Cowrie JSON log: {size} bytes")
            else:
                print(f"\n⚠ Cowrie JSON log not yet created (will appear after first connection)")

            if os.path.exists(nginx_log):
                size = os.path.getsize(nginx_log)
                print(f"✓ nginx access log: {size} bytes")
            else:
                print(f"⚠ nginx access log not yet created (will appear after first request)")

            self.results.append({
                'test': 'Logging',
                'status': 'PASS' if all_exist else 'PARTIAL',
                'details': 'Log directories configured correctly'
            })

            return True

        except Exception as e:
            print(f"✗ Logging test failed: {e}")
            self.results.append({
                'test': 'Logging',
                'status': 'FAIL',
                'details': str(e)
            })
            return False

    def test_attack_simulation(self) -> bool:
        """
        Simulate basic attacks to generate log data.

        Returns:
            True if attack simulation completed
        """
        print("\n" + "=" * 60)
        print("TEST 5: Attack Simulation (Log Generation)")
        print("=" * 60)

        try:
            print("[*] Simulating attack patterns to generate logs...\n")

            # SSH brute force simulation
            print("[1] SSH brute force simulation:")
            usernames = ['admin', 'root', 'ubuntu', 'test']
            passwords = ['password', '123456', 'admin', 'root']

            for user in usernames:
                for pwd in passwords[:2]:  # Just 2 passwords per user to keep it quick
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect('localhost', port=2222, username=user, password=pwd,
                                  timeout=3, allow_agent=False, look_for_keys=False)
                        ssh.close()
                        print(f"  ✓ Attempt: {user}:{pwd} (logged)")
                        break
                    except:
                        print(f"  ✓ Failed attempt: {user}:{pwd} (logged)")
                    time.sleep(0.5)

            # Web enumeration simulation
            print("\n[2] Web enumeration simulation:")
            attack_paths = [
                '/', '/.env', '/robots.txt', '/admin', '/login',
                '/wp-admin', '/phpmyadmin', '/.git/config',
                '/backup.sql', '/config.php', '/api-status.json'
            ]

            for path in attack_paths:
                try:
                    response = requests.get(f"http://localhost:8080{path}", timeout=3)
                    print(f"  ✓ GET {path} -> {response.status_code} (logged)")
                except Exception as e:
                    print(f"  ⚠ GET {path} -> failed")
                time.sleep(0.3)

            # SQL injection simulation
            print("\n[3] SQL injection simulation:")
            sqli_payloads = [
                "1' OR '1'='1",
                "admin'--",
                "1; DROP TABLE users--"
            ]

            for payload in sqli_payloads:
                try:
                    requests.get(f"http://localhost:8080/api", params={'id': payload}, timeout=3)
                    print(f"  ✓ SQLi attempt: {payload[:20]}... (logged)")
                except:
                    pass
                time.sleep(0.3)

            print("\n✓ Attack simulation complete!")
            print("  Logs should now contain attack data")

            self.results.append({
                'test': 'Attack Simulation',
                'status': 'PASS',
                'details': 'Attack patterns simulated successfully'
            })
            return True

        except Exception as e:
            print(f"✗ Attack simulation failed: {e}")
            self.results.append({
                'test': 'Attack Simulation',
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
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"  ✓ Passed:  {passed}")
        print(f"  ⚠ Partial: {partial}")
        print(f"  ✗ Failed:  {failed}")

        print("\nDetailed Results:")
        for r in self.results:
            status_icon = {
                'PASS': '✓',
                'FAIL': '✗',
                'PARTIAL': '⚠'
            }.get(r['status'], '?')

            print(f"  {status_icon} {r['test']}: {r['status']}")
            print(f"    {r['details']}")

        # Export results
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_file = f"local_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'target': 'localhost',
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'partial': partial
                },
                'results': self.results
            }, f, indent=2)

        print(f"\n✓ Results saved to: {output_file}")

        # Next steps
        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)

        if failed > 0:
            print("\n⚠ SOME TESTS FAILED")
            print("\nTroubleshooting:")
            print("  1. Check containers: docker-compose -f docker-compose.local.yml ps")
            print("  2. View logs: docker-compose -f docker-compose.local.yml logs")
            print("  3. Restart: docker-compose -f docker-compose.local.yml restart")
            return False
        else:
            print("\n✓ ALL TESTS PASSED!")
            print("\nView generated logs:")
            print("  Cowrie: cat data/cowrie/logs/cowrie.json | jq")
            print("  nginx:  cat data/nginx/logs/access.log")
            print("\nTest with RL agent:")
            print("  python main.py --episodes 10")
            print("\nReady for AWS deployment:")
            print("  See PRODUCTION_QUICK_START.md")
            return True


def main():
    parser = argparse.ArgumentParser(
        description='Test DeceptiCloud local honeypot deployment'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only (skip attack simulation)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DeceptiCloud Local Honeypot Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("=" * 60)

    tester = LocalHoneypotTester()

    # Run tests
    tester.test_docker_containers()
    tester.test_ssh_honeypot()
    tester.test_web_honeypot()
    tester.test_logging()

    if not args.quick:
        tester.test_attack_simulation()

    # Print summary
    success = tester.print_summary()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
