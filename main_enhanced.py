#!/usr/bin/env python3
"""
Enhanced DeceptiCloud Main Runner with Adaptive Deception

This is the main entry point for running DeceptiCloud with the enhanced deception system.
It supports both local testing and AWS deployment.
"""

import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.agent import DQNAgent
from src.enhanced_environment import EnhancedCloudHoneynetEnv
from src.attacker import BasicAttacker


def print_banner():
    """Print DeceptiCloud banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║   DeceptiCloud - Enhanced Adaptive Honeypot System       ║
    ║   With Intelligent Deception & RL-Based Management       ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def train_enhanced_local(num_episodes=10, timesteps_per_episode=20):
    """
    Train the enhanced RL agent locally with deception.

    Args:
        num_episodes: Number of training episodes
        timesteps_per_episode: Timesteps per episode
    """
    print_banner()
    print("\n[MODE] Local Training with Enhanced Deception")
    print("=" * 60)

    # Import local environment
    from src.local_environment import LocalHoneynetEnv

    # Initialize environment with deception
    print("\n[Setup] Initializing enhanced environment...")
    env = LocalHoneynetEnv(
        docker_compose_file='./docker-compose.local.yml',
        deception_enabled=True,
        deception_data_dir='./data/deception'
    )

    # Initialize agent with enhanced state size
    print("[Setup] Initializing RL agent...")
    agent = DQNAgent(state_size=5, action_size=3)  # Enhanced state includes deception metrics

    # Initialize attacker
    print("[Setup] Initializing attacker simulator...")
    attacker = BasicAttacker(
        ssh_host='localhost',
        ssh_port=2222,
        ssh_user='root',
        ssh_password='123456',
        web_url='http://localhost:8080'
    )

    # Create results directory
    results_dir = Path('./results')
    results_dir.mkdir(exist_ok=True)

    # Training loop
    print(f"\n[Training] Starting {num_episodes} episodes...")
    print("=" * 60)

    all_episode_results = []
    all_timestep_results = []

    for episode in range(1, num_episodes + 1):
        state = env.reset()
        total_reward = 0
        total_deception_reward = 0

        print(f"\n--- Episode {episode}/{num_episodes} ---")

        for timestep in range(1, timesteps_per_episode + 1):
            # Agent chooses action
            action = agent.act(state)

            # Execute action in environment
            next_state, reward, done = env.step(action)

            # Extract deception reward component
            deception_component = next_state[4] * 5  # Engagement score contribution

            # Remember and learn
            agent.remember(state, action, reward, next_state, done)
            agent.replay(batch_size=32)

            # Track rewards
            total_reward += reward
            total_deception_reward += deception_component

            # Simulate attacker activity
            if action == 1:  # Cowrie deployed
                attacker.attempt_ssh_bruteforce(max_attempts=3)
            elif action == 2:  # Web deployed
                attacker.probe_web_vulnerabilities()

            # Log timestep
            timestep_data = {
                'Episode': episode,
                'Timestep': timestep,
                'Action': action,
                'Reward': reward,
                'SSH_Attack': int(next_state[0]),
                'Web_Attack': int(next_state[1]),
                'Deception_Active': int(next_state[3]),
                'Engagement_Score': float(next_state[4]),
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            all_timestep_results.append(timestep_data)

            print(f"  Step {timestep}: Action={action}, Reward={reward:.2f}, "
                  f"Deception={deception_component:.2f}, State={next_state}")

            state = next_state

        # Episode summary
        episode_data = {
            'Episode': episode,
            'Total_Reward': total_reward,
            'Deception_Reward': total_deception_reward,
            'Epsilon': agent.epsilon,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        all_episode_results.append(episode_data)

        print(f"\nEpisode {episode} Complete:")
        print(f"  Total Reward: {total_reward:.2f}")
        print(f"  Deception Reward: {total_deception_reward:.2f}")
        print(f"  Epsilon: {agent.epsilon:.4f}")

        # Save model checkpoint
        if episode % 5 == 0:
            model_path = f'./models/enhanced_local_dqn_episode_{episode}.pth'
            agent.save(model_path)
            print(f"  Model saved: {model_path}")

            # Export deception metrics
            json_path, csv_path = env.export_deception_metrics(episode)
            print(f"  Deception metrics: {json_path}, {csv_path}")

    # Save final results
    print("\n[Results] Saving training results...")

    import csv

    # Save episode summaries
    with open(results_dir / 'enhanced_local_episodes.csv', 'w', newline='') as f:
        fieldnames = ['Episode', 'Total_Reward', 'Deception_Reward', 'Epsilon', 'Timestamp']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_episode_results)

    # Save timestep details
    with open(results_dir / 'enhanced_local_timesteps.csv', 'w', newline='') as f:
        fieldnames = ['Episode', 'Timestep', 'Action', 'Reward', 'SSH_Attack',
                     'Web_Attack', 'Deception_Active', 'Engagement_Score', 'Timestamp']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_timestep_results)

    # Print final deception report
    print("\n[Deception Report]")
    print("=" * 60)
    report = env.get_deception_report()
    print(f"Total Deception Events: {report['environment_metrics']['total_deception_events']}")
    print(f"Accumulated Deception Rewards: {report['environment_metrics']['accumulated_deception_rewards']:.2f}")

    if report['dwell_time_analysis']['avg_with_deception_seconds'] > 0:
        print(f"\nDwell Time Analysis:")
        print(f"  Baseline: {report['dwell_time_analysis']['avg_baseline_seconds']:.2f}s")
        print(f"  With Deception: {report['dwell_time_analysis']['avg_with_deception_seconds']:.2f}s")
        print(f"  Improvement: {report['dwell_time_analysis']['improvement_percentage']:.1f}%")

    print("\n[Training Complete]")
    print(f"Results saved to: {results_dir}")


def train_enhanced_aws(num_episodes=10, timesteps_per_episode=20):
    """
    Train the enhanced RL agent on AWS with deception.

    Args:
        num_episodes: Number of training episodes
        timesteps_per_episode: Timesteps per episode
    """
    print_banner()
    print("\n[MODE] AWS Training with Enhanced Deception")
    print("=" * 60)

    # Load AWS configuration
    EC2_HOST = os.environ.get('EC2_HOST')
    EC2_USER = os.environ.get('EC2_USER', 'ubuntu')
    EC2_KEY_FILE = os.environ.get('EC2_KEY_FILE')
    USE_SSM = os.environ.get('USE_SSM', 'false').lower() == 'true'
    SSM_INSTANCE_ID = os.environ.get('SSM_INSTANCE_ID')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

    if not EC2_HOST and not (USE_SSM and SSM_INSTANCE_ID):
        print("[ERROR] AWS configuration missing!")
        print("Set EC2_HOST or (USE_SSM=true and SSM_INSTANCE_ID)")
        sys.exit(1)

    # Initialize enhanced environment
    print("\n[Setup] Connecting to AWS environment...")
    env = EnhancedCloudHoneynetEnv(
        host=EC2_HOST,
        user=EC2_USER,
        key_file=EC2_KEY_FILE,
        use_ssm=USE_SSM,
        ssm_instance_id=SSM_INSTANCE_ID,
        aws_region=AWS_REGION,
        deception_data_dir='./data/deception'
    )

    # Initialize agent
    print("[Setup] Initializing RL agent...")
    agent = DQNAgent(state_size=5, action_size=3)

    # Training loop (similar to local but without attacker simulation)
    print(f"\n[Training] Starting {num_episodes} episodes on AWS...")
    print("=" * 60)

    all_episode_results = []
    all_timestep_results = []

    for episode in range(1, num_episodes + 1):
        state = env.reset()
        total_reward = 0

        print(f"\n--- Episode {episode}/{num_episodes} ---")

        for timestep in range(1, timesteps_per_episode + 1):
            action = agent.act(state)
            next_state, reward, done = env.step(action)

            agent.remember(state, action, reward, next_state, done)
            agent.replay(batch_size=32)

            total_reward += reward

            timestep_data = {
                'Episode': episode,
                'Timestep': timestep,
                'Action': action,
                'Reward': reward,
                'Deception_Active': int(next_state[3]),
                'Engagement_Score': float(next_state[4]),
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            all_timestep_results.append(timestep_data)

            print(f"  Step {timestep}: Action={action}, Reward={reward:.2f}, State={next_state}")

            state = next_state

        episode_data = {
            'Episode': episode,
            'Total_Reward': total_reward,
            'Epsilon': agent.epsilon,
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        all_episode_results.append(episode_data)

        print(f"\nEpisode {episode} Complete: Reward={total_reward:.2f}, Epsilon={agent.epsilon:.4f}")

        # Checkpoints
        if episode % 5 == 0:
            agent.save(f'./models/enhanced_aws_dqn_episode_{episode}.pth')
            env.export_deception_metrics(episode)

    print("\n[Training Complete]")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='DeceptiCloud Enhanced Training')
    parser.add_argument('--mode', choices=['local', 'aws'], default='local',
                       help='Training mode: local or aws')
    parser.add_argument('--episodes', type=int, default=10,
                       help='Number of training episodes')
    parser.add_argument('--timesteps', type=int, default=20,
                       help='Timesteps per episode')

    args = parser.parse_args()

    if args.mode == 'local':
        train_enhanced_local(args.episodes, args.timesteps)
    else:
        train_enhanced_aws(args.episodes, args.timesteps)
