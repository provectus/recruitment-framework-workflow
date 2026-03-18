resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

resource "aws_db_parameter_group" "this" {
  name   = "${var.project_name}-${var.environment}-postgres16"
  family = "postgres16"

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres16"
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
  username                    = var.db_username
  manage_master_user_password = true

  multi_az               = var.multi_az
  publicly_accessible    = false
  vpc_security_group_ids = [var.rds_security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.this.name
  parameter_group_name   = aws_db_parameter_group.this.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  skip_final_snapshot   = var.environment != "prod"
  deletion_protection   = var.environment == "prod"
  apply_immediately     = var.environment != "prod"
  copy_tags_to_snapshot = true

  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  max_allocated_storage                 = var.max_allocated_storage

  tags = {
    Name = "${var.project_name}-${var.environment}-db"
  }
}
