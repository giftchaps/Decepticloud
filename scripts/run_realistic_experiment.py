#!/usr/bin/env python3
"""
Realistic Experiment Runner for DeceptiCloud

Runs experiments with industry-standard attack frameworks to compare
RL adaptive honeypots vs static honeypots.

Usage:
    # Run mixed attack scenario for 4 hours
    python scripts/run_realistic_experiment.py --scenario mixed --duration 4

    # Run full experimental protocol (all scenarios, 3 repetitions)
    python scripts/run_realistic_experiment.py --full-protocol

    # Run specific attack with Stratus Red Team
    python scripts/run_realistic_experiment.py --stratus --scenario cloud_native
"""
import argparse
import sys
import os
import time
import yaml
import threading
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.advanced_attacker import run_realistic_attacker, MultiVectorAttacker
from src.environment import CloudHoneynetEnv
from src.agent import DQNAgent
from src.aws_utils import get_instance_id_by_ip, upload_dir_to_s3
import numpy as np
import csv


def load_attack_scenarios():
    """Load attack scenarios from config file."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config', 'attack_scenarios.yaml'
    )

    if not os.path.exists(config_path):
        print(f"Error: Config file not found: {config_path}")
        return None

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_adaptive_experiment_with_realistic_attacks(
    scenario_name: str,
    duration_hours: int,
    ec2_host: str,
    ec2_user: str,
    ec2_key_file: str,
    episodes: int = None
):
    """
    Run adaptive DQN experiment with realistic attack traffic.

    Args:
        scenario_name: Attack scenario from config
        duration_hours: How long to run
        ec2_host: EC2 honeypot host
        ec2_user: SSH username
        ec2_key_file: SSH key file
        episodes: Number of episodes (auto-calculated if None)
    """
    print("=" * 70)
    print(f"ADAPTIVE RL EXPERIMENT - Realistic Attacks")
    print(f"Scenario: {scenario_name}")
    print(f"Duration: {duration_hours} hours")
    print("=" * 70)

    # Load configuration
    configs = load_attack_scenarios()
    if not configs or scenario_name not in configs:
        print(f"Error: Unknown scenario '{scenario_name}'")
        return

    scenario_config = configs[scenario_name]

    # Auto-calculate episodes based on duration
    if episodes is None:
        timesteps_per_episode = 24
        total_timesteps = duration_hours * 60  # Assume 1 timestep = 1 minute
        episodes = max(1, total_timesteps // timesteps_per_episode)

    # Initialize environment and agent
    STATE_SIZE = 3
    ACTION_SIZE = 3
    BATCH_SIZE = 32

    USE_SSM = os.environ.get('DECEPTICLOUD_USE_SSM', '0').lower() in ('1', 'true', 'yes')
    SSM_INSTANCE_ID = os.environ.get('DECEPTICLOUD_SSM_INSTANCE') or None
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'

    # Results directory
    RESULTS_DIR = f"results/{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    summary_path = os.path.join(RESULTS_DIR, 'results_summary.csv')
    per_timestep_path = os.path.join(RESULTS_DIR, 'results_per_timestep.csv')

    # Create CSV files
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['episode', 'total_reward', 'epsilon', 'timestamp', 'scenario'])

    with open(per_timestep_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['episode', 'timestep', 'action', 'reward',
                        'ssh_attack', 'web_attack', 'current_honeypot', 'timestamp'])

    # Initialize environment
    print("\n[1/3] Initializing environment...")
    ssm_instance = SSM_INSTANCE_ID
    if USE_SSM and not SSM_INSTANCE_ID and ec2_host:
        ssm_instance = get_instance_id_by_ip(AWS_REGION, ec2_host)

    env = CloudHoneynetEnv(
        host=ec2_host, user=ec2_user, key_file=ec2_key_file,
        use_ssm=USE_SSM, ssm_instance_id=ssm_instance, aws_region=AWS_REGION
    )

    # Initialize agent
    agent = DQNAgent(state_size=STATE_SIZE, action_size=ACTION_SIZE)

    # Start realistic attacker thread
    print("\n[2/3] Starting realistic attack campaign...")
    attack_thread = threading.Thread(
        target=run_realistic_attacker,
        args=(ec2_host, scenario_name, duration_hours),
        daemon=True
    )
    attack_thread.start()

    # Give attackers time to start
    time.sleep(10)

    # Run experiment
    print(f"\n[3/3] Running {episodes} episodes with RL agent...")
    print("-" * 70)

    for e in range(episodes):
        state = env.reset()
        state = np.reshape(state, [STATE_SIZE])
        total_reward = 0

        timesteps = 24
        for t in range(timesteps):
            print(f"Episode {e+1}/{episodes}, Timestep {t+1}/{timesteps}")

            action = agent.act(state)
            next_state, reward, done = env.step(action)
            next_state = np.reshape(next_state, [STATE_SIZE])

            total_reward += reward
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            agent.learn(BATCH_SIZE)

            # Log per-timestep
            with open(per_timestep_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    e+1, t+1, int(action), float(reward),
                    int(next_state[0]), int(next_state[1]), int(next_state[2]),
                    datetime.utcnow().isoformat()
                ])

            time.sleep(60)  # 1 minute per timestep for realistic attacks

        print(f"✓ Episode {e+1} complete: Reward={total_reward:.2f}, Epsilon={agent.epsilon:.3f}")

        # Log summary
        with open(summary_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                e+1, float(total_reward), float(agent.epsilon),
                datetime.utcnow().isoformat(), scenario_name
            ])

    # Save model
    model_path = os.path.join(RESULTS_DIR, 'dqn_model.pth')
    agent.save(model_path)

    print("\n" + "=" * 70)
    print("EXPERIMENT COMPLETE")
    print(f"Results saved to: {RESULTS_DIR}")
    print("=" * 70)

    return RESULTS_DIR


def run_static_experiment_with_realistic_attacks(
    honeypot_type: str,
    scenario_name: str,
    duration_hours: int,
    ec2_host: str,
    ec2_user: str,
    ec2_key_file: str,
    episodes: int = None
):
    """
    Run static honeypot baseline with realistic attacks.

    Args:
        honeypot_type: 'ssh', 'web', or 'none'
        scenario_name: Attack scenario from config
        duration_hours: How long to run
        ec2_host: EC2 honeypot host
        ec2_user: SSH username
        ec2_key_file: SSH key file
        episodes: Number of episodes (auto-calculated if None)
    """
    print("=" * 70)
    print(f"STATIC BASELINE EXPERIMENT - Realistic Attacks")
    print(f"Honeypot Type: {honeypot_type.upper()}")
    print(f"Scenario: {scenario_name}")
    print(f"Duration: {duration_hours} hours")
    print("=" * 70)

    # Map honeypot type to action
    honeypot_map = {'none': 0, 'ssh': 1, 'cowrie': 1, 'web': 2, 'nginx': 2}
    if honeypot_type.lower() not in honeypot_map:
        print(f"Error: Invalid honeypot type '{honeypot_type}'")
        return

    static_action = honeypot_map[honeypot_type.lower()]

    # Auto-calculate episodes
    if episodes is None:
        timesteps_per_episode = 24
        total_timesteps = duration_hours * 60
        episodes = max(1, total_timesteps // timesteps_per_episode)

    # Initialize environment
    USE_SSM = os.environ.get('DECEPTICLOUD_USE_SSM', '0').lower() in ('1', 'true', 'yes')
    SSM_INSTANCE_ID = os.environ.get('DECEPTICLOUD_SSM_INSTANCE') or None
    AWS_REGION = os.environ.get('AWS_REGION') or 'us-east-1'

    # Results directory
    RESULTS_DIR = f"results/static_{honeypot_type}_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    summary_path = os.path.join(RESULTS_DIR, 'results_summary.csv')
    per_timestep_path = os.path.join(RESULTS_DIR, 'results_per_timestep.csv')

    # Create CSV files
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['episode', 'total_reward', 'honeypot_type', 'timestamp', 'scenario'])

    with open(per_timestep_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['episode', 'timestep', 'action', 'reward',
                        'ssh_attack', 'web_attack', 'current_honeypot', 'timestamp'])

    # Initialize environment
    print("\n[1/3] Initializing environment...")
    ssm_instance = SSM_INSTANCE_ID
    if USE_SSM and not SSM_INSTANCE_ID and ec2_host:
        ssm_instance = get_instance_id_by_ip(AWS_REGION, ec2_host)

    env = CloudHoneynetEnv(
        host=ec2_host, user=ec2_user, key_file=ec2_key_file,
        use_ssm=USE_SSM, ssm_instance_id=ssm_instance, aws_region=AWS_REGION
    )

    # Start realistic attacker
    print("\n[2/3] Starting realistic attack campaign...")
    attack_thread = threading.Thread(
        target=run_realistic_attacker,
        args=(ec2_host, scenario_name, duration_hours),
        daemon=True
    )
    attack_thread.start()
    time.sleep(10)

    # Run experiment
    print(f"\n[3/3] Running {episodes} episodes with static {honeypot_type} honeypot...")
    print("-" * 70)

    for e in range(episodes):
        state = env.reset()
        total_reward = 0

        timesteps = 24
        for t in range(timesteps):
            print(f"Episode {e+1}/{episodes}, Timestep {t+1}/{timesteps}")

            # Always take same action (static deployment)
            action = static_action
            next_state, reward, done = env.step(action)

            total_reward += reward

            # Log per-timestep
            with open(per_timestep_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    e+1, t+1, int(action), float(reward),
                    int(next_state[0]), int(next_state[1]), int(next_state[2]),
                    datetime.utcnow().isoformat()
                ])

            time.sleep(60)

        print(f"✓ Episode {e+1} complete: Reward={total_reward:.2f}")

        # Log summary
        with open(summary_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                e+1, float(total_reward), honeypot_type,
                datetime.utcnow().isoformat(), scenario_name
            ])

    print("\n" + "=" * 70)
    print("BASELINE EXPERIMENT COMPLETE")
    print(f"Results saved to: {RESULTS_DIR}")
    print("=" * 70)

    return RESULTS_DIR


def main():
    parser = argparse.ArgumentParser(
        description='Run DeceptiCloud experiments with realistic attack frameworks'
    )

    parser.add_argument('--scenario', type=str, default='mixed',
                       choices=['ssh_focused', 'web_focused', 'mixed', 'cloud_native',
                               'aggressive', 'stealthy'],
                       help='Attack scenario to run')

    parser.add_argument('--duration', type=int, default=4,
                       help='Duration in hours (default: 4)')

    parser.add_argument('--mode', type=str, default='adaptive',
                       choices=['adaptive', 'static'],
                       help='Experiment mode: adaptive RL or static baseline')

    parser.add_argument('--honeypot', type=str, default='ssh',
                       choices=['ssh', 'web', 'none'],
                       help='Honeypot type for static mode')

    parser.add_argument('--full-protocol', action='store_true',
                       help='Run full experimental protocol (all scenarios, 3 reps)')

    parser.add_argument('--stratus', action='store_true',
                       help='Use Stratus Red Team attacks (requires installation)')

    args = parser.parse_args()

    # Get EC2 configuration
    EC2_HOST = os.environ.get('EC2_HOST')
    EC2_USER = os.environ.get('EC2_USER', 'ubuntu')
    EC2_KEY_FILE = os.environ.get('EC2_KEY_FILE')

    if not EC2_HOST or not EC2_KEY_FILE:
        print("Error: Set EC2_HOST and EC2_KEY_FILE environment variables")
        print("Example:")
        print("  export EC2_HOST=1.2.3.4")
        print("  export EC2_KEY_FILE=/path/to/key.pem")
        sys.exit(1)

    if args.full_protocol:
        print("Running full experimental protocol...")
        print("This will take significant time. Consider running overnight.")
        # TODO: Implement full protocol runner
        print("Full protocol not yet implemented. Run individual scenarios for now.")
        sys.exit(0)

    # Run single experiment
    if args.mode == 'adaptive':
        run_adaptive_experiment_with_realistic_attacks(
            scenario_name=args.scenario,
            duration_hours=args.duration,
            ec2_host=EC2_HOST,
            ec2_user=EC2_USER,
            ec2_key_file=EC2_KEY_FILE
        )
    else:
        run_static_experiment_with_realistic_attacks(
            honeypot_type=args.honeypot,
            scenario_name=args.scenario,
            duration_hours=args.duration,
            ec2_host=EC2_HOST,
            ec2_user=EC2_USER,
            ec2_key_file=EC2_KEY_FILE
        )


if __name__ == "__main__":
    main()
