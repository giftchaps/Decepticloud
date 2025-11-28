import numpy as np
import paramiko
import time
import json
import os
from . import utils
from .cloud_control import CloudCommandRunner
from .local_honeypot_manager import LocalHoneypotManager
# from .monitoring import monitor  # Optional monitoring

class CloudHoneynetEnv:
    def __init__(self, host, user, key_file, use_ssm=False, ssm_instance_id=None, aws_region=None, dry_run=False):
        """Environment that controls honeypots on a cloud VM.

        Args:
            host: IP or hostname (used for SSH fallback)
            user: SSH username
            key_file: SSH key file path
            use_ssm: If True, use AWS SSM RunCommand to execute commands (preferred on AWS)
            ssm_instance_id: EC2 instance id to target via SSM (required if use_ssm=True)
            aws_region: AWS region for SSM client
        """
        self.host = host
        self.user = user
        self.key_file = key_file
        self.use_ssm = use_ssm
        self.ssm_instance_id = ssm_instance_id
        self.aws_region = aws_region

        self.ssh_client = None
        if not use_ssm:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.state_size = 4  # [attacker_detected, current_honeypot, attack_intensity, dwell_time]
        self.action_size = 3 # [0: None, 1: Cowrie, 2: Web]
        self.current_honeypot = 0 # 0 = None
        
        # Deception tracking for adaptive behavior
        self.attacker_history = []
        self.dwell_time = 0
        self.attack_intensity = 0
        self.last_attack_time = 0

        self.ssm_runner = None
        if use_ssm:
            if not ssm_instance_id:
                print("ERROR: use_ssm=True but no ssm_instance_id provided.")
            else:
                self.ssm_runner = CloudCommandRunner(region_name=aws_region)

        # Dry-run (do not execute remote commands, only print them)
        self.dry_run = bool(dry_run)
        
        # Initialize local honeypot manager for research validation
        self.honeypot_manager = LocalHoneypotManager()
        if self.host == 'localhost':
            print("[Environment] Using local honeypot manager for research validation")
            self.honeypot_manager.simulate_realistic_attacks(duration=600)  # 10 minutes of attacks

        # Attempt SSH connect if using SSH
        if not use_ssm and self.host:
            try:
                self.ssh_client.connect(
                    hostname=self.host, 
                    username=self.user, 
                    key_filename=self.key_file,
                    timeout=30,
                    banner_timeout=30,
                    auth_timeout=30,
                    look_for_keys=False,
                    allow_agent=False
                )
                print("Successfully connected to EC2 instance via SSH.")
            except Exception as e:
                print(f"ERROR: Could not connect to EC2 instance via SSH. {e}")
                print("Please check your EC2_HOST, EC2_USER, and EC2_KEY_FILE variables in main.py")
                self.ssh_client = None

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
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=30)
            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            return stdout_data, stderr_data
        except Exception as e:
            print(f"Error executing SSH command: {e}")
            return "", str(e)

    def _get_state(self):
        print("[Environment] Checking for attacker activity...")
        attacker_detected = 0
        attacker_details = {}
        
        # Use local honeypot manager for localhost
        if self.host == 'localhost' and hasattr(self, 'honeypot_manager'):
            attacker_detected = self.honeypot_manager.get_attack_detection_state()
            if attacker_detected:
                metrics = self.honeypot_manager.get_performance_metrics()
                print(f"[Environment] Attack detected! Total attacks: {metrics['total_attacks']}")
                attacker_details = {'detection_method': 'local_simulation', 'metrics': metrics}
            # Enhanced state for deception learning
            if attacker_detected:
                self.dwell_time += 1
                self.attack_intensity = min(10, self.attack_intensity + 1)
            else:
                self.attack_intensity = max(0, self.attack_intensity - 0.5)
            
            return np.array([attacker_detected, self.current_honeypot, self.attack_intensity, self.dwell_time])
        
        # Remote instance detection
        running_containers, _ = self._execute_command("docker ps --format '{{.Names}}'")
        if not running_containers:
            running_containers = ""
        
        # Check for SSH honeypot logs (Cowrie)
        if 'cowrie_honeypot' in running_containers:
            # Check Cowrie logs for recent connections with IP extraction
            log_cmd = "docker logs --tail 50 cowrie_honeypot 2>/dev/null | grep -i 'new connection' | tail -5"
            log_data, _ = self._execute_command(log_cmd)
            if log_data and log_data.strip():
                attacker_detected = 1
                print(f"[Environment] Attacker activity detected in SSH honeypot")
                
                # Extract attacker IP from logs
                ip_cmd = r"docker logs --tail 10 cowrie_honeypot 2>/dev/null | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | tail -1"
                attacker_ip, _ = self._execute_command(ip_cmd)
                attacker_ip = attacker_ip.strip() if attacker_ip else "unknown"
                
                attacker_details = {
                    'ip': attacker_ip,
                    'honeypot_type': 'ssh',
                    'log_sample': log_data.strip()[-200:]  # Last 200 chars
                }
                
                # Optional CloudWatch logging
                print(f"[CloudWatch] Attack detected from {attacker_ip} on SSH honeypot")
        
        # Check for web honeypot access logs
        elif 'web_honeypot' in running_containers:
            # Check nginx access logs for recent requests
            log_cmd = "docker logs --tail 20 web_honeypot 2>/dev/null | grep -E '(GET|POST)' | tail -3"
            log_data, _ = self._execute_command(log_cmd)
            if log_data and log_data.strip():
                attacker_detected = 1
                print(f"[Environment] Attacker activity detected in web honeypot")
                
                # Extract IP from nginx logs
                ip_cmd = r"docker logs --tail 10 web_honeypot 2>/dev/null | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | tail -1"
                attacker_ip, _ = self._execute_command(ip_cmd)
                attacker_ip = attacker_ip.strip() if attacker_ip else "unknown"
                
                attacker_details = {
                    'ip': attacker_ip,
                    'honeypot_type': 'web',
                    'log_sample': log_data.strip()[-200:]
                }
                
                # Optional CloudWatch logging
                print(f"[CloudWatch] Attack detected from {attacker_ip} on web honeypot")
        
        # Track attacker behavior for deception adaptation
        current_time = time.time()
        if attacker_detected:
            self.dwell_time += 1
            self.attack_intensity = min(10, self.attack_intensity + 1)
            self.last_attack_time = current_time
            
            # Log attacker behavior for research
            self.attacker_history.append({
                'timestamp': current_time,
                'honeypot_type': self.current_honeypot,
                'details': attacker_details
            })
            
            print(f"[Deception] Attacker engaged for {self.dwell_time} timesteps, intensity: {self.attack_intensity}")
        else:
            # Decay intensity when no attacker
            self.attack_intensity = max(0, self.attack_intensity - 0.5)
            
            # Reset dwell time if attacker has been gone too long
            if current_time - self.last_attack_time > 60:  # 1 minute
                self.dwell_time = 0
        
        return np.array([attacker_detected, self.current_honeypot, self.attack_intensity, self.dwell_time])

    def step(self, action):
        action_names = ['Stop Honeypots', 'Deploy SSH Honeypot', 'Deploy Web Honeypot']
        print(f"[RL Agent Decision] Action {action}: {action_names[action]}")
        
        # Store action for monitoring
        self.last_action = action
        
        # Use local honeypot manager for localhost, otherwise use remote commands
        if self.host == 'localhost' and hasattr(self, 'honeypot_manager'):
            self.honeypot_manager.deploy_honeypot(action)
            self.current_honeypot = action
        else:
            # Remote deployment commands
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

        # Adaptive timing for deception - avoid detection during transitions
        if attacker_detected:
            # Longer observation to maximize dwell time and learning
            time.sleep(12)  # Extended engagement period
            print(f"[Deception] Maintaining engagement with attacker...")
        else:
            # Quick setup when no attacker to be ready
            time.sleep(3)  # Setup time for honeypot deployment

        next_state = self._get_state()

        reward = 0
        attacker_detected = int(next_state[0])

        # Deceptive reward structure - maximize dwell time and learning
        if attacker_detected == 1:
            if self.current_honeypot == 1:  # SSH honeypot engaging attacker
                reward = 15  # High reward for successful deception
                print(f"[Environment] REWARD +15: SSH honeypot successfully deceiving attacker")
            elif self.current_honeypot == 2:  # Web honeypot engaging attacker
                reward = 12  # Good reward for web deception
                print(f"[Environment] REWARD +12: Web honeypot successfully deceiving attacker")
            else:
                reward = -10  # Heavy penalty for missing deception opportunity
                print(f"[Environment] REWARD -10: Attacker present but no deception active")
        else:
            if self.current_honeypot != 0:
                reward = -2  # Small penalty for running without attacker
                print(f"[Environment] REWARD -2: Honeypot idle (waiting for attacker)")
            else:
                reward = -1  # Penalty for not being ready
                print(f"[Environment] REWARD -1: No deception ready")
        
        # Optional CloudWatch metrics
        action_names = ['none', 'ssh', 'web']
        print(f"[CloudWatch] Reward: {reward}, Action: {action_names[action] if action < len(action_names) else 'unknown'}")

        done = False
        return next_state, reward, done

    def reset(self):
        print("Resetting environment (stopping all honeypots)...")
        self._execute_command("docker stop cowrie_honeypot || true")
        self._execute_command("docker stop web_honeypot || true")
        self.current_honeypot = 0
        
        # Reset deception tracking
        self.attacker_history = []
        self.dwell_time = 0
        self.attack_intensity = 0
        self.last_attack_time = 0
        
        return np.array([0, self.current_honeypot, 0, 0])

    def __del__(self):
        try:
            print("Closing SSH connection.")
            if self.ssh_client:
                self.ssh_client.close()
        except Exception:
            pass
