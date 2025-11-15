import numpy as np
import paramiko
import time
import json
import os
from . import utils
from .cloud_control import CloudCommandRunner

class CloudHoneynetEnv:
    def __init__(self, host, user, key_file, use_ssm=False, ssm_instance_id=None, aws_region=None, dry_run=False,
                 cowrie_log_path='/home/ubuntu/cowrie/var/log/cowrie/cowrie.json',
                 nginx_log_path='/var/log/nginx/access.log'):
        """Environment that controls honeypots on a cloud VM.

        Args:
            host: IP or hostname (used for SSH fallback)
            user: SSH username
            key_file: SSH key file path
            use_ssm: If True, use AWS SSM RunCommand to execute commands (preferred on AWS)
            ssm_instance_id: EC2 instance id to target via SSM (required if use_ssm=True)
            aws_region: AWS region for SSM client
            dry_run: If True, print commands without executing them
            cowrie_log_path: Path to Cowrie JSON logs on remote instance
            nginx_log_path: Path to nginx access logs on remote instance
        """
        self.host = host
        self.user = user
        self.key_file = key_file
        self.use_ssm = use_ssm
        self.ssm_instance_id = ssm_instance_id
        self.aws_region = aws_region
        self.cowrie_log_path = cowrie_log_path
        self.nginx_log_path = nginx_log_path

        self.ssh_client = None
        if not use_ssm:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.state_size = 3  # [ssh_attack_detected, web_attack_detected, current_honeypot]
        self.action_size = 3 # [0: None, 1: Cowrie, 2: Web]
        self.current_honeypot = 0 # 0 = None

        self.ssm_runner = None
        if use_ssm:
            if not ssm_instance_id:
                print("ERROR: use_ssm=True but no ssm_instance_id provided.")
            else:
                self.ssm_runner = CloudCommandRunner(region_name=aws_region)

        # Dry-run (do not execute remote commands, only print them)
        self.dry_run = bool(dry_run)

        # Attempt SSH connect if using SSH
        if not use_ssm and self.host:
            try:
                self.ssh_client.connect(hostname=self.host, username=self.user, key_filename=self.key_file)
                print("Successfully connected to EC2 instance via SSH.")
            except Exception as e:
                print(f"ERROR: Could not connect to EC2 instance via SSH. {e}")
                print("Please check your EC2_HOST, EC2_USER, and EC2_KEY_FILE variables in main.py")

    def _execute_command(self, cmd):
        """Execute a shell command either via SSM or SSH depending on configuration.

        Returns (stdout, stderr) strings.
        """
        # When dry-run is enabled, print the command and skip execution
        if self.dry_run:
            print(f"[DRY_RUN] Would execute: {cmd}")
            # Return empty output and no error to allow higher-level logic to continue
            return "", ""

        if self.use_ssm and self.ssm_runner:
            success, out, err = self.ssm_runner.run_command(self.ssm_instance_id, [cmd], timeout=60)
            if success:
                return out, ''
            return '', err

        # Fallback to SSH
        if not self.ssh_client:
            return None, 'no ssh client available'

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            return stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            print(f"Error executing SSH command: {e}")
            return None, str(e)

    def _get_state(self):
        print("Getting new state from EC2 instance...")

        # Check for SSH attacks (Cowrie logs)
        ssh_attack_detected = 0
        cmd = f"tail -n 20 {self.cowrie_log_path} 2>/dev/null || echo ''"
        log_data, err = self._execute_command(cmd)
        if log_data and log_data.strip():
            for line in log_data.strip().split('\n'):
                if line:
                    try:
                        log_entry = json.loads(line)
                        if log_entry.get('eventid') == 'cowrie.session.connect':
                            ssh_attack_detected = 1
                            break
                    except json.JSONDecodeError:
                        pass

        # Check for web attacks (nginx access logs)
        web_attack_detected = 0
        cmd = f"docker exec web_honeypot tail -n 20 {self.nginx_log_path} 2>/dev/null || echo ''"
        log_data, err = self._execute_command(cmd)
        if log_data and log_data.strip():
            # Any HTTP request in the last check indicates web traffic
            lines = [l for l in log_data.strip().split('\n') if l.strip()]
            if len(lines) > 0:
                web_attack_detected = 1

        return np.array([ssh_attack_detected, web_attack_detected, self.current_honeypot])

    def step(self, action):
        print(f"Executing action: {action}")
        if action == 0: # Do Nothing / Stop Honeypot
            self._execute_command("docker stop cowrie_honeypot || true")
            self._execute_command("docker stop web_honeypot || true")
            self.current_honeypot = 0
        elif action == 1: # Deploy Cowrie (SSH)
            self._execute_command("docker stop web_honeypot || true")
            self._execute_command("docker run -d --rm -p 2222:2222 --name cowrie_honeypot cowrie/cowrie")
            self.current_honeypot = 1
        elif action == 2: # Deploy Web Honeypot
            self._execute_command("docker stop cowrie_honeypot || true")
            self._execute_command("docker run -d --rm -p 80:80 --name web_honeypot nginx")
            self.current_honeypot = 2

        time.sleep(5)

        next_state = self._get_state()

        # Reward function
        reward = 0
        ssh_attack = int(next_state[0])
        web_attack = int(next_state[1])

        # Positive rewards for matching honeypot to attack type
        if ssh_attack == 1 and self.current_honeypot == 1:
            reward += 10  # SSH attack caught by Cowrie
        if web_attack == 1 and self.current_honeypot == 2:
            reward += 10  # Web attack caught by nginx

        # Small penalty for running honeypot without matching traffic (resource waste)
        if self.current_honeypot != 0:
            if self.current_honeypot == 1 and ssh_attack == 0:
                reward -= 1
            elif self.current_honeypot == 2 and web_attack == 0:
                reward -= 1

        # Small penalty for missing attacks (no honeypot deployed when attack occurs)
        if self.current_honeypot == 0 and (ssh_attack == 1 or web_attack == 1):
            reward -= 2

        done = False
        return next_state, reward, done

    def reset(self):
        print("Resetting environment (stopping all honeypots)...")
        self._execute_command("docker stop cowrie_honeypot || true")
        self._execute_command("docker stop web_honeypot || true")
        self.current_honeypot = 0
        return np.array([0, 0, self.current_honeypot])

    def __del__(self):
        try:
            print("Closing SSH connection.")
            if self.ssh_client:
                self.ssh_client.close()
        except Exception:
            pass
