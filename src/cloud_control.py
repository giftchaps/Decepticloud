import time
import boto3

class CloudCommandRunner:
    """Helper to execute shell commands on EC2 instances using AWS SSM.

    This is an optional alternative to SSH. It requires the target instance to
    have the SSM Agent installed and an IAM role that allows SSM SendCommand.
    """

    def __init__(self, region_name=None):
        self.region_name = region_name
        self.ssm = boto3.client('ssm', region_name=region_name) if region_name else boto3.client('ssm')

    def run_command(self, instance_ids, commands, timeout=60):
        """Run commands (list of strings) via SSM on the given instance ids.

        Returns a tuple (success, output, error). Output is concatenated stdout.
        """
        if isinstance(instance_ids, str):
            instance_ids = [instance_ids]

        try:
            response = self.ssm.send_command(
                InstanceIds=instance_ids,
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": commands},
                TimeoutSeconds=max(60, timeout),
            )
            cmd_id = response['Command']['CommandId']

            # wait for the command to finish
            end_time = time.time() + timeout
            while time.time() < end_time:
                invocation = self.ssm.list_command_invocations(
                    CommandId=cmd_id,
                    InstanceId=instance_ids[0],
                    Details=True
                )
                if invocation['CommandInvocations']:
                    status = invocation['CommandInvocations'][0]['Status']
                    if status in ('Success', 'Failed', 'Cancelled', 'TimedOut'):
                        out = invocation['CommandInvocations'][0].get('CommandPlugins', [])
                        stdout = ''
                        stderr = ''
                        for p in out:
                            stdout += p.get('Output', '')
                        success = status == 'Success'
                        return success, stdout, '' if success else f'status={status}'
                time.sleep(1)

            return False, '', 'timeout'
        except Exception as e:
            return False, '', str(e)
