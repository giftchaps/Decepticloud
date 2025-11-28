"""
Content Generator

Generates realistic fake content for directories, files, credentials, and command outputs
based on attacker interests and skill level.
"""

import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class ContentGenerator:
    """
    Generates convincing fake content tailored to attacker profile.
    """

    def __init__(self):
        self.fake_usernames = [
            'admin', 'root', 'ubuntu', 'ec2-user', 'deploy', 'jenkins',
            'gitlab', 'postgres', 'mysql', 'www-data', 'nginx', 'devops'
        ]

        self.fake_hostnames = [
            'prod-web-01', 'db-master', 'api-server', 'backup-node',
            'jenkins-ci', 'staging-app', 'log-aggregator', 'cache-redis'
        ]

        self.company_names = [
            'TechCorp', 'DataSystems', 'CloudServices', 'SecureNet',
            'FinanceGroup', 'HealthCare Inc', 'RetailChain', 'MediaWorks'
        ]

    def generate_directory_listing(self, path: str, interests: List[str],
                                   skill_level: str) -> str:
        """
        Generate fake directory listing output for 'ls' commands.

        Args:
            path: Directory path being listed
            interests: Attacker interests (credentials, financial, etc.)
            skill_level: Attacker skill level

        Returns:
            Fake ls -la output
        """
        entries = []

        # Always include basic entries
        entries.extend([
            'drwxr-xr-x 12 ubuntu ubuntu 4096 Nov 28 10:23 .',
            'drwxr-xr-x  3 root   root   4096 Nov 15 14:12 ..',
            '-rw------- 1 ubuntu ubuntu 2847 Nov 28 09:15 .bash_history',
            '-rw-r--r-- 1 ubuntu ubuntu  220 Nov 15 14:12 .bash_logout',
            '-rw-r--r-- 1 ubuntu ubuntu 3526 Nov 15 14:12 .bashrc',
            '-rw-r--r-- 1 ubuntu ubuntu  807 Nov 15 14:12 .profile',
        ])

        # Add interest-specific directories/files
        if 'credentials' in interests:
            entries.extend([
                'drwx------ 2 ubuntu ubuntu 4096 Nov 20 08:30 .ssh',
                'drwxr-xr-x 3 ubuntu ubuntu 4096 Nov 18 16:45 .aws',
                '-rw------- 1 ubuntu ubuntu  156 Nov 25 11:22 .mysql_history',
                'drwxr-xr-x 2 ubuntu ubuntu 4096 Nov 22 14:10 credentials',
            ])

        if 'financial' in interests:
            entries.extend([
                'drwxr-xr-x 4 ubuntu ubuntu 4096 Nov 27 09:00 payroll',
                'drwxr-xr-x 3 ubuntu ubuntu 4096 Nov 26 13:45 invoices',
                '-rw-r--r-- 1 ubuntu ubuntu 8192 Nov 28 08:00 transactions.db',
            ])

        if 'system_info' in interests or skill_level in ['advanced', 'expert']:
            entries.extend([
                'drwxr-xr-x 5 ubuntu ubuntu 4096 Nov 28 10:20 backups',
                'drwxr-xr-x 3 ubuntu ubuntu 4096 Nov 27 22:00 logs',
                '-rw-r--r-- 1 ubuntu ubuntu 1653 Nov 28 06:00 crontab.backup',
            ])

        # Add application-specific directories
        if path == '/home/ubuntu' or path == '~':
            entries.extend([
                'drwxr-xr-x 8 ubuntu ubuntu 4096 Nov 27 15:30 projects',
                'drwxr-xr-x 4 ubuntu ubuntu 4096 Nov 26 18:20 scripts',
                '-rw-r--r-- 1 ubuntu ubuntu  445 Nov 28 09:45 notes.txt',
            ])

        if path in ['/var', '/var/www', '/opt']:
            entries.extend([
                'drwxr-xr-x 6 www-data www-data 4096 Nov 28 07:15 app',
                'drwxr-xr-x 3 root     root     4096 Nov 27 23:30 config',
                '-rw-r--r-- 1 root     root      892 Nov 28 10:10 .env.backup',
            ])

        # Sort and return
        return '\n'.join(sorted(entries))

    def generate_file_content(self, filename: str, interests: List[str],
                             skill_level: str) -> str:
        """
        Generate fake file content based on filename and context.

        Args:
            filename: Name of file being read
            interests: Attacker interests
            skill_level: Attacker skill level

        Returns:
            Fake file contents
        """
        # Credentials files
        if '.env' in filename or 'credentials' in filename or 'secrets' in filename:
            return self._generate_env_file(skill_level)

        if 'id_rsa' in filename or 'private' in filename:
            return self._generate_ssh_key(skill_level)

        if 'password' in filename.lower() or 'passwd' in filename:
            return self._generate_password_file(skill_level)

        # Financial files
        if any(x in filename.lower() for x in ['payroll', 'invoice', 'transaction', 'payment']):
            return self._generate_financial_data(skill_level)

        # Configuration files
        if filename.endswith('.conf') or filename.endswith('.cfg') or filename.endswith('.ini'):
            return self._generate_config_file(filename, skill_level)

        # Database files
        if 'database' in filename.lower() or filename.endswith('.sql'):
            return self._generate_database_dump(skill_level)

        # Backup files
        if 'backup' in filename.lower() or filename.endswith('.bak'):
            return self._generate_backup_file(skill_level)

        # Log files
        if 'log' in filename.lower():
            return self._generate_log_file(filename, skill_level)

        # Script files
        if filename.endswith('.sh') or filename.endswith('.py'):
            return self._generate_script_file(filename, skill_level)

        # Default text file
        return self._generate_generic_text(filename, skill_level)

    def generate_find_results(self, search_term: str, interests: List[str],
                             skill_level: str) -> List[str]:
        """
        Generate fake find command results.

        Args:
            search_term: What the attacker is searching for
            interests: Attacker interests
            skill_level: Attacker skill level

        Returns:
            List of fake file paths
        """
        results = []

        # Credential-related searches
        if any(x in search_term.lower() for x in ['password', 'passwd', 'pwd', 'pass']):
            results.extend([
                '/home/ubuntu/.ssh/id_rsa',
                '/var/backups/.mysql_passwords',
                '/opt/app/config/database_passwords.txt',
                '/home/deploy/.password-store',
            ])

        if 'ssh' in search_term.lower() or 'id_rsa' in search_term.lower():
            results.extend([
                '/home/ubuntu/.ssh/id_rsa',
                '/home/admin/.ssh/id_rsa',
                '/root/.ssh/id_rsa',
                '/home/deploy/.ssh/authorized_keys',
            ])

        if '.env' in search_term.lower() or 'env' in search_term.lower():
            results.extend([
                '/var/www/app/.env',
                '/opt/application/.env.production',
                '/home/ubuntu/projects/api/.env.backup',
                '/var/backups/.env.old',
            ])

        if 'aws' in search_term.lower() or 'credentials' in search_term.lower():
            results.extend([
                '/home/ubuntu/.aws/credentials',
                '/root/.aws/credentials',
                '/home/jenkins/.aws/config',
            ])

        # Financial searches
        if any(x in search_term.lower() for x in ['payment', 'payroll', 'invoice', 'bank']):
            results.extend([
                '/var/data/payroll/november_2024.csv',
                '/home/finance/invoices_q4.xlsx',
                '/opt/billing/payment_records.db',
            ])

        # Database searches
        if any(x in search_term.lower() for x in ['database', '.db', 'sql', 'mysql', 'postgres']):
            results.extend([
                '/var/lib/mysql/production.sql',
                '/var/backups/database_dump.sql',
                '/opt/app/data/users.db',
            ])

        # Config searches
        if any(x in search_term.lower() for x in ['config', 'conf', '.cfg']):
            results.extend([
                '/etc/nginx/nginx.conf',
                '/opt/app/config/production.cfg',
                '/var/www/app/config/database.yml',
            ])

        # Backup searches
        if 'backup' in search_term.lower() or '.bak' in search_term.lower():
            results.extend([
                '/var/backups/system_backup.tar.gz',
                '/home/ubuntu/backup_credentials.txt',
                '/opt/backups/database_2024-11-27.sql',
            ])

        # Limit results based on skill level
        if skill_level == 'novice':
            return results[:3]
        elif skill_level == 'intermediate':
            return results[:5]
        else:
            return results

    def generate_grep_results(self, pattern: str, file_path: str,
                             interests: List[str], skill_level: str) -> str:
        """
        Generate fake grep results.

        Args:
            pattern: Search pattern
            file_path: File being searched (can be fake)
            interests: Attacker interests
            skill_level: Attacker skill level

        Returns:
            Fake grep output
        """
        results = []

        # Generate contextual matches
        if any(x in pattern.lower() for x in ['password', 'pass', 'pwd']):
            results.extend([
                f"{file_path}:12:DB_PASSWORD=S3cur3P@ssw0rd2024",
                f"{file_path}:34:ADMIN_PASSWORD=TempP@ss123!",
                f"{file_path}:67:# Old password: MyOldP@ss2023",
            ])

        if any(x in pattern.lower() for x in ['api', 'key', 'token']):
            results.extend([
                f"{file_path}:8:API_KEY=sk_live_51HxYz..." + self._generate_random_string(32),
                f"{file_path}:23:STRIPE_SECRET_KEY=sk_test_" + self._generate_random_string(40),
                f"{file_path}:45:JWT_SECRET=" + self._generate_random_string(64),
            ])

        if any(x in pattern.lower() for x in ['aws', 'access']):
            results.extend([
                f"{file_path}:15:AWS_ACCESS_KEY_ID=AKIA" + self._generate_random_string(16, chars=string.ascii_uppercase + string.digits),
                f"{file_path}:16:AWS_SECRET_ACCESS_KEY=" + self._generate_random_string(40),
            ])

        if 'database' in pattern.lower() or 'db' in pattern.lower():
            results.extend([
                f"{file_path}:29:DATABASE_URL=postgresql://user:pass@db-prod.internal:5432/maindb",
                f"{file_path}:30:REDIS_URL=redis://:password@cache.internal:6379/0",
            ])

        # Return appropriate number of results
        if skill_level == 'novice':
            return '\n'.join(results[:2])
        else:
            return '\n'.join(results)

    def generate_ps_output(self, skill_level: str) -> str:
        """Generate fake process listing."""
        processes = [
            'root         1  0.0  0.1  168976  11652 ?        Ss   Nov27   0:03 /sbin/init',
            'root        42  0.0  0.0  37352   3540 ?        S<s  Nov27   0:00 /lib/systemd/systemd-journald',
            'systemd+   543  0.0  0.0  90084   5432 ?        Ssl  Nov27   0:01 /lib/systemd/systemd-timesyncd',
            'root       782  0.0  0.1 283736   8964 ?        Ssl  Nov27   0:00 /usr/sbin/rsyslogd',
            'root       793  0.0  0.0  16764   2156 ?        Ss   Nov27   0:00 /usr/sbin/cron',
            'ubuntu    1234  0.0  0.3 758492  25368 ?        Ssl  09:15   0:12 /usr/bin/python3 /opt/app/main.py',
            'www-data  1567  0.0  0.2 345678  18234 ?        S    07:30   0:05 nginx: worker process',
            'mysql     1823  0.5  2.1 1876532 178956 ?       Ssl  Nov27   8:34 /usr/sbin/mysqld',
            'ubuntu    2134  0.0  0.1 245678  12345 ?        S    10:00   0:01 /usr/bin/redis-server',
        ]

        # Add suspicious but plausible processes for advanced users
        if skill_level in ['advanced', 'expert']:
            processes.extend([
                'root      3456  0.0  0.0  12345   2345 ?        S    08:45   0:00 /usr/sbin/backup_daemon',
                'ubuntu    4567  0.0  0.1  45678   8765 ?        S    09:30   0:00 python3 /home/ubuntu/scripts/sync_data.py',
            ])

        return '\n'.join(processes)

    def generate_netstat_output(self, skill_level: str) -> str:
        """Generate fake network connections."""
        connections = [
            'Active Internet connections (w/o servers)',
            'Proto Recv-Q Send-Q Local Address           Foreign Address         State      ',
            'tcp        0      0 10.0.1.42:22            203.0.113.45:54321     ESTABLISHED',
            'tcp        0      0 10.0.1.42:3306          10.0.1.15:45678        ESTABLISHED',
            'tcp        0      0 10.0.1.42:443           198.51.100.23:12345    ESTABLISHED',
            'tcp        0      0 10.0.1.42:80            198.51.100.67:54321    TIME_WAIT  ',
        ]

        # Add internal connections
        if skill_level in ['intermediate', 'advanced', 'expert']:
            connections.extend([
                'tcp        0      0 10.0.1.42:6379          10.0.1.20:34567        ESTABLISHED',
                'tcp        0      0 10.0.1.42:5432          10.0.1.18:23456        ESTABLISHED',
                'tcp        0      0 10.0.1.42:9200          10.0.1.22:45678        ESTABLISHED',
            ])

        return '\n'.join(connections)

    # Private helper methods for content generation

    def _generate_env_file(self, skill_level: str) -> str:
        """Generate fake .env file with credentials."""
        company = random.choice(self.company_names)

        content = [
            f"# {company} Production Environment",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "# Database Configuration",
            f"DB_HOST=db-prod-{random.randint(1, 5)}.internal",
            "DB_PORT=5432",
            f"DB_NAME={company.lower().replace(' ', '_')}_production",
            f"DB_USER=db_admin_{random.randint(100, 999)}",
            f"DB_PASSWORD={self._generate_password(skill_level)}",
            "",
            "# AWS Configuration",
            f"AWS_REGION=us-east-{random.randint(1, 2)}",
            f"AWS_ACCESS_KEY_ID=AKIA{self._generate_random_string(16, chars=string.ascii_uppercase + string.digits)}",
            f"AWS_SECRET_ACCESS_KEY={self._generate_random_string(40)}",
            f"S3_BUCKET={company.lower().replace(' ', '-')}-prod-data",
            "",
            "# API Keys",
            f"STRIPE_SECRET_KEY=sk_live_{self._generate_random_string(64)}",
            f"SENDGRID_API_KEY=SG.{self._generate_random_string(48)}",
            f"TWILIO_AUTH_TOKEN={self._generate_random_string(32)}",
            "",
            "# Redis Configuration",
            f"REDIS_HOST=cache-{random.randint(1, 3)}.internal",
            "REDIS_PORT=6379",
            f"REDIS_PASSWORD={self._generate_password(skill_level)}",
            "",
            "# Application Settings",
            f"APP_ENV=production",
            f"APP_DEBUG=false",
            f"APP_KEY=base64:{self._generate_random_string(32)}",
            f"JWT_SECRET={self._generate_random_string(64)}",
        ]

        return '\n'.join(content)

    def _generate_ssh_key(self, skill_level: str) -> str:
        """Generate fake SSH private key."""
        key_data = self._generate_random_string(1600, chars=string.ascii_letters + string.digits + '/+=')

        # Format as base64 blocks
        blocks = [key_data[i:i+64] for i in range(0, len(key_data), 64)]

        return f"""-----BEGIN RSA PRIVATE KEY-----
{chr(10).join(blocks[:25])}
-----END RSA PRIVATE KEY-----"""

    def _generate_password_file(self, skill_level: str) -> str:
        """Generate fake password file (like /etc/shadow format)."""
        users = []
        for username in self.fake_usernames[:8]:
            # Generate fake password hash
            salt = self._generate_random_string(8)
            hash_val = hashlib.sha512(salt.encode()).hexdigest()[:86]
            users.append(f"{username}:$6${salt}${hash_val}:19330:0:99999:7:::")

        return '\n'.join(users)

    def _generate_financial_data(self, skill_level: str) -> str:
        """Generate fake financial data."""
        data = [
            "Employee Payroll - November 2024",
            "=" * 60,
            "",
            "Employee ID | Name              | Department  | Salary",
            "-" * 60,
        ]

        names = ['John Smith', 'Jane Doe', 'Bob Johnson', 'Alice Williams',
                'Charlie Brown', 'Diana Prince', 'Eve Martinez', 'Frank Zhang']

        departments = ['Engineering', 'Finance', 'Marketing', 'Sales', 'HR']

        for i, name in enumerate(names[:6]):
            emp_id = f"EMP{1000 + i}"
            dept = random.choice(departments)
            salary = f"${random.randint(60000, 150000):,}"
            data.append(f"{emp_id:11} | {name:17} | {dept:11} | {salary}")

        data.extend([
            "",
            f"Total Payroll: ${random.randint(500000, 800000):,}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ])

        return '\n'.join(data)

    def _generate_config_file(self, filename: str, skill_level: str) -> str:
        """Generate fake configuration file."""
        if 'nginx' in filename or 'web' in filename:
            return f"""server {{
    listen 80;
    server_name prod-web.{random.choice(self.company_names).lower()}.com;

    root /var/www/app/public;
    index index.php index.html;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    location ~ \\.php$ {{
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
    }}
}}"""
        else:
            return f"""[database]
host = db-prod-1.internal
port = 5432
user = app_user
password = {self._generate_password(skill_level)}
database = production_db

[cache]
host = cache-1.internal
port = 6379
password = {self._generate_password(skill_level)}

[logging]
level = INFO
file = /var/log/app/production.log"""

    def _generate_database_dump(self, skill_level: str) -> str:
        """Generate fake database dump."""
        dump = [
            "-- MySQL dump 10.13  Distrib 8.0.35",
            f"-- Host: db-prod-1.internal    Database: production_db",
            f"-- Server version: 8.0.35",
            "",
            "-- Table structure for table `users`",
            "",
            "DROP TABLE IF EXISTS `users`;",
            "CREATE TABLE `users` (",
            "  `id` int NOT NULL AUTO_INCREMENT,",
            "  `username` varchar(50) NOT NULL,",
            "  `email` varchar(100) NOT NULL,",
            "  `password_hash` varchar(255) NOT NULL,",
            "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,",
            "  PRIMARY KEY (`id`)",
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;",
            "",
            "-- Dumping data for table `users`",
            "",
            "INSERT INTO `users` VALUES",
        ]

        # Add fake user records
        for i in range(5):
            username = random.choice(['admin', 'user', 'test']) + str(random.randint(1, 100))
            email = f"{username}@{random.choice(self.company_names).lower()}.com"
            password_hash = hashlib.sha256(self._generate_random_string(20).encode()).hexdigest()
            dump.append(f"({i+1}, '{username}', '{email}', '{password_hash}', '2024-11-{random.randint(1, 28):02d} 10:00:00')" + ("," if i < 4 else ";"))

        return '\n'.join(dump)

    def _generate_backup_file(self, skill_level: str) -> str:
        """Generate fake backup file content."""
        return f"""Backup Summary
==============
Date: {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')}
Type: Full System Backup
Status: Completed

Files backed up: {random.randint(50000, 100000)}
Size: {random.randint(10, 50)}GB
Duration: {random.randint(30, 90)} minutes

Backup Location: s3://{random.choice(self.company_names).lower()}-backups/prod-backup-{datetime.now().strftime('%Y%m%d')}.tar.gz

Credentials stored in: /var/backups/.backup_credentials
"""

    def _generate_log_file(self, filename: str, skill_level: str) -> str:
        """Generate fake log file entries."""
        logs = []
        base_time = datetime.now()

        for i in range(10):
            timestamp = (base_time - timedelta(minutes=i*5)).strftime('%Y-%m-%d %H:%M:%S')

            if 'auth' in filename.lower():
                logs.append(f"{timestamp} sshd[{random.randint(1000, 9999)}]: Accepted publickey for ubuntu from 10.0.1.{random.randint(1, 254)} port {random.randint(40000, 60000)}")
            elif 'nginx' in filename.lower() or 'access' in filename.lower():
                logs.append(f'10.0.1.{random.randint(1, 254)} - - [{timestamp}] "GET /api/v1/users HTTP/1.1" 200 {random.randint(100, 10000)}')
            else:
                logs.append(f"{timestamp} INFO: Application running normally - PID {random.randint(1000, 9999)}")

        return '\n'.join(logs)

    def _generate_script_file(self, filename: str, skill_level: str) -> str:
        """Generate fake script file."""
        if filename.endswith('.sh'):
            return f"""#!/bin/bash
# Backup script - DO NOT DELETE
# Created: {datetime.now().strftime('%Y-%m-%d')}

DB_HOST="db-prod-1.internal"
DB_USER="backup_user"
DB_PASS="{self._generate_password(skill_level)}"

echo "Starting backup at $(date)"
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASS production_db > /var/backups/db_$(date +%Y%m%d).sql
echo "Backup completed"
"""
        else:  # Python
            return f"""#!/usr/bin/env python3
\"\"\"
Data synchronization script
\"\"\"

import os
import psycopg2

DB_CONFIG = {{
    'host': 'db-prod-1.internal',
    'database': 'production_db',
    'user': 'sync_user',
    'password': '{self._generate_password(skill_level)}'
}}

def sync_data():
    conn = psycopg2.connect(**DB_CONFIG)
    # Sync logic here
    print("Data synchronized successfully")

if __name__ == '__main__':
    sync_data()
"""

    def _generate_generic_text(self, filename: str, skill_level: str) -> str:
        """Generate generic text file content."""
        return f"""Notes - {datetime.now().strftime('%Y-%m-%d')}
================================

TODO:
- Update database credentials for Q4
- Migrate data to new S3 bucket
- Review backup schedules
- Contact DevOps about prod access

Important servers:
- db-prod-1.internal (main database)
- cache-1.internal (Redis)
- app-server-{random.randint(1, 5)}.internal

Credentials stored in: /home/ubuntu/credentials/
"""

    def _generate_password(self, skill_level: str) -> str:
        """Generate realistic fake password based on skill level."""
        if skill_level == 'expert':
            # More realistic, complex passwords for expert attackers
            parts = [
                random.choice(['Secure', 'Prod', 'Admin', 'System']),
                random.choice(['Pass', 'Key', 'Auth']),
                str(random.randint(1000, 9999)),
                random.choice(['!', '@', '#', '$', '&'])
            ]
            return ''.join(parts)
        else:
            # Simpler passwords for less skilled attackers
            return random.choice([
                'Password123!',
                'Admin2024!',
                'TempP@ss123',
                'Secure@2024',
                'Prod!Pass99'
            ])

    def _generate_random_string(self, length: int,
                                chars: str = string.ascii_letters + string.digits) -> str:
        """Generate random string of specified length."""
        return ''.join(random.choices(chars, k=length))
