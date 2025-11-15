import boto3
import os
import pathlib
import time


def get_instance_id_by_ip(region, public_ip):
    """Return the EC2 instance id that has the given public IP, or None."""
    try:
        ec2 = boto3.client('ec2', region_name=region) if region else boto3.client('ec2')
        resp = ec2.describe_instances(
            Filters=[
                {'Name': 'ip-address', 'Values': [public_ip]},
                {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
            ]
        )
        for r in resp.get('Reservations', []):
            for inst in r.get('Instances', []):
                return inst.get('InstanceId')
    except Exception as e:
        print(f"aws_utils.get_instance_id_by_ip error: {e}")
    return None


def upload_dir_to_s3(bucket_name, prefix, local_dir, region=None):
    """Upload all files under local_dir to s3://bucket_name/prefix/

    Returns list of uploaded keys or raises on error.
    """
    s3 = boto3.client('s3', region_name=region) if region else boto3.client('s3')
    local_dir = pathlib.Path(local_dir)
    uploaded = []

    if not local_dir.exists():
        raise FileNotFoundError(f"Local directory {local_dir} does not exist")

    # Upload files with a retry per file so transient S3 errors don't abort the entire run
    for p in local_dir.rglob('*'):
        if p.is_file():
            key = f"{prefix.rstrip('/')}/{p.relative_to(local_dir).as_posix()}"
            max_attempts = 3
            attempt = 0
            success = False
            last_error = None
            while attempt < max_attempts and not success:
                try:
                    attempt += 1
                    s3.upload_file(str(p), bucket_name, key)
                    uploaded.append(key)
                    success = True
                except Exception as e:
                    last_error = e
                    print(f"Upload attempt {attempt} failed for {p} -> s3://{bucket_name}/{key}: {e}")
                    time.sleep(1)

            if not success:
                # continue uploading other files but report the error
                print(f"Failed to upload {p} after {max_attempts} attempts: {last_error}")
    return uploaded
