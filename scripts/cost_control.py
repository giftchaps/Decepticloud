#!/usr/bin/env python3
"""
Cost Control and Automated Cleanup for DeceptiCloud

Prevents runaway AWS costs by:
- Monitoring current spend
- Auto-stopping expensive resources
- Cleaning up orphaned resources
- Setting up billing alarms

Usage:
    # Check current costs
    python scripts/cost_control.py --check

    # Cleanup all honeypot resources
    python scripts/cost_control.py --cleanup

    # Setup billing alarms
    python scripts/cost_control.py --setup-alarms --threshold 50
"""
import argparse
import boto3
import sys
from datetime import datetime, timedelta
from decimal import Decimal


class CostController:
    """Automated cost control for DeceptiCloud deployments."""

    def __init__(self, region='us-east-1'):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)
        self.ce = boto3.client('ce', region_name='us-east-1')  # Cost Explorer is us-east-1 only
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)

    def get_current_month_costs(self):
        """Get cost for current month."""
        start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')

        try:
            response = self.ce.get_cost_and_usage(
                TimePeriod={'Start': start, 'End': end},
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )

            if response['ResultsByTime']:
                amount = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
                return float(amount)
            return 0.0

        except Exception as e:
            print(f"[Warning] Could not retrieve cost data: {e}")
            print("Make sure Cost Explorer is enabled in your AWS account")
            return None

    def list_decepticloud_resources(self):
        """List all EC2 resources tagged with DeceptiCloud."""
        resources = {
            'instances': [],
            'volumes': [],
            'snapshots': []
        }

        # Find instances
        try:
            instances = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': ['*DeceptiCloud*', '*Honeynet*']},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
                ]
            )

            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    resources['instances'].append({
                        'id': instance['InstanceId'],
                        'type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'launch_time': instance['LaunchTime']
                    })

        except Exception as e:
            print(f"[Error] Failed to list instances: {e}")

        # Find volumes
        try:
            volumes = self.ec2.describe_volumes(
                Filters=[
                    {'Name': 'tag:Name', 'Values': ['*DeceptiCloud*']}
                ]
            )

            for volume in volumes['Volumes']:
                resources['volumes'].append({
                    'id': volume['VolumeId'],
                    'size': volume['Size'],
                    'state': volume['State']
                })

        except Exception as e:
            print(f"[Error] Failed to list volumes: {e}")

        return resources

    def cleanup_resources(self, dry_run=False):
        """Cleanup all DeceptiCloud resources."""
        print("=" * 60)
        print("DeceptiCloud Cost Control - Resource Cleanup")
        print("=" * 60)

        resources = self.list_decepticloud_resources()

        # Terminate instances
        if resources['instances']:
            print(f"\nFound {len(resources['instances'])} instance(s):")
            for inst in resources['instances']:
                print(f"  - {inst['id']} ({inst['type']}, {inst['state']})")

            if not dry_run:
                instance_ids = [i['id'] for i in resources['instances']]
                confirm = input(f"\nTerminate {len(instance_ids)} instance(s)? (yes/no): ")
                if confirm.lower() == 'yes':
                    try:
                        self.ec2.terminate_instances(InstanceIds=instance_ids)
                        print(f"✓ Terminated {len(instance_ids)} instance(s)")
                    except Exception as e:
                        print(f"[Error] Failed to terminate: {e}")
        else:
            print("\n✓ No instances to cleanup")

        # Delete unattached volumes
        if resources['volumes']:
            unattached = [v for v in resources['volumes'] if v['state'] == 'available']
            if unattached:
                print(f"\nFound {len(unattached)} unattached volume(s):")
                for vol in unattached:
                    print(f"  - {vol['id']} ({vol['size']} GB)")

                if not dry_run:
                    confirm = input(f"\nDelete {len(unattached)} volume(s)? (yes/no): ")
                    if confirm.lower() == 'yes':
                        for vol in unattached:
                            try:
                                self.ec2.delete_volume(VolumeId=vol['id'])
                                print(f"✓ Deleted {vol['id']}")
                            except Exception as e:
                                print(f"[Error] Failed to delete {vol['id']}: {e}")

        print("\n" + "=" * 60)
        print("Cleanup complete!")
        print("=" * 60)

    def setup_billing_alarm(self, threshold_usd=50, email=None):
        """Setup CloudWatch billing alarm."""
        print(f"\nSetting up billing alarm (threshold: ${threshold_usd})...")

        # Create SNS topic for alerts
        topic_name = 'DeceptiCloud-Billing-Alerts'

        try:
            topic_response = self.sns.create_topic(Name=topic_name)
            topic_arn = topic_response['TopicArn']
            print(f"✓ Created SNS topic: {topic_arn}")

            # Subscribe email if provided
            if email:
                self.sns.subscribe(
                    TopicArn=topic_arn,
                    Protocol='email',
                    Endpoint=email
                )
                print(f"✓ Subscribed {email} to alerts (check your email to confirm)")

        except Exception as e:
            print(f"[Error] Failed to setup SNS: {e}")
            return

        # Create CloudWatch alarm
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName='DeceptiCloud-Cost-Alert',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='EstimatedCharges',
                Namespace='AWS/Billing',
                Period=21600,  # 6 hours
                Statistic='Maximum',
                Threshold=threshold_usd,
                ActionsEnabled=True,
                AlarmActions=[topic_arn],
                AlarmDescription=f'Alert when DeceptiCloud costs exceed ${threshold_usd}',
                Dimensions=[
                    {'Name': 'Currency', 'Value': 'USD'}
                ]
            )
            print(f"✓ Created billing alarm (threshold: ${threshold_usd})")

        except Exception as e:
            print(f"[Error] Failed to create alarm: {e}")
            print("Note: Billing alarms require CloudWatch in us-east-1")

    def stop_expensive_instances(self, instance_type_threshold='t2.micro'):
        """Stop instances larger than threshold."""
        print(f"\nChecking for instances larger than {instance_type_threshold}...")

        # Instance size hierarchy
        sizes = {
            't2.nano': 1,
            't2.micro': 2,
            't2.small': 3,
            't2.medium': 4,
            't2.large': 5,
            't2.xlarge': 6,
            't3.micro': 2,
            't3.small': 3,
        }

        threshold_size = sizes.get(instance_type_threshold, 2)
        resources = self.list_decepticloud_resources()

        for inst in resources['instances']:
            if inst['state'] == 'running':
                inst_size = sizes.get(inst['type'], 999)
                if inst_size > threshold_size:
                    print(f"[Warning] Found large instance: {inst['id']} ({inst['type']})")
                    confirm = input(f"Stop instance {inst['id']}? (yes/no): ")
                    if confirm.lower() == 'yes':
                        try:
                            self.ec2.stop_instances(InstanceIds=[inst['id']])
                            print(f"✓ Stopped {inst['id']}")
                        except Exception as e:
                            print(f"[Error] Failed to stop: {e}")


def main():
    parser = argparse.ArgumentParser(description='DeceptiCloud Cost Control')

    parser.add_argument('--check', action='store_true',
                       help='Check current month costs')

    parser.add_argument('--cleanup', action='store_true',
                       help='Cleanup all DeceptiCloud resources')

    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be cleaned up (no actual deletion)')

    parser.add_argument('--setup-alarms', action='store_true',
                       help='Setup billing alarms')

    parser.add_argument('--threshold', type=float, default=50,
                       help='Billing alarm threshold in USD (default: 50)')

    parser.add_argument('--email', type=str,
                       help='Email address for billing alerts')

    parser.add_argument('--stop-large-instances', action='store_true',
                       help='Stop instances larger than t2.micro')

    parser.add_argument('--region', type=str, default='us-east-1',
                       help='AWS region (default: us-east-1)')

    args = parser.parse_args()

    controller = CostController(region=args.region)

    if args.check:
        cost = controller.get_current_month_costs()
        if cost is not None:
            print("=" * 60)
            print(f"Current month costs: ${cost:.2f} USD")
            print("=" * 60)

    if args.cleanup:
        controller.cleanup_resources(dry_run=args.dry_run)

    if args.setup_alarms:
        controller.setup_billing_alarm(
            threshold_usd=args.threshold,
            email=args.email
        )

    if args.stop_large_instances:
        controller.stop_expensive_instances()

    if not any([args.check, args.cleanup, args.setup_alarms, args.stop_large_instances]):
        parser.print_help()


if __name__ == "__main__":
    main()
