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
            ssh.connect(
                hostname=host, 
                port=2222, 
                username='root', 
                password=pw, 
                timeout=5,
                banner_timeout=5,
                auth_timeout=5,
                look_for_keys=False,
                allow_agent=False
            )
            ssh.close()
        except paramiko.AuthenticationException:
            print(f"[Attacker] Login failed for root@{pw} (as expected)")
        except Exception as e:
            print(f"[Attacker] Cannot connect to honeypot port 2222. Is it running? {e}")
            time.sleep(5)  # Wait before retrying on connection errors
        time.sleep(random.randint(5, 15))


def run_attacker_thread(host, user, key_file):
    t = threading.Thread(target=attacker_loop, args=(host, user, key_file), daemon=True)
    t.start()
