provider "aws" {
  region = var.region
}

# VPC for honeypot isolation
resource "aws_vpc" "honeynet_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "DeceptiCloud-VPC"
  }
}

# Internet Gateway for public subnet
resource "aws_internet_gateway" "honeynet_igw" {
  vpc_id = aws_vpc.honeynet_vpc.id

  tags = {
    Name = "DeceptiCloud-IGW"
  }
}

# Public subnet (for honeypot - needs to be accessible)
resource "aws_subnet" "honeynet_public" {
  vpc_id                  = aws_vpc.honeynet_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "DeceptiCloud-Public-Subnet"
  }
}

# Private subnet (for management/control plane if needed)
resource "aws_subnet" "honeynet_private" {
  vpc_id            = aws_vpc.honeynet_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "DeceptiCloud-Private-Subnet"
  }
}

# Route table for public subnet
resource "aws_route_table" "honeynet_public_rt" {
  vpc_id = aws_vpc.honeynet_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.honeynet_igw.id
  }

  tags = {
    Name = "DeceptiCloud-Public-RT"
  }
}

# Associate route table with public subnet
resource "aws_route_table_association" "honeynet_public_rta" {
  subnet_id      = aws_subnet.honeynet_public.id
  route_table_id = aws_route_table.honeynet_public_rt.id
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/decepticloud-flow-logs"
  retention_in_days = 7

  tags = {
    Name = "DeceptiCloud-VPC-Flow-Logs"
  }
}

# IAM role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs_role" {
  name = "DeceptiCloudVPCFlowLogsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM policy for VPC Flow Logs
resource "aws_iam_role_policy" "vpc_flow_logs_policy" {
  name = "DeceptiCloudVPCFlowLogsPolicy"
  role = aws_iam_role.vpc_flow_logs_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# VPC Flow Logs
resource "aws_flow_log" "honeynet_flow_log" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs_role.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.honeynet_vpc.id

  tags = {
    Name = "DeceptiCloud-VPC-Flow-Log"
  }
}

# Security group for honeypot instance (restricted ingress)
resource "aws_security_group" "honeynet_sg" {
  name        = "honeynet-sg"
  description = "Allow necessary inbound traffic for honeypot (restricted)"
  vpc_id      = aws_vpc.honeynet_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 2222
    to_port     = 2222
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# S3 bucket for CloudTrail logs
resource "aws_s3_bucket" "cloudtrail_bucket" {
  bucket = "${var.s3_bucket_name}-cloudtrail"

  tags = {
    Name = "DeceptiCloud-CloudTrail-Logs"
  }
}

resource "aws_s3_bucket_policy" "cloudtrail_bucket_policy" {
  bucket = aws_s3_bucket.cloudtrail_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail_bucket.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail_bucket.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# CloudTrail for honeytoken monitoring
resource "aws_cloudtrail" "honeytoken_trail" {
  name                          = "decepticloud-honeytoken-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_bucket.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::*/"]
    }
  }

  tags = {
    Name = "DeceptiCloud-Honeytoken-Trail"
  }

  depends_on = [aws_s3_bucket_policy.cloudtrail_bucket_policy]
}

# CloudWatch Log Group for CloudTrail
resource "aws_cloudwatch_log_group" "cloudtrail_logs" {
  name              = "/aws/cloudtrail/decepticloud-honeytokens"
  retention_in_days = 30

  tags = {
    Name = "DeceptiCloud-Honeytoken-Logs"
  }
}

# SNS Topic for honeytoken alerts
resource "aws_sns_topic" "honeytoken_alerts" {
  name = "decepticloud-honeytoken-alerts"

  tags = {
    Name = "DeceptiCloud-Honeytoken-Alerts"
  }
}

# CloudWatch metric filter for unauthorized credential usage
resource "aws_cloudwatch_log_metric_filter" "honeytoken_usage" {
  name           = "HoneytokenUsageDetected"
  log_group_name = aws_cloudwatch_log_group.cloudtrail_logs.name
  pattern        = "[userIdentity.accessKeyId = AKIA3OEXAMPLEKEY123 || userIdentity.accessKeyId = AKIA3PRODKEY456789]"

  metric_transformation {
    name      = "HoneytokenUsageCount"
    namespace = "DeceptiCloud/Security"
    value     = "1"
  }
}

# CloudWatch alarm for honeytoken usage
resource "aws_cloudwatch_metric_alarm" "honeytoken_alarm" {
  alarm_name          = "DeceptiCloud-Honeytoken-Usage-Detected"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HoneytokenUsageCount"
  namespace           = "DeceptiCloud/Security"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Alert when honeytoken credentials are used"
  alarm_actions       = [aws_sns_topic.honeytoken_alerts.arn]

  tags = {
    Name = "DeceptiCloud-Honeytoken-Alarm"
  }
}

# Optional S3 bucket for results
resource "aws_s3_bucket" "results_bucket" {
  count = var.create_s3_bucket ? 1 : 0
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_acl" "results_bucket_acl" {
  count = var.create_s3_bucket ? 1 : 0
  bucket = aws_s3_bucket.results_bucket[0].id
  acl    = "private"
  depends_on = [aws_s3_bucket_ownership_controls.results_bucket_ownership]
}

resource "aws_s3_bucket_ownership_controls" "results_bucket_ownership" {
  count = var.create_s3_bucket ? 1 : 0
  bucket = aws_s3_bucket.results_bucket[0].id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# IAM role and policy for SSM + S3 access
resource "aws_iam_role" "decepticloud_role" {
  name = "DeceptiCloudInstanceRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "decepticloud_policy" {
  name = "DeceptiCloudSSMS3Policy"
  role = aws_iam_role.decepticloud_role.id

  policy = var.create_s3_bucket ? replace(file("${path.module}/ssm_s3_role_policy.json"), "REPLACE_WITH_YOUR_BUCKET", var.s3_bucket_name) : jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "AllowSSMRunCommand"
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations",
          "ssm:ListCommands"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "decepticloud_profile" {
  name = "DeceptiCloudInstanceProfile"
  role = aws_iam_role.decepticloud_role.name
}

resource "aws_instance" "honeynet_ec2" {
  ami           = var.ami
  instance_type = var.instance_type

  subnet_id              = aws_subnet.honeynet_public.id
  vpc_security_group_ids = [aws_security_group.honeynet_sg.id]

  key_name = var.key_name

  iam_instance_profile = aws_iam_instance_profile.decepticloud_profile.name

  user_data = <<-EOF
              #!/bin/bash
              set -e

              # Update system
              apt-get update
              apt-get install -y docker.io docker-compose git curl

              # Start and enable Docker
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ubuntu

              # Create directories for Docker volumes
              mkdir -p /opt/decepticloud/cowrie/{logs,downloads,filesystem}
              mkdir -p /opt/decepticloud/nginx/{logs,content}
              mkdir -p /opt/decepticloud/config

              # Download and build custom Docker images
              cd /opt/decepticloud

              # Pull base images
              docker pull cowrie/cowrie:latest
              docker pull nginx:alpine

              # Create docker-compose.yml for honeypot orchestration
              cat > docker-compose.yml << 'COMPOSE_EOF'
              version: '3.8'

              services:
                cowrie:
                  image: cowrie/cowrie:latest
                  container_name: cowrie_honeypot
                  ports:
                    - "2222:2222"
                  volumes:
                    - /opt/decepticloud/cowrie/logs:/cowrie/cowrie-git/var/log/cowrie
                    - /opt/decepticloud/cowrie/downloads:/cowrie/cowrie-git/var/lib/cowrie/downloads
                  environment:
                    - COWRIE_HOSTNAME=ip-10-0-1-42
                    - COWRIE_SSH_VERSION_STRING=SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6
                  restart: unless-stopped
                  healthcheck:
                    test: ["CMD", "nc", "-z", "localhost", "2222"]
                    interval: 30s
                    timeout: 10s
                    retries: 3
                    start_period: 40s

                nginx:
                  image: nginx:alpine
                  container_name: nginx_honeypot
                  ports:
                    - "80:80"
                  volumes:
                    - /opt/decepticloud/nginx/logs:/var/log/nginx
                    - /opt/decepticloud/nginx/content:/usr/share/nginx/html:ro
                  restart: unless-stopped
                  healthcheck:
                    test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
                    interval: 30s
                    timeout: 10s
                    retries: 3
                    start_period: 20s
              COMPOSE_EOF

              # Create realistic web content
              cat > /opt/decepticloud/nginx/content/index.html << 'HTML_EOF'
              <!DOCTYPE html>
              <html lang="en">
              <head>
                  <meta charset="UTF-8">
                  <title>Production API Gateway</title>
              </head>
              <body>
                  <h1>Production API Gateway</h1>
                  <p class="status">All Systems Operational</p>
                  <p>Build: v1.2.3-a4f8d9c</p>
              </body>
              </html>
              HTML_EOF

              # Start honeypots
              docker-compose up -d

              # Set proper permissions
              chown -R ubuntu:ubuntu /opt/decepticloud

              # Log completion
              echo "DeceptiCloud honeypot deployment completed at $(date)" >> /var/log/decepticloud-init.log
              EOF

  tags = {
    Name = "DeceptiCloud-Honeynet-Instance"
  }
}

output "public_ip" {
  value = aws_instance.honeynet_ec2.public_ip
  description = "Public IP address of the honeypot EC2 instance"
}

output "instance_id" {
  value = aws_instance.honeynet_ec2.id
  description = "ID of the honeypot EC2 instance"
}

output "vpc_id" {
  value = aws_vpc.honeynet_vpc.id
  description = "ID of the DeceptiCloud VPC"
}

output "vpc_flow_log_group" {
  value = aws_cloudwatch_log_group.vpc_flow_logs.name
  description = "CloudWatch log group for VPC Flow Logs"
}

output "cloudtrail_bucket" {
  value = aws_s3_bucket.cloudtrail_bucket.bucket
  description = "S3 bucket for CloudTrail logs"
}

output "honeytoken_alerts_topic" {
  value = aws_sns_topic.honeytoken_alerts.arn
  description = "SNS topic ARN for honeytoken alerts - subscribe your email here"
}

output "ssh_honeypot_url" {
  value = "ssh -p 2222 ubuntu@${aws_instance.honeynet_ec2.public_ip}"
  description = "Command to connect to SSH honeypot"
}

output "web_honeypot_url" {
  value = "http://${aws_instance.honeynet_ec2.public_ip}"
  description = "URL for web honeypot"
}
