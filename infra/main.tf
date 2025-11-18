provider "aws" {
  region = var.region
}

# Security group for honeypot instance
resource "aws_security_group" "honeynet_sg" {
  name        = "honeynet-sg"
  description = "Allow necessary inbound traffic for honeypot"

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

  vpc_security_group_ids = [aws_security_group.honeynet_sg.id]

  key_name = var.key_name

  iam_instance_profile = aws_iam_instance_profile.decepticloud_profile.name

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update
              sudo apt-get install -y docker.io
              sudo systemctl start docker
              sudo systemctl enable docker
              sudo usermod -aG docker ubuntu
              EOF

  tags = {
    Name = "DeceptiCloud-Honeynet-Instance"
  }
}
