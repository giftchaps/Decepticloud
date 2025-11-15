variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "key_name" {
  description = "Name of the EC2 keypair to use"
  type        = string
  default     = "your-key-name"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ami" {
  description = "AMI id to use for the EC2 instance"
  type        = string
  default     = "ami-0c7217cdde317cfec"
}

variable "create_s3_bucket" {
  description = "Whether to create an S3 bucket for results uploads"
  type        = bool
  default     = false
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket to create/use for results (if create_s3_bucket=true)"
  type        = string
  default     = ""
}
