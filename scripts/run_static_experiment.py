"""
Static Baseline Experiment for DeceptiCloud

This script runs a control experiment with a fixed (non-adaptive) honeypot deployment.
Use this to generate baseline results for comparison with the adaptive DQN agent.

Usage:
    python scripts/run_static_experiment.py --honeypot ssh --episodes 5
    python scripts/run_static_experiment.py --honeypot web --episodes 5
"""
import time
import csv
import os
import argparse
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment import CloudHoneynetEnv
from src.attacker import run_attacker_thread
from src.aws_utils import get_instance_id_by_ip, upload_dir_to_s3
import numpy as np


def run_static_experiment(honeypot_type='ssh', episodes=5, timesteps_per_episode=24):
    """Run a static baseline experiment with fixed honeypot deployment.

    Args:
        honeypot_type: Type of honeypot to deploy ('ssh', 'web', or 'none')
        episodes: Number of episodes to run
        timesteps_per_episode: Number of timesteps per episode
    """
    # Configuration from environment variables
    EC2_HOST = os.environ.get('EC2_HOST') or "YOUR_EC2_IP_ADDRESS"
    EC2_USER = os.environ.get('EC2_USER') or "ubuntu"
    EC2_KEY_FILE = os.environ.get('EC2_KEY_FILE') or "path/to/your/key.pem"

    USE_SSM = os.environ.get('DECEPTICLOUD_USE_SSM', '0').lower() in ('1', 'true', 'yes')
    SSM_INSTANCE_ID = os.environ.get('DECEPTICLOUD_SSM_INSTANCE') or None
    AWS_REGION = os.environ.get('AWS_REGION') or None
    DRY_RUN = os.environ.get('DECEPTICLOUD_DRY_RUN', '0').lower() in ('1', 'true', 'yes')
    S3_BUCKET = os.environ.get('DECEPTICLOUD_RESULTS_BUCKET') or None

    # Results directory
    RESULTS_DIR = "results"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    summary_path = os.path.join(RESULTS_DIR, 'static_results_summary.csv')
    per_timestep_path = os.path.join(RESULTS_DIR, 'static_results_per_timestep.csv')

    # Map honeypot type to action
    honeypot_map = {
        'none': 0,
        'ssh': 1,
        'cowrie': 1,
        'web': 2,
        'nginx': 2
    }

    if honeypot_type.lower() not in honeypot_map:
        print(f"Error: Invalid honeypot type '{honeypot_type}'")
        print("Valid options: none, ssh, cowrie, web, nginx")
        return

    static_action = honeypot_map[honeypot_type.lower()]

    # Create CSV files
    if not os.path.exists(summary_path):
        with open(summary_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['episode', 'total_reward', 'honeypot_type', 'timestamp'])

    if not os.path.exists(per_timestep_path):
        with open(per_timestep_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['episode', 'timestep', 'action', 'reward', 'ssh_attack',
                           'web_attack', 'current_honeypot', 'timestamp'])

    print(f"=== Static Baseline Experiment ===")
    print(f"Honeypot type: {honeypot_type} (action={static_action})")
    print(f"Episodes: {episodes}")
    print(f"Timesteps per episode: {timesteps_per_episode}")
    print("=" * 40)

    # Initialize environment
    print("Initializing environment...")
    ssm_instance = SSM_INSTANCE_ID
    if USE_SSM and not SSM_INSTANCE_ID and EC2_HOST:
        print("Attempting to auto-detect EC2 instance id from public IP...")
        ssm_instance = get_instance_id_by_ip(AWS_REGION, EC2_HOST)
        if ssm_instance:
            print(f"Found instance id: {ssm_instance}")

    env = CloudHoneynetEnv(host=EC2_HOST, user=EC2_USER, key_file=EC2_KEY_FILE,
                          use_ssm=USE_SSM, ssm_instance_id=ssm_instance,
                          aws_region=AWS_REGION, dry_run=DRY_RUN)

    # Start attacker threads
    print("Starting attacker threads...")
    run_attacker_thread(EC2_HOST, EC2_USER, EC2_KEY_FILE)

    # Run episodes
    for e in range(episodes):
        state = env.reset()
        total_reward = 0

        for t in range(timesteps_per_episode):
            print(f"Episode {e+1}/{episodes}, Timestep {t+1}/{timesteps_per_episode}")

            # Always take the same action (static deployment)
            action = static_action
            next_state, reward, done = env.step(action)

            total_reward += reward
            time.sleep(1)

            # Log per-timestep
            with open(per_timestep_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([e+1, t+1, int(action), float(reward),
                               int(next_state[0]), int(next_state[1]), int(next_state[2]),
                               datetime.utcnow().isoformat()])

        print(f"Episode: {e+1}/{episodes}, Total Reward: {total_reward}")

        # Log episode summary
        with open(summary_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([e+1, float(total_reward), honeypot_type,
                           datetime.utcnow().isoformat()])

    print(f"\n=== Experiment Complete ===")
    print(f"Results saved to:")
    print(f"  - {summary_path}")
    print(f"  - {per_timestep_path}")

    # Upload to S3 if configured
    if S3_BUCKET:
        print(f"\nUploading results to S3...")
        try:
            uploaded = upload_dir_to_s3(S3_BUCKET, 'decepticloud_static_results',
                                       RESULTS_DIR, region=AWS_REGION)
            print(f"Uploaded {len(uploaded)} files to S3")
        except Exception as e:
            print(f"S3 upload failed: {e}")


def main():
    parser = argparse.ArgumentParser(description='Run static baseline experiment')
    parser.add_argument('--honeypot', type=str, default='ssh',
                       choices=['none', 'ssh', 'cowrie', 'web', 'nginx'],
                       help='Type of honeypot to deploy (default: ssh)')
    parser.add_argument('--episodes', type=int, default=5,
                       help='Number of episodes (default: 5)')
    parser.add_argument('--timesteps', type=int, default=24,
                       help='Timesteps per episode (default: 24)')

    args = parser.parse_args()

    run_static_experiment(
        honeypot_type=args.honeypot,
        episodes=args.episodes,
        timesteps_per_episode=args.timesteps
    )


if __name__ == "__main__":
    main()
