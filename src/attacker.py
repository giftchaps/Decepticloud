import paramiko
import time
import threading
import random


def attacker_loop(host, user, key_file):
    print(f"[Attacker] Starting attack thread against {host}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    passwords = ['123456', 'password', 'root', 'admin']

    while True:
        pw = random.choice(passwords)
        try:
            ssh.connect(hostname=host, port=2222, username='root', password=pw, timeout=5)
            ssh.close()
        except paramiko.AuthenticationException:
            print(f"[Attacker] Login failed for root@{pw} (as expected)")
        except Exception as e:
            print(f"[Attacker] Cannot connect to honeypot port 2222. Is it running? {e}")
        time.sleep(random.randint(5, 15))


def run_attacker_thread(host, user, key_file):
    t = threading.Thread(target=attacker_loop, args=(host, user, key_file), daemon=True)
    t.start()
