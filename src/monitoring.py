import boto3
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any
import logging

class DeceptiCloudMonitor:
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.log_group = '/decepticloud/honeypot'
        self.metrics_namespace = 'DeceptiCloud'
        
    def setup_cloudwatch_logging(self):
        """Create CloudWatch log group for honeypot events"""
        try:
            self.logs_client.create_log_group(logGroupName=self.log_group)
            print(f"Created CloudWatch log group: {self.log_group}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            print(f"Log group {self.log_group} already exists")
    
    def send_attack_event(self, attacker_ip: str, attack_type: str, honeypot_type: str, 
                         success: bool, details: Dict[str, Any]):
        """Send attack event to CloudWatch"""
        timestamp = int(time.time() * 1000)
        
        # Send to CloudWatch Logs
        log_event = {
            'timestamp': timestamp,
            'message': json.dumps({
                'event_type': 'attack',
                'attacker_ip': attacker_ip,
                'attack_type': attack_type,
                'honeypot_type': honeypot_type,
                'success': success,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
        }
        
        try:
            self.logs_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"attacks-{datetime.now().strftime('%Y-%m-%d')}",
                logEvents=[log_event]
            )
        except Exception as e:
            print(f"Failed to send log event: {e}")
        
        # Send metrics to CloudWatch
        self.cloudwatch.put_metric_data(
            Namespace=self.metrics_namespace,
            MetricData=[
                {
                    'MetricName': 'AttackCount',
                    'Dimensions': [
                        {'Name': 'AttackType', 'Value': attack_type},
                        {'Name': 'HoneypotType', 'Value': honeypot_type}
                    ],
                    'Value': 1,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'AttackSuccess',
                    'Dimensions': [
                        {'Name': 'AttackerIP', 'Value': attacker_ip}
                    ],
                    'Value': 1 if success else 0,
                    'Unit': 'Count'
                }
            ]
        )
    
    def send_reward_metric(self, episode: int, reward: float, action: str):
        """Send RL reward metrics to CloudWatch"""
        self.cloudwatch.put_metric_data(
            Namespace=self.metrics_namespace,
            MetricData=[
                {
                    'MetricName': 'EpisodeReward',
                    'Dimensions': [{'Name': 'Episode', 'Value': str(episode)}],
                    'Value': reward,
                    'Unit': 'None'
                },
                {
                    'MetricName': 'ActionTaken',
                    'Dimensions': [{'Name': 'Action', 'Value': action}],
                    'Value': 1,
                    'Unit': 'Count'
                }
            ]
        )
    
    def send_learning_metrics(self, episode: int, epsilon: float, loss: float, q_values: List[float]):
        """Send learning progress metrics"""
        self.cloudwatch.put_metric_data(
            Namespace=self.metrics_namespace,
            MetricData=[
                {
                    'MetricName': 'Epsilon',
                    'Value': epsilon,
                    'Unit': 'None'
                },
                {
                    'MetricName': 'Loss',
                    'Value': loss,
                    'Unit': 'None'
                },
                {
                    'MetricName': 'AvgQValue',
                    'Value': sum(q_values) / len(q_values) if q_values else 0,
                    'Unit': 'None'
                }
            ]
        )
    
    def get_attack_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get attack summary from CloudWatch logs"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        try:
            response = self.logs_client.filter_log_events(
                logGroupName=self.log_group,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern='{ $.event_type = "attack" }'
            )
            
            attacks = []
            for event in response['events']:
                try:
                    data = json.loads(event['message'])
                    attacks.append(data)
                except json.JSONDecodeError:
                    continue
            
            # Analyze attacks
            unique_ips = set(attack['attacker_ip'] for attack in attacks)
            attack_types = {}
            honeypot_usage = {}
            
            for attack in attacks:
                attack_type = attack['attack_type']
                honeypot_type = attack['honeypot_type']
                
                attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
                honeypot_usage[honeypot_type] = honeypot_usage.get(honeypot_type, 0) + 1
            
            return {
                'total_attacks': len(attacks),
                'unique_attackers': len(unique_ips),
                'attacker_ips': list(unique_ips),
                'attack_types': attack_types,
                'honeypot_usage': honeypot_usage,
                'recent_attacks': attacks[-10:]  # Last 10 attacks
            }
        except Exception as e:
            print(f"Error getting attack summary: {e}")
            return {}
    
    def get_learning_progress(self, hours: int = 24) -> Dict[str, List[float]]:
        """Get learning metrics from CloudWatch"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {}
        for metric_name in ['EpisodeReward', 'Epsilon', 'Loss', 'AvgQValue']:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace=self.metrics_namespace,
                    MetricName=metric_name,
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5 minutes
                    Statistics=['Average']
                )
                
                values = [(point['Timestamp'], point['Average']) 
                         for point in response['Datapoints']]
                values.sort(key=lambda x: x[0])
                metrics[metric_name] = values
            except Exception as e:
                print(f"Error getting {metric_name}: {e}")
                metrics[metric_name] = []
        
        return metrics
    
    def create_dashboard(self, save_path: str = "dashboard.html"):
        """Create HTML dashboard showing all metrics"""
        attack_summary = self.get_attack_summary()
        learning_metrics = self.get_learning_progress()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DeceptiCloud Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric-box {{ border: 1px solid #ccc; padding: 15px; margin: 10px; border-radius: 5px; }}
                .attack-ip {{ color: red; font-weight: bold; }}
                .reward {{ color: green; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>DeceptiCloud Real-Time Dashboard</h1>
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="metric-box">
                <h2>Attack Summary (Last 24h)</h2>
                <p><strong>Total Attacks:</strong> {attack_summary.get('total_attacks', 0)}</p>
                <p><strong>Unique Attackers:</strong> {attack_summary.get('unique_attackers', 0)}</p>
                <p><strong>Attacker IPs:</strong></p>
                <ul>
                    {''.join(f'<li class="attack-ip">{ip}</li>' for ip in attack_summary.get('attacker_ips', []))}
                </ul>
                
                <h3>Attack Types</h3>
                <table>
                    <tr><th>Type</th><th>Count</th></tr>
                    {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in attack_summary.get('attack_types', {}).items())}
                </table>
                
                <h3>Honeypot Usage</h3>
                <table>
                    <tr><th>Honeypot</th><th>Attacks</th></tr>
                    {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in attack_summary.get('honeypot_usage', {}).items())}
                </table>
            </div>
            
            <div class="metric-box">
                <h2>Recent Attacks</h2>
                <table>
                    <tr><th>Time</th><th>IP</th><th>Type</th><th>Honeypot</th><th>Success</th></tr>
                    {''.join(f'<tr><td>{attack.get("timestamp", "")}</td><td class="attack-ip">{attack.get("attacker_ip", "")}</td><td>{attack.get("attack_type", "")}</td><td>{attack.get("honeypot_type", "")}</td><td>{attack.get("success", "")}</td></tr>' for attack in attack_summary.get('recent_attacks', []))}
                </table>
            </div>
            
            <div class="metric-box">
                <h2>Learning Progress</h2>
                <p>Current learning metrics from the RL agent:</p>
                <ul>
                    <li>Episode Rewards: {len(learning_metrics.get('EpisodeReward', []))} data points</li>
                    <li>Epsilon (Exploration): {len(learning_metrics.get('Epsilon', []))} data points</li>
                    <li>Training Loss: {len(learning_metrics.get('Loss', []))} data points</li>
                    <li>Q-Values: {len(learning_metrics.get('AvgQValue', []))} data points</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        with open(save_path, 'w') as f:
            f.write(html_content)
        
        print(f"Dashboard saved to {save_path}")
        return save_path

# Global monitor instance
monitor = DeceptiCloudMonitor()