# Contains bad patterns to test the pipeline

resource "aws_s3_bucket" "example1" {
  bucket = "my-test-bucket"
  acl    = "public-read" # Checkov: bucket publicly readable
}

resource "aws_db_instance" "prod" {
  identifier          = "prod-db"
  instance_class      = "db.t3.micro"
  engine              = "mysql"
  engine_version      = "8.0"
  username            = "admin"
  password            = "hardcoded_password_123" # Checkov: hardcoded secret
  publicly_accessible = true                     # Checkov: exposed to internet
  deletion_protection = false                    # Checkov: no deletion protection
  storage_encrypted   = false                    # Checkov: no encryption
  allocated_storage   = 20
  skip_final_snapshot = true
}

resource "aws_security_group" "open" {
  name = "open-sg"

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Checkov: open to entire internet
  }
}

