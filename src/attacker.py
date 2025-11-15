import paramiko
import time
import threading
import random
import requests


def ssh_attacker_loop(host, user, key_file):
    """Simulates SSH brute-force attacks against Cowrie honeypot."""
    print(f"[SSH Attacker] Starting SSH attack thread against {host}:2222")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    passwords = ['123456', 'password', 'root', 'admin']

    while True:
        pw = random.choice(passwords)
        try:
            ssh.connect(hostname=host, port=2222, username='root', password=pw, timeout=5)
            ssh.close()
        except paramiko.AuthenticationException:
            print(f"[SSH Attacker] Login attempt: root/{pw} (failed as expected)")
        except Exception as e:
            # Honeypot not running - silently continue
            pass
        time.sleep(random.randint(5, 15))


def web_attacker_loop(host):
    """Simulates web traffic/attacks against nginx honeypot."""
    print(f"[Web Attacker] Starting web attack thread against {host}:80")

    # Common web attack patterns and probes
    paths = [
        '/',
        '/admin',
        '/login',
        '/wp-admin',
        '/phpmyadmin',
        '/.env',
        '/config.php',
        '/backup.sql',
        '/../../../etc/passwd',
        '/api/users'
    ]

    user_agents = [
        'Mozilla/5.0 (compatible; Botnet/1.0)',
        'sqlmap/1.0',
        'Nmap Scripting Engine',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    ]

    while True:
        path = random.choice(paths)
        ua = random.choice(user_agents)
        try:
            url = f"http://{host}{path}"
            headers = {'User-Agent': ua}
            response = requests.get(url, headers=headers, timeout=5)
            print(f"[Web Attacker] GET {path} -> {response.status_code}")
        except requests.exceptions.RequestException:
            # Honeypot not running - silently continue
            pass
        time.sleep(random.randint(8, 20))


def run_attacker_thread(host, user, key_file):
    """Start both SSH and web attacker threads."""
    ssh_thread = threading.Thread(target=ssh_attacker_loop, args=(host, user, key_file), daemon=True)
    web_thread = threading.Thread(target=web_attacker_loop, args=(host,), daemon=True)

    ssh_thread.start()
    web_thread.start()
    print("[Attacker] Both SSH and web attack threads started")
