import time
import csv
import os
from datetime import datetime
from src.agent import DQNAgent
from src.environment import CloudHoneynetEnv
from src.attacker import run_attacker_thread
from src.aws_utils import get_instance_id_by_ip, upload_dir_to_s3
import numpy as np

# --- CONFIGURATION ---
STATE_SIZE = 3      # [ssh_attack_detected (0/1), web_attack_detected (0/1), current_honeypot_type (0/1/2)]
ACTION_SIZE = 3     # [0: Do Nothing, 1: Deploy Cowrie, 2: Deploy Web Honeypot]
EPISODES = 5  # Reduced default for quick smoke runs
BATCH_SIZE = 32

# Replace these with your instance's details before running
EC2_HOST = os.environ.get('EC2_HOST') or "YOUR_EC2_IP_ADDRESS"
EC2_USER = os.environ.get('EC2_USER') or "ubuntu"
EC2_KEY_FILE = os.environ.get('EC2_KEY_FILE') or "path/to/your/key.pem"

# Results logging
RESULTS_DIR = "results"
LOG_PER_TIMESTEP = True

# Optional SSM usage (driven by env vars or code)
USE_SSM = os.environ.get('DECEPTICLOUD_USE_SSM', os.environ.get('USE_SSM', '0')).lower() in ('1', 'true', 'yes')
# If SSM_INSTANCE_ID is provided via env, use it; otherwise None
SSM_INSTANCE_ID = os.environ.get('DECEPTICLOUD_SSM_INSTANCE') or os.environ.get('SSM_INSTANCE_ID') or None
AWS_REGION = os.environ.get('AWS_REGION') or None

# Optional S3 upload of results after run (set S3_BUCKET env var or below)
S3_BUCKET = os.environ.get('DECEPTICLOUD_RESULTS_BUCKET') or None
S3_PREFIX = 'decepticloud_results'

# Dry-run mode: set DECEPTICLOUD_DRY_RUN=1 to enable (no remote commands executed)
DRY_RUN = os.environ.get('DECEPTICLOUD_DRY_RUN', os.environ.get('DRY_RUN', '0')).lower() in ('1', 'true', 'yes')

os.makedirs(RESULTS_DIR, exist_ok=True)

summary_path = os.path.join(RESULTS_DIR, 'results_summary.csv')
per_timestep_path = os.path.join(RESULTS_DIR, 'results_per_timestep.csv')

if not os.path.exists(summary_path):
    with open(summary_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['episode', 'total_reward', 'epsilon', 'timestamp'])

if LOG_PER_TIMESTEP and not os.path.exists(per_timestep_path):
    with open(per_timestep_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['episode', 'timestep', 'action', 'reward', 'ssh_attack', 'web_attack', 'current_honeypot', 'timestamp'])


def run_experiment():
    print("Initializing environment and agent...")
    # Auto-detect instance id if using SSM and only IP is provided
    ssm_instance = SSM_INSTANCE_ID
    if USE_SSM and not SSM_INSTANCE_ID and EC2_HOST:
        print("Attempting to auto-detect EC2 instance id from public IP via AWS API...")
        ssm_instance = get_instance_id_by_ip(AWS_REGION, EC2_HOST)
        if ssm_instance:
            print(f"Found instance id: {ssm_instance}")
        else:
            print("Could not auto-detect instance id. Ensure AWS credentials and region are configured.")

    env = CloudHoneynetEnv(host=EC2_HOST, user=EC2_USER, key_file=EC2_KEY_FILE,
                           use_ssm=USE_SSM, ssm_instance_id=ssm_instance, aws_region=AWS_REGION,
                           dry_run=DRY_RUN)
    agent = DQNAgent(state_size=STATE_SIZE, action_size=ACTION_SIZE)
    
    print("Starting attacker thread...")
    run_attacker_thread(EC2_HOST, EC2_USER, EC2_KEY_FILE)

    for e in range(EPISODES):
        state = env.reset()
        state = np.reshape(state, [STATE_SIZE])
        total_reward = 0

        for t in range(24):
            print(f"Episode {e+1}/{EPISODES}, Timestep {t+1}/24")
            action = agent.act(state)
            next_state, reward, done = env.step(action)
            next_state = np.reshape(next_state, [STATE_SIZE])

            total_reward += reward
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            agent.learn(BATCH_SIZE)
            time.sleep(1)
            # Log per-timestep row
            if LOG_PER_TIMESTEP:
                with open(per_timestep_path, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([e+1, t+1, int(action), float(reward), int(next_state[0]), int(next_state[1]), int(next_state[2]), datetime.utcnow().isoformat()])

        print(f"Episode: {e+1}/{EPISODES}, Total Reward: {total_reward}, Epsilon: {agent.epsilon:.2f}")
        # Append summary
        with open(summary_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([e+1, float(total_reward), float(agent.epsilon), datetime.utcnow().isoformat()])

    # Save trained model
    model_path = os.path.join(RESULTS_DIR, 'dqn_model.pth')
    agent.save(model_path)

    # Optionally upload results to S3 for later analysis
    if S3_BUCKET:
        print(f"Uploading results to s3://{S3_BUCKET}/{S3_PREFIX} ...")
        try:
            uploaded = upload_dir_to_s3(S3_BUCKET, S3_PREFIX, RESULTS_DIR, region=AWS_REGION)
            print(f"Uploaded {len(uploaded)} files to S3")
        except Exception as e:
            print(f"S3 upload failed: {e}")


if __name__ == "__main__":
    run_experiment()
