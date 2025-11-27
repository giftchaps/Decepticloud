import boto3
import time
import json
from datetime import datetime, timedelta

class AWSCostTracker:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.ce_client = boto3.client('ce', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.api_calls = []
        self.resource_usage = {}
        self.start_time = datetime.utcnow()
        
    def log_api_call(self, service, operation, cost_estimate=0.0):
        """Log each API call with timestamp and estimated cost"""
        self.api_calls.append({
            'timestamp': datetime.utcnow().isoformat(),
            'service': service,
            'operation': operation,
            'estimated_cost': cost_estimate
        })
        
    def track_resource_usage(self, resource_type, resource_id, action):
        """Track resource creation/deletion for cost calculation"""
        if resource_id not in self.resource_usage:
            self.resource_usage[resource_id] = {
                'type': resource_type,
                'created': datetime.utcnow(),
                'actions': []
            }
        
        self.resource_usage[resource_id]['actions'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': action
        })
        
    def get_real_costs(self):
        """Get actual AWS costs for the experiment period"""
        try:
            end_date = datetime.utcnow().date()
            start_date = self.start_time.date()
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            return response['ResultsByTime']
        except Exception as e:
            print(f"Could not retrieve real costs: {e}")
            return None
            
    def calculate_experiment_cost(self):
        """Calculate total cost of the experiment"""
        # API call costs (rough estimates)
        api_cost = len(self.api_calls) * 0.0001  # $0.0001 per API call estimate
        
        # Resource costs
        resource_cost = 0.0
        for resource_id, data in self.resource_usage.items():
            if data['type'] == 'ec2_instance':
                # t3.micro: $0.0104/hour
                hours = (datetime.utcnow() - data['created']).total_seconds() / 3600
                resource_cost += hours * 0.0104
                
        return {
            'api_calls_cost': api_cost,
            'resource_cost': resource_cost,
            'total_estimated_cost': api_cost + resource_cost,
            'total_api_calls': len(self.api_calls),
            'experiment_duration_hours': (datetime.utcnow() - self.start_time).total_seconds() / 3600
        }
        
    def export_cost_report(self, filepath):
        """Export detailed cost analysis"""
        report = {
            'experiment_metadata': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'region': self.region
            },
            'cost_summary': self.calculate_experiment_cost(),
            'api_calls': self.api_calls,
            'resource_usage': self.resource_usage,
            'real_aws_costs': self.get_real_costs()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)