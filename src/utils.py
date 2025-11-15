import json

def parse_cowrie_logs(log_lines):
    # Placeholder: parse lines of cowrie JSON logs
    events = []
    for line in log_lines:
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def calculate_reward(state, new_state, action):
    # Placeholder simple reward function
    attacker_detected = new_state[0]
    current_honeypot = new_state[1]
    reward = 0
    if attacker_detected == 1 and current_honeypot == 1:
        reward = 10
    elif attacker_detected == 0 and current_honeypot != 0:
        reward = -1
    return reward
