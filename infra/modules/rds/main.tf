resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.project_name}-${var.environment}-db-subnet-group"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-${var.environment}-postgres16"
  family = "postgres16"

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgres16"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_db_instance" "this" {
  identifier = "${var.project_name}-${var.environment}-db"

  engine            = "postgres"
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name                     = var.db_name
  username                    = "tap_admin"
  manage_master_user_password = true

  multi_az               = false
  publicly_accessible    = false
  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.this.name
  parameter_group_name   = aws_db_parameter_group.this.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot   = true
  deletion_protection   = false
  apply_immediately     = true
  copy_tags_to_snapshot = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-db"
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
