"""
Local Honeypot Manager for DeceptiCloud Research
Manages Docker honeypots and simulates attack detection for research validation
"""
import requests
import socket
import time
import random
import threading
from datetime import datetime

class LocalHoneypotManager:
    def __init__(self):
        self.current_honeypot = 0  # 0=none, 1=ssh, 2=web
        self.attack_log = []
        self.ssh_port = 2222
        self.web_port = 80
        
    def deploy_honeypot(self, honeypot_type):
        """Deploy specified honeypot type"""
        print(f"[HoneypotManager] Deploying honeypot type: {honeypot_type}")
        self.current_honeypot = honeypot_type
        
        if honeypot_type == 1:
            print("[HoneypotManager] SSH Honeypot (Cowrie) active on port 2222")
        elif honeypot_type == 2:
            print("[HoneypotManager] Web Honeypot active on port 80")
        else:
            print("[HoneypotManager] All honeypots stopped")
    
    def check_ssh_honeypot(self):
        """Check if SSH honeypot is accessible and has recent activity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', self.ssh_port))
            sock.close()
            
            if result == 0:
                # Check for recent SSH attacks in logs
                recent_attacks = [a for a in self.attack_log 
                                if a['type'] == 'ssh' and 
                                (datetime.now() - a['timestamp']).seconds < 30]
                return len(recent_attacks) > 0
        except:
            pass
        return False
    
    def check_web_honeypot(self):
        """Check if web honeypot is accessible and has recent activity"""
        try:
            response = requests.get(f'http://localhost:{self.web_port}', timeout=2)
            if response.status_code == 200:
                # Check for recent web attacks
                recent_attacks = [a for a in self.attack_log 
                                if a['type'] == 'web' and 
                                (datetime.now() - a['timestamp']).seconds < 30]
                return len(recent_attacks) > 0
        except:
            pass
        return False
    
    def log_attack(self, attack_type, source_ip, details):
        """Log detected attack for research analysis"""
        attack_record = {
            'type': attack_type,
            'source_ip': source_ip,
            'details': details,
            'timestamp': datetime.now(),
            'honeypot_active': self.current_honeypot
        }
        self.attack_log.append(attack_record)
        print(f"[HoneypotManager] Attack logged: {attack_type} from {source_ip}")
    
    def get_attack_detection_state(self):
        """Get current attack detection state for RL agent"""
        if self.current_honeypot == 1:
            return 1 if self.check_ssh_honeypot() else 0
        elif self.current_honeypot == 2:
            return 1 if self.check_web_honeypot() else 0
        else:
            return 0
    
    def simulate_realistic_attacks(self, duration=300):
        """Simulate realistic attack patterns for research validation"""
        def attack_thread():
            attack_patterns = [
                {'type': 'web', 'frequency': 0.3, 'burst': True},
                {'type': 'ssh', 'frequency': 0.2, 'burst': False}
            ]
            
            end_time = time.time() + duration
            while time.time() < end_time:
                for pattern in attack_patterns:
                    if random.random() < pattern['frequency']:
                        if pattern['type'] == 'web':
                            self._simulate_web_attack()
                        elif pattern['type'] == 'ssh':
                            self._simulate_ssh_attack()
                
                time.sleep(random.uniform(2, 8))
        
        thread = threading.Thread(target=attack_thread, daemon=True)
        thread.start()
        print("[HoneypotManager] Realistic attack simulation started")
    
    def _simulate_web_attack(self):
        """Simulate web-based attacks"""
        try:
            usernames = ['admin', 'root', 'administrator', 'user']
            passwords = ['password', '123456', 'admin', 'root', 'password123']
            
            data = {
                'username': random.choice(usernames),
                'password': random.choice(passwords)
            }
            
            response = requests.post(f'http://localhost:{self.web_port}/login', 
                                   data=data, timeout=5)
            
            self.log_attack('web', '192.168.1.' + str(random.randint(100, 200)), 
                          f"Login attempt: {data['username']}/{data['password']}")
            
        except Exception as e:
            pass
    
    def _simulate_ssh_attack(self):
        """Simulate SSH-based attacks"""
        try:
            # Just log the attack attempt (SSH honeypot simulation)
            usernames = ['root', 'admin', 'ubuntu', 'user']
            self.log_attack('ssh', '10.0.0.' + str(random.randint(50, 150)), 
                          f"SSH brute force attempt: {random.choice(usernames)}")
        except Exception as e:
            pass
    
    def get_performance_metrics(self):
        """Get performance metrics for research analysis"""
        total_attacks = len(self.attack_log)
        web_attacks = len([a for a in self.attack_log if a['type'] == 'web'])
        ssh_attacks = len([a for a in self.attack_log if a['type'] == 'ssh'])
        
        # Calculate detection effectiveness
        detected_attacks = len([a for a in self.attack_log if a['honeypot_active'] > 0])
        detection_rate = detected_attacks / max(1, total_attacks)
        
        return {
            'total_attacks': total_attacks,
            'web_attacks': web_attacks,
            'ssh_attacks': ssh_attacks,
            'detection_rate': detection_rate,
            'unique_ips': len(set(a['source_ip'] for a in self.attack_log))
        }