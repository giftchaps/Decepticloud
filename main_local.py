#!/usr/bin/env python3
"""
DeceptiCloud Local Testing Version

This version runs the RL agent with Docker containers on localhost.
No AWS/EC2 required - perfect for testing and development on Windows/Mac/Linux.

Usage:
    1. First, start honeypots: docker-compose -f docker-compose.local.yml up -d
    2. Then run: python main_local.py --episodes 5
"""

import sys
import os
import time
import csv
import argparse
from datetime import datetime
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import DQNAgent


class LocalDockerEnvironment:
    """
    Simplified environment for local Docker testing.

    Uses docker commands directly instead of SSH to EC2.
    """

    def __init__(self, host="localhost"):
        self.host = host
        self.state_size = 4  # [attacker_detected, current_honeypot, attack_intensity, dwell_time]
        self.action_size = 3  # 0=nothing, 1=ssh, 2=web
        self.current_honeypot = 0  # 0=none, 1=cowrie, 2=nginx
        
        # Deception tracking
        self.attack_intensity = 0
        self.dwell_time = 0
        self.last_attack_time = 0

        print("[Environment] Local Docker environment initialized")
        print(f"[Environment] Target: {host}")
        print(f"[Environment] State size: {self.state_size}, Action size: {self.action_size}")

    def _execute_docker_command(self, cmd):
        """Execute docker command locally."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return "", "Command timed out"
        except Exception as e:
            return "", str(e)

    def _check_container_running(self, container_name):
        """Check if Docker container is running."""
        cmd = f'docker ps --filter "name={container_name}" --format "{{{{.Names}}}}"'
        stdout, stderr = self._execute_docker_command(cmd)
        return container_name in stdout

    def _get_state(self):
        """
        Get current state by checking Docker logs.

        Returns:
            [ssh_attack_detected, web_attack_detected, current_honeypot]
        """
        ssh_attack = 0
        web_attack = 0

        # Check Cowrie SSH logs for recent attacks
        if self._check_container_running("cowrie_honeypot_local"):
            cmd = 'docker logs --tail 50 cowrie_honeypot_local 2>&1 | findstr /C:"login attempt" /C:"SSH" /C:"authentication"'
            stdout, _ = self._execute_docker_command(cmd)
            if stdout and len(stdout.strip()) > 0:
                ssh_attack = 1
                print(f"[Detection] SSH attack detected in Cowrie logs")

        # Check nginx web logs for recent requests
        if self._check_container_running("nginx_honeypot_local"):
            cmd = 'docker logs --tail 50 nginx_honeypot_local 2>&1 | findstr /C:"GET" /C:"POST" /C:"404" /C:"401"'
            stdout, _ = self._execute_docker_command(cmd)
            if stdout and len(stdout.strip()) > 0:
                web_attack = 1
                print(f"[Detection] Web attack detected in nginx logs")

        # Enhanced state for deception learning
        attacker_detected = max(ssh_attack, web_attack)
        current_time = time.time()
        
        if attacker_detected:
            self.dwell_time += 1
            self.attack_intensity = min(10, self.attack_intensity + 1)
            self.last_attack_time = current_time
            print(f"[Deception] Attacker engaged for {self.dwell_time} timesteps, intensity: {self.attack_intensity}")
        else:
            self.attack_intensity = max(0, self.attack_intensity - 0.5)
            if current_time - self.last_attack_time > 60:
                self.dwell_time = 0
        
        state = [attacker_detected, self.current_honeypot, self.attack_intensity, self.dwell_time]
        return state

    def reset(self):
        """Reset environment - stop all honeypots."""
        print("[Environment] Resetting environment (stopping honeypots)...")

        # Stop containers if running
        self._execute_docker_command("docker stop cowrie_honeypot_local nginx_honeypot_local 2>nul")
        self.current_honeypot = 0
        
        # Reset deception tracking
        self.attack_intensity = 0
        self.dwell_time = 0
        self.last_attack_time = 0

        time.sleep(2)
        return self._get_state()

    def step(self, action):
        """
        Execute action and return new state, reward, done.

        Actions:
            0 = Do nothing / stop all
            1 = Deploy Cowrie SSH honeypot
            2 = Deploy nginx web honeypot
        """
        reward = 0

        # Execute action
        if action == 0:
            # Stop all honeypots
            if self.current_honeypot != 0:
                print("[Action] Stopping all honeypots...")
                self._execute_docker_command("docker stop cowrie_honeypot_local nginx_honeypot_local 2>nul")
                self.current_honeypot = 0

        elif action == 1:
            # Deploy Cowrie SSH honeypot
            if self.current_honeypot != 1:
                print("[Action] Deploying Cowrie SSH honeypot...")
                self._execute_docker_command("docker stop nginx_honeypot_local 2>nul")

                # Start Cowrie
                cmd = 'docker-compose -f docker-compose.local.yml up -d cowrie'
                stdout, stderr = self._execute_docker_command(cmd)

                if "error" not in stderr.lower():
                    self.current_honeypot = 1
                    print("[Action] Cowrie honeypot deployed")
                else:
                    print(f"[Action] Failed to deploy Cowrie: {stderr}")

        elif action == 2:
            # Deploy nginx web honeypot
            if self.current_honeypot != 2:
                print("[Action] Deploying nginx web honeypot...")
                self._execute_docker_command("docker stop cowrie_honeypot_local 2>nul")

                # Start nginx
                cmd = 'docker-compose -f docker-compose.local.yml up -d nginx'
                stdout, stderr = self._execute_docker_command(cmd)

                if "error" not in stderr.lower():
                    self.current_honeypot = 2
                    print("[Action] nginx honeypot deployed")
                else:
                    print(f"[Action] Failed to deploy nginx: {stderr}")

        # Adaptive timing for deception
        next_state_preview = self._get_state()
        attacker_detected = next_state_preview[0]
        
        if attacker_detected:
            # Longer engagement time when attacker is active
            time.sleep(8)
            print(f"[Deception] Maintaining engagement with attacker...")
        else:
            # Quick transitions when no attacker
            time.sleep(3)

        # Get new state
        next_state = self._get_state()
        attacker_detected, current_honeypot, attack_intensity, dwell_time = next_state
        
        # For reward calculation, we need to know attack types
        ssh_attack = 0
        web_attack = 0
        if attacker_detected:
            # Check which type of attack
            if self._check_container_running("cowrie_honeypot_local"):
                cmd = 'docker logs --tail 10 cowrie_honeypot_local 2>&1 | findstr /C:"login attempt" /C:"SSH"'
                stdout, _ = self._execute_docker_command(cmd)
                if stdout and len(stdout.strip()) > 0:
                    ssh_attack = 1
            
            if self._check_container_running("nginx_honeypot_local"):
                cmd = 'docker logs --tail 10 nginx_honeypot_local 2>&1 | findstr /C:"GET" /C:"POST"'
                stdout, _ = self._execute_docker_command(cmd)
                if stdout and len(stdout.strip()) > 0:
                    web_attack = 1

        # Enhanced deceptive reward structure
        if attacker_detected:
            if action == 1 and ssh_attack:  # SSH honeypot engaging SSH attacker
                reward = 15 + (dwell_time * 0.5)  # Bonus for sustained engagement
                print(f"[Reward] +{reward}: SSH honeypot successfully deceiving attacker (dwell: {dwell_time})")
            elif action == 2 and web_attack:  # Web honeypot engaging web attacker
                reward = 12 + (dwell_time * 0.5)  # Bonus for sustained engagement
                print(f"[Reward] +{reward}: Web honeypot successfully deceiving attacker (dwell: {dwell_time})")
            elif action == 0:
                reward = -10  # Heavy penalty for missing deception opportunity
                print(f"[Reward] -10: Attacker present but no deception active")
            else:
                reward = -5  # Wrong honeypot type but still engaging
                print(f"[Reward] -5: Wrong honeypot type but maintaining some deception")
        else:
            if action != 0:
                reward = -2  # Small penalty for running without attacker
                print(f"[Reward] -2: Honeypot idle (waiting for attacker)")
            else:
                reward = -1  # Penalty for not being ready
                print(f"[Reward] -1: No deception ready")

        done = False  # Never end episode early

        return next_state, reward, done


def main():
    parser = argparse.ArgumentParser(description='DeceptiCloud Local Testing')
    parser.add_argument('--episodes', type=int, default=5, help='Number of episodes')
    parser.add_argument('--timesteps', type=int, default=24, help='Timesteps per episode')
    parser.add_argument('--target', type=str, default='localhost', help='Target host')

    args = parser.parse_args()

    print("=" * 60)
    print("DeceptiCloud: Local Docker Testing Mode")
    print("=" * 60)
    print(f"Episodes: {args.episodes}")
    print(f"Timesteps per episode: {args.timesteps}")
    print(f"Target: {args.target}")
    print("=" * 60)

    # Check if Docker is available
    result = subprocess.run("docker --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("\n❌ ERROR: Docker not found!")
        print("Please install Docker Desktop and start it before running this script.")
        print("See LOCAL_TESTING.md for instructions.")
        sys.exit(1)

    print(f"Docker found: {result.stdout.decode().strip()}")

    # Check if honeypot containers exist
    result = subprocess.run(
        'docker-compose -f docker-compose.local.yml ps',
        shell=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("\n⚠️  Warning: Docker Compose configuration not found or not started")
        print("\nQuick start:")
        print("  1. bash scripts/setup_local_test.sh")
        print("  2. docker-compose -f docker-compose.local.yml up -d")
        print("  3. python main_local.py")
        print("\nContinuing anyway...")

    # Initialize environment and agent
    print("\nInitializing environment and agent...")
    env = LocalDockerEnvironment(host=args.target)
    agent = DQNAgent(state_size=env.state_size, action_size=env.action_size)

    # Create results directory
    os.makedirs('results', exist_ok=True)

    # CSV files for logging
    timestep_file = 'results/local_timesteps.csv'
    episode_file = 'results/local_episodes.csv'

    # Write CSV headers
    with open(timestep_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Episode', 'Timestep', 'Action', 'Reward', 'SSH_Attack', 'Web_Attack', 'Timestamp'])

    with open(episode_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Episode', 'Total_Reward', 'Epsilon', 'Timestamp'])

    # Training loop
    print("\n" + "=" * 60)
    print("Starting Training")
    print("=" * 60)

    print("\nTIP: Open another terminal and run attack simulations:")
    print("  ssh -p 2222 root@localhost")
    print("  curl http://localhost:8080/.env")
    print("\n" + "=" * 60 + "\n")

    for e in range(args.episodes):
        state = env.reset()
        total_reward = 0

        for t in range(args.timesteps):
            print(f"\nEpisode {e+1}/{args.episodes}, Timestep {t+1}/{args.timesteps}")

            # Agent chooses action
            action = agent.act(state)

            # Environment executes action
            next_state, reward, done = env.step(action)

            # Agent learns
            agent.remember(state, action, reward, next_state, done)
            if len(agent.memory) > 32:
                agent.learn(32, e)

            # Log timestep
            with open(timestep_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    e+1, t+1, int(action), float(reward),
                    int(next_state[0]), int(next_state[1]),
                    datetime.now().isoformat()
                ])

            state = next_state
            total_reward += reward

        # Log episode
        with open(episode_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                e+1, float(total_reward), float(agent.epsilon),
                datetime.now().isoformat()
            ])

        print(f"\n{'='*60}")
        print(f"Episode {e+1}/{args.episodes} Complete")
        print(f"Total Reward: {total_reward}")
        print(f"Epsilon: {agent.epsilon:.2f}")
        print(f"{'='*60}\n")

        # Save model every 5 episodes
        if (e + 1) % 5 == 0:
            model_path = f'models/local_dqn_episode_{e+1}.pth'
            os.makedirs('models', exist_ok=True)
            # Save model (simplified for local testing)
            import torch
            torch.save(agent.model.state_dict(), model_path)
            print(f"Model saved: {model_path}")

    # Final cleanup
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"\nResults saved to:")
    print(f"  - {timestep_file}")
    print(f"  - {episode_file}")
    print(f"\nFinal model saved to:")
    print(f"  - models/local_dqn_episode_{args.episodes}.pth")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
