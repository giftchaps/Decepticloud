Infra notes

This folder contains Terraform configuration used to create the EC2 instance, security group, optional S3 bucket, and an IAM role/instance-profile for SSM and S3 access.

Usage
1. Edit `variables.tf` to set `key_name`, `region`, and optionally `create_s3_bucket` and `s3_bucket_name`.
2. Run `terraform init` and `terraform apply` inside this folder.
3. After apply completes, note `public_ip` and `instance_id` from outputs.

Before you run
- If you enable `create_s3_bucket` set `s3_bucket_name` to a globally unique bucket name.
- The `ssm_s3_role_policy.json` file contains a placeholder `REPLACE_WITH_YOUR_BUCKET`. If you create a bucket manually, replace that placeholder in the JSON or set `s3_bucket_name` and let Terraform create the bucket for you.
