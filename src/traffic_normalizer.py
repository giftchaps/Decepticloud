"""
Traffic Normalizer for DeceptiCloud Honeypots

Generates realistic background traffic to make honeypots indistinguishable
from real systems. This increases dwell time by masking the honeypot nature.

Key techniques:
- Simulated legitimate SSH sessions
- Realistic web traffic patterns
- Variable timing to mimic real users
- Normal administrative commands
"""
import random
import time
import threading
import logging
import requests
import paramiko
from datetime import datetime

logger = logging.getLogger(__name__)


class TrafficNormalizer:
    """
    Generates realistic background traffic to honeypots.

    This makes network analysis difficult - attackers can't distinguish
    honeypot from real system based on traffic patterns alone.
    """

    def __init__(self, ssh_host, web_host, ssh_port=2222, web_port=80):
        """
        Initialize traffic normalizer.

        Args:
            ssh_host: SSH honeypot hostname/IP
            web_host: Web honeypot hostname/IP
            ssh_port: SSH port (default: 2222)
            web_port: Web port (default: 80)
        """
        self.ssh_host = ssh_host
        self.web_host = web_host
        self.ssh_port = ssh_port
        self.web_port = web_port
        self.running = False

        # Realistic command patterns
        self.admin_commands = [
            'uptime',
            'df -h',
            'free -m',
            'docker ps',
            'docker images',
            'netstat -tuln',
            'tail -n 20 /var/log/syslog',
            'ps aux | grep docker',
            'systemctl status nginx',
            'journalctl -u nginx -n 20',
            'cat /proc/cpuinfo | grep "model name"',
            'du -sh /var/log/*',
            'who',
            'last | head -10',
        ]

        self.web_endpoints = [
            '/api/v1/status',
            '/api/v1/health',
            '/api/v1/metrics',
            '/api/v1/version',
            '/',
            '/robots.txt',
            '/favicon.ico',
        ]

    def simulate_legitimate_ssh_sessions(self):
        """
        Simulate periodic legitimate SSH logins.

        Mimics DevOps/SRE checking system health.
        """
        logger.info("[TrafficNormalizer] Starting SSH session simulator")

        while self.running:
            try:
                # Realistic delay between administrative sessions (1-6 hours)
                delay_hours = random.uniform(1, 6)
                delay_seconds = delay_hours * 3600

                logger.debug(f"[SSH Simulator] Next session in {delay_hours:.1f} hours")
                time.sleep(delay_seconds)

                # Attempt SSH connection
                logger.info(f"[SSH Simulator] Initiating session to {self.ssh_host}:{self.ssh_port}")

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    # Try key-based auth (realistic)
                    ssh.connect(
                        self.ssh_host,
                        port=self.ssh_port,
                        username='ubuntu',
                        password='',  # Will fail, but that's realistic
                        timeout=10,
                        allow_agent=False,
                        look_for_keys=False
                    )
                except paramiko.AuthenticationException:
                    # Expected - we don't have valid credentials
                    # But this creates realistic failed auth attempts
                    logger.debug("[SSH Simulator] Auth failed (expected)")
                    continue
                except Exception as e:
                    logger.debug(f"[SSH Simulator] Connection failed: {e}")
                    continue

                # Execute realistic admin commands
                num_commands = random.randint(2, 5)
                selected_commands = random.sample(self.admin_commands, k=num_commands)

                for cmd in selected_commands:
                    try:
                        logger.debug(f"[SSH Simulator] Executing: {cmd}")
                        stdin, stdout, stderr = ssh.exec_command(cmd)

                        # Realistic delay between commands
                        time.sleep(random.uniform(2, 15))
                    except Exception as e:
                        logger.debug(f"[SSH Simulator] Command failed: {e}")
                        break

                # Close session
                ssh.close()
                logger.info("[SSH Simulator] Session completed")

            except Exception as e:
                logger.error(f"[SSH Simulator] Error: {e}")
                time.sleep(300)  # Wait 5 min on error

    def simulate_legitimate_web_traffic(self):
        """
        Simulate periodic legitimate web requests.

        Mimics health checks, monitoring systems, and normal API usage.
        """
        logger.info("[TrafficNormalizer] Starting web traffic simulator")

        while self.running:
            try:
                # Health checks are more frequent (1-10 minutes)
                delay_minutes = random.uniform(1, 10)
                delay_seconds = delay_minutes * 60

                time.sleep(delay_seconds)

                # Realistic user agents
                user_agents = [
                    'curl/7.68.0',  # Health check script
                    'python-requests/2.28.1',  # Monitoring tool
                    'Prometheus/2.37.0',  # Metrics collector
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',  # Browser
                    'Datadog Agent/7.40.1',  # APM
                ]

                ua = random.choice(user_agents)
                endpoint = random.choice(self.web_endpoints)

                try:
                    url = f'http://{self.web_host}:{self.web_port}{endpoint}'
                    logger.debug(f"[Web Simulator] GET {url}")

                    response = requests.get(
                        url,
                        headers={'User-Agent': ua},
                        timeout=10
                    )

                    logger.debug(f"[Web Simulator] Response: {response.status_code}")

                except requests.exceptions.RequestException as e:
                    logger.debug(f"[Web Simulator] Request failed: {e}")

            except Exception as e:
                logger.error(f"[Web Simulator] Error: {e}")
                time.sleep(60)

    def simulate_cron_jobs(self):
        """
        Simulate periodic cron job activity.

        Creates traffic that looks like automated backups, log rotation, etc.
        """
        logger.info("[TrafficNormalizer] Starting cron job simulator")

        while self.running:
            try:
                # Cron jobs run on schedule (every 30 minutes to 6 hours)
                delay_seconds = random.uniform(1800, 21600)
                time.sleep(delay_seconds)

                # Simulate cron job hitting API
                cron_endpoints = [
                    '/api/internal/backup-status',
                    '/api/internal/log-rotation',
                    '/api/internal/metrics-export',
                    '/health',
                ]

                endpoint = random.choice(cron_endpoints)

                try:
                    url = f'http://{self.web_host}:{self.web_port}{endpoint}'
                    logger.debug(f"[Cron Simulator] Automated job: {endpoint}")

                    requests.get(
                        url,
                        headers={'User-Agent': 'cron-job/internal'},
                        timeout=10
                    )

                except Exception as e:
                    logger.debug(f"[Cron Simulator] Job failed: {e}")

            except Exception as e:
                logger.error(f"[Cron Simulator] Error: {e}")
                time.sleep(300)

    def start(self):
        """Start all background traffic simulators."""
        if self.running:
            logger.warning("[TrafficNormalizer] Already running")
            return

        self.running = True

        # Start SSH session simulator
        ssh_thread = threading.Thread(
            target=self.simulate_legitimate_ssh_sessions,
            daemon=True,
            name="SSH-Normalizer"
        )
        ssh_thread.start()

        # Start web traffic simulator
        web_thread = threading.Thread(
            target=self.simulate_legitimate_web_traffic,
            daemon=True,
            name="Web-Normalizer"
        )
        web_thread.start()

        # Start cron job simulator
        cron_thread = threading.Thread(
            target=self.simulate_cron_jobs,
            daemon=True,
            name="Cron-Normalizer"
        )
        cron_thread.start()

        logger.info("=" * 60)
        logger.info("Traffic Normalizer STARTED")
        logger.info("Generating realistic background traffic to honeypots")
        logger.info("This masks honeypot nature and increases dwell time")
        logger.info("=" * 60)

    def stop(self):
        """Stop all background traffic."""
        self.running = False
        logger.info("[TrafficNormalizer] Stopping background traffic generation")


def start_traffic_normalizer_for_experiment(ec2_host):
    """
    Convenience function to start traffic normalizer for an experiment.

    Args:
        ec2_host: EC2 instance IP/hostname

    Returns:
        TrafficNormalizer instance (already started)
    """
    normalizer = TrafficNormalizer(
        ssh_host=ec2_host,
        web_host=ec2_host,
        ssh_port=2222,
        web_port=80
    )

    normalizer.start()

    return normalizer


if __name__ == "__main__":
    # Test the traffic normalizer
    import sys

    if len(sys.argv) < 2:
        print("Usage: python traffic_normalizer.py <target_host>")
        print("Example: python traffic_normalizer.py 1.2.3.4")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    target = sys.argv[1]
    normalizer = start_traffic_normalizer_for_experiment(target)

    print(f"Traffic normalizer running for {target}")
    print("Press Ctrl+C to stop...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        normalizer.stop()
        print("\nStopped")
