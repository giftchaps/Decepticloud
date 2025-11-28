#!/usr/bin/env python3
"""
Adaptive Deception Engine for DeceptiCloud

Creates convincing fake content based on attacker behavior patterns.
Generates breadcrumbs that increase dwell time and gather intelligence.
"""

import random
import time
import json
from datetime import datetime, timedelta

class AdaptiveDeceptionEngine:
    def __init__(self):
        self.attacker_profile = {
            'commands_used': [],
            'directories_searched': [],
            'files_accessed': [],
            'behavior_pattern': 'reconnaissance',  # reconnaissance, exploitation, persistence
            'skill_level': 'novice',  # novice, intermediate, advanced
            'interests': []  # financial, personal, system, credentials
        }
        
        # Fake content templates
        self.fake_files = {
            'financial': [
                'bank_accounts.xlsx', 'payroll_2024.csv', 'tax_returns.pdf',
                'crypto_wallets.txt', 'investment_portfolio.xlsx'
            ],
            'credentials': [
                'passwords.txt', 'ssh_keys.pem', 'database_creds.json',
                'admin_accounts.csv', 'service_tokens.txt'
            ],
            'personal': [
                'employee_records.db', 'customer_data.csv', 'personal_info.xlsx',
                'contact_list.txt', 'email_archive.pst'
            ],
            'system': [
                'backup_scripts.sh', 'config_files.tar.gz', 'system_logs.zip',
                'network_topology.png', 'server_inventory.xlsx'
            ]
        }
        
        self.fake_directories = {
            'financial': ['accounting', 'finance', 'payroll', 'invoices'],
            'credentials': ['keys', 'auth', 'credentials', 'secrets'],
            'personal': ['hr', 'employees', 'customers', 'contacts'],
            'system': ['backups', 'configs', 'logs', 'scripts']
        }
        
        print("[Deception] Adaptive deception engine initialized")
    
    def analyze_attacker_behavior(self, command, output=""):
        """Analyze attacker command to update behavioral profile"""
        cmd = command.lower().strip()
        self.attacker_profile['commands_used'].append(cmd)
        
        # Detect interests based on commands
        if any(term in cmd for term in ['password', 'passwd', 'cred', 'key', 'token']):
            if 'credentials' not in self.attacker_profile['interests']:
                self.attacker_profile['interests'].append('credentials')
        
        if any(term in cmd for term in ['bank', 'money', 'pay', 'finance', 'account']):
            if 'financial' not in self.attacker_profile['interests']:
                self.attacker_profile['interests'].append('financial')
        
        if any(term in cmd for term in ['user', 'employee', 'customer', 'personal']):
            if 'personal' not in self.attacker_profile['interests']:
                self.attacker_profile['interests'].append('personal')
        
        if any(term in cmd for term in ['config', 'backup', 'log', 'system', 'network']):
            if 'system' not in self.attacker_profile['interests']:
                self.attacker_profile['interests'].append('system')
        
        # Update behavior pattern
        if len(self.attacker_profile['commands_used']) > 10:
            if any(cmd.startswith(adv) for adv in ['wget', 'curl', 'nc', 'python', 'perl']):
                self.attacker_profile['behavior_pattern'] = 'exploitation'
                self.attacker_profile['skill_level'] = 'advanced'
            elif any(cmd.startswith(inter) for inter in ['find', 'grep', 'cat', 'head', 'tail']):
                self.attacker_profile['behavior_pattern'] = 'reconnaissance'
                self.attacker_profile['skill_level'] = 'intermediate'
        
        print(f"[Deception] Analyzed command: {cmd}")
        print(f"[Deception] Interests: {self.attacker_profile['interests']}")
        print(f"[Deception] Pattern: {self.attacker_profile['behavior_pattern']}")
    
    def generate_fake_directory_listing(self, directory=""):
        """Generate convincing fake directory contents"""
        dir_name = directory.lower()
        
        # Determine what type of content to show based on attacker interests
        content_types = self.attacker_profile['interests'] if self.attacker_profile['interests'] else ['system']
        
        fake_items = []
        
        # Add some realistic system directories
        if not directory or directory == "/":
            fake_items.extend(['home', 'var', 'etc', 'tmp', 'opt'])
        
        # Add targeted fake content based on attacker interests
        for content_type in content_types[:2]:  # Limit to 2 types to avoid suspicion
            # Add fake directories
            fake_dirs = random.sample(self.fake_directories[content_type], 
                                    min(2, len(self.fake_directories[content_type])))
            fake_items.extend(fake_dirs)
            
            # Add fake files
            fake_files = random.sample(self.fake_files[content_type], 
                                     min(3, len(self.fake_files[content_type])))
            fake_items.extend(fake_files)
        
        # Add some realistic system files
        fake_items.extend(['.bashrc', '.profile', 'README.txt'])
        
        # Shuffle to make it look natural
        random.shuffle(fake_items)
        
        print(f"[Deception] Generated fake listing for '{directory}': {len(fake_items)} items")
        return fake_items
    
    def generate_fake_file_content(self, filename):
        """Generate convincing fake file content"""
        fname = filename.lower()
        
        if 'password' in fname or 'cred' in fname:
            return self._generate_fake_credentials()
        elif 'bank' in fname or 'account' in fname:
            return self._generate_fake_financial()
        elif 'employee' in fname or 'user' in fname:
            return self._generate_fake_personal()
        elif 'config' in fname or 'backup' in fname:
            return self._generate_fake_system()
        else:
            return self._generate_generic_fake_content(filename)
    
    def _generate_fake_credentials(self):
        """Generate fake credential data"""
        fake_creds = [
            "# Database Credentials",
            "db_user=admin_prod",
            "db_pass=Tr0ub4dor&3_2024",
            "db_host=192.168.1.100",
            "",
            "# SSH Keys",
            "ssh_key=/home/admin/.ssh/id_rsa_backup",
            "ssh_user=root",
            "",
            "# API Tokens",
            "api_token=sk-1234567890abcdef",
            "service_key=AIzaSyD1234567890"
        ]
        return "\n".join(fake_creds)
    
    def _generate_fake_financial(self):
        """Generate fake financial data"""
        fake_data = [
            "Account,Balance,Type",
            "4532-****-****-1234,$45,230.50,Checking",
            "4532-****-****-5678,$12,890.75,Savings",
            "5555-****-****-9999,$8,450.00,Credit",
            "",
            "Crypto Wallets:",
            "BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "ETH: 0x742d35Cc6634C0532925a3b8D4C0532925a3b8D4"
        ]
        return "\n".join(fake_data)
    
    def _generate_fake_personal(self):
        """Generate fake personal data"""
        fake_data = [
            "Employee ID,Name,Department,Salary",
            "E001,John Smith,IT,$75000",
            "E002,Sarah Johnson,Finance,$68000",
            "E003,Mike Wilson,HR,$62000",
            "",
            "Customer Records:",
            "C001,Alice Brown,alice@email.com,555-0123",
            "C002,Bob Davis,bob@email.com,555-0456"
        ]
        return "\n".join(fake_data)
    
    def _generate_fake_system(self):
        """Generate fake system configuration"""
        fake_data = [
            "# System Configuration",
            "server_ip=10.0.1.50",
            "backup_location=/mnt/backup/daily",
            "admin_email=admin@company.com",
            "",
            "# Network Settings",
            "gateway=192.168.1.1",
            "dns_primary=8.8.8.8",
            "dns_secondary=8.8.4.4",
            "",
            "# Last backup: " + (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        ]
        return "\n".join(fake_data)
    
    def _generate_generic_fake_content(self, filename):
        """Generate generic fake content"""
        return f"# {filename}\n# Created: {datetime.now().strftime('%Y-%m-%d')}\n# This file contains important data\n\nContent placeholder for {filename}"
    
    def should_show_fake_content(self, command):
        """Decide whether to show fake content based on attacker behavior"""
        cmd = command.lower()
        
        # Always show fake content for file/directory exploration
        if any(term in cmd for term in ['ls', 'dir', 'cat', 'head', 'tail', 'find', 'grep']):
            return True
        
        # Show fake content based on skill level and interests
        if self.attacker_profile['skill_level'] == 'advanced' and len(self.attacker_profile['interests']) > 2:
            return random.random() > 0.3  # 70% chance for advanced attackers
        elif self.attacker_profile['skill_level'] == 'intermediate':
            return random.random() > 0.5  # 50% chance for intermediate
        else:
            return random.random() > 0.7  # 30% chance for novice
    
    def get_deception_metrics(self):
        """Get current deception effectiveness metrics"""
        return {
            'commands_analyzed': len(self.attacker_profile['commands_used']),
            'interests_identified': len(self.attacker_profile['interests']),
            'behavior_pattern': self.attacker_profile['behavior_pattern'],
            'skill_level': self.attacker_profile['skill_level'],
            'deception_effectiveness': min(100, len(self.attacker_profile['commands_used']) * 5)
        }

# Global deception engine instance
deception_engine = AdaptiveDeceptionEngine()