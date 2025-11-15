"""
Smoke-check utility for DeceptiCloud

This script checks whether the target EC2 instance is reachable and can run
Docker commands. It supports two modes:
 - SSM mode: uses AWS SSM RunCommand to execute commands remotely (recommended).
 - SSH mode: uses Paramiko to SSH to the instance and run commands.

Usage (examples):
  python .\scripts\smoke_check.py --host 1.2.3.4 --user ubuntu --key C:\path\key.pem
  python .\scripts\smoke_check.py --use-ssm --ssm-instance-id i-0123456789abcdef --region us-east-1

The script prints PASS/FAIL messages and returns non-zero exit code on failure.
"""
import argparse
import sys
import time
import json

# Local imports from repo
try:
    from src.cloud_control import CloudCommandRunner
except Exception:
    CloudCommandRunner = None

try:
    import paramiko
except Exception:
    paramiko = None


def run_via_ssm(instance_id, region):
    if CloudCommandRunner is None:
        print("ERROR: boto3/CloudCommandRunner not available. Ensure requirements installed.")
        return False

    runner = CloudCommandRunner(region_name=region)

    checks = [
        ('docker status', 'sudo systemctl is-active docker || echo INACTIVE'),
        ('docker version', 'docker --version || true'),
        # A conservative docker test: list containers
        ('docker ps', 'docker ps --no-trunc --format "{{.ID}} {{.Image}}" || true')
    ]

    all_ok = True
    for name, cmd in checks:
        print(f"[SSM] Running check: {name}")
        success, out, err = runner.run_command(instance_id, [cmd], timeout=30)
        if not success:
            print(f"[SSM] {name} FAILED: {err}")
            all_ok = False
        else:
            print(f"[SSM] {name} output:\n{out.strip()}\n")
    return all_ok


def run_via_ssh(host, user, key_file):
    if paramiko is None:
        print("ERROR: paramiko not available. Ensure requirements installed.")
        return False

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, username=user, key_filename=key_file, timeout=10)
    except Exception as e:
        print(f"SSH connect failed: {e}")
        return False

    checks = [
        ('docker status', 'sudo systemctl is-active docker || echo INACTIVE'),
        ('docker version', 'docker --version || true'),
        ('docker ps', 'docker ps --no-trunc --format "{{.ID}} {{.Image}}" || true')
    ]

    all_ok = True
    for name, cmd in checks:
        print(f"[SSH] Running check: {name}")
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode()
            err = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()
            print(f"[SSH] {name} exit={exit_status} out:\n{out.strip()}\nerr:\n{err.strip()}\n")
            if exit_status != 0 and 'INACTIVE' in out:
                print(f"[SSH] {name} indicates Docker not active")
                all_ok = False
        except Exception as e:
            print(f"[SSH] {name} failed: {e}")
            all_ok = False

    try:
        ssh.close()
    except Exception:
        pass
    return all_ok


def main():
    parser = argparse.ArgumentParser(description='DeceptiCloud smoke-check')
    parser.add_argument('--use-ssm', action='store_true', help='Use AWS SSM RunCommand instead of SSH')
    parser.add_argument('--region', help='AWS region (for SSM)')
    parser.add_argument('--ssm-instance-id', help='EC2 instance id (i-...) for SSM mode')
    parser.add_argument('--host', help='EC2 public IP or hostname (for SSH mode)')
    parser.add_argument('--user', default='ubuntu', help='SSH username')
    parser.add_argument('--key', help='Path to SSH private key (.pem)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run: print actions only')

    args = parser.parse_args()

    dry = args.dry_run
    if args.use_ssm:
        if dry:
            print("Dry-run: would run SSM checks on instance id:", args.ssm_instance_id)
            print("Commands: sudo systemctl is-active docker; docker --version; docker ps")
            sys.exit(0)
        if not args.ssm_instance_id:
            print("ERROR: --ssm-instance-id is required when --use-ssm is set")
            sys.exit(2)
        ok = run_via_ssm(args.ssm_instance_id, args.region)
    else:
        if dry:
            print("Dry-run: would SSH to host", args.host, "user", args.user, "key", args.key)
            print("Commands: sudo systemctl is-active docker; docker --version; docker ps")
            sys.exit(0)
        if not args.host or not args.key:
            print("ERROR: --host and --key are required for SSH mode")
            sys.exit(2)
        ok = run_via_ssh(args.host, args.user, args.key)

    if ok:
        print("SMOKE CHECK: PASS")
        sys.exit(0)
    else:
        print("SMOKE CHECK: FAIL")
        sys.exit(3)


if __name__ == '__main__':
    main()
