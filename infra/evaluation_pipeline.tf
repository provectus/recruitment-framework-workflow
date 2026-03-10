data "aws_caller_identity" "eval_pipeline" {}
data "aws_region" "eval_pipeline" {}

locals {
  lambda_evaluation_functions = ["cv-analysis", "screening-eval", "technical-eval", "recommendation", "feedback-gen"]
  db_ssm_prefix               = "/${var.project_name}/db"
}

# ─── SSM Parameters: DB connection details for Lambda cold-start reads ───────

resource "aws_ssm_parameter" "db_host" {
  name        = "${local.db_ssm_prefix}/host"
  description = "RDS hostname for ${var.project_name} Lambda functions"
  type        = "String"
  value       = module.rds.db_instance_address

  tags = {
    Name = "${var.project_name}-db-host-param"
  }
}

resource "aws_ssm_parameter" "db_port" {
  name        = "${local.db_ssm_prefix}/port"
  description = "RDS port for ${var.project_name} Lambda functions"
  type        = "String"
  value       = tostring(module.rds.db_instance_port)

  tags = {
    Name = "${var.project_name}-db-port-param"
  }
}

resource "aws_ssm_parameter" "db_name" {
  name        = "${local.db_ssm_prefix}/name"
  description = "Database name for ${var.project_name} Lambda functions"
  type        = "String"
  value       = var.db_name

  tags = {
    Name = "${var.project_name}-db-name-param"
  }
}

resource "aws_ssm_parameter" "db_username" {
  name        = "${local.db_ssm_prefix}/username"
  description = "Database master username for ${var.project_name} Lambda functions"
  type        = "String"
  value       = var.db_username

  tags = {
    Name = "${var.project_name}-db-username-param"
  }
}

# ─── EventBridge ─────────────────────────────────────────────────────────────

resource "aws_cloudwatch_event_bus" "evaluation" {
  name = "${var.project_name}-evaluation-events"

  tags = {
    Name = "${var.project_name}-evaluation-events"
  }
}

resource "aws_cloudwatch_event_rule" "evaluation_requested" {
  name           = "${var.project_name}-evaluation-requested"
  description    = "Routes evaluation.requested events to the Step Functions state machine"
  event_bus_name = aws_cloudwatch_event_bus.evaluation.name

  event_pattern = jsonencode({
    source      = ["lauter.api"]
    detail-type = ["evaluation.requested"]
  })

  tags = {
    Name = "${var.project_name}-evaluation-requested-rule"
  }
}

resource "aws_cloudwatch_event_target" "sfn" {
  rule           = aws_cloudwatch_event_rule.evaluation_requested.name
  event_bus_name = aws_cloudwatch_event_bus.evaluation.name
  target_id      = "EvaluationPipelineStateMachine"
  arn            = aws_sfn_state_machine.evaluation_pipeline.arn
  role_arn       = aws_iam_role.eventbridge_sfn.arn
}

# ─── IAM: EventBridge → Step Functions ───────────────────────────────────────

resource "aws_iam_role" "eventbridge_sfn" {
  name = "${var.project_name}-eventbridge-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-eventbridge-sfn-role"
  }
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "${var.project_name}-eventbridge-sfn-policy"
  role = aws_iam_role.eventbridge_sfn.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "states:StartExecution"
        Resource = aws_sfn_state_machine.evaluation_pipeline.arn
      }
    ]
  })
}

# ─── Security Group: Lambda evaluation functions ─────────────────────────────

resource "aws_security_group" "lambda_evaluation" {
  name        = "${var.project_name}-lambda-evaluation"
  description = "Security group for evaluation Lambda functions"
  vpc_id      = module.networking.vpc_id

  egress {
    description     = "PostgreSQL to RDS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.networking.rds_security_group_id]
  }

  egress {
    description = "HTTPS to AWS APIs (Bedrock, S3, SSM, etc.) via NAT Gateway"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-lambda-evaluation-sg"
  }
}

# Allow Lambda security group to reach RDS
resource "aws_security_group_rule" "rds_from_lambda" {
  type                     = "ingress"
  description              = "PostgreSQL from evaluation Lambda functions"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = module.networking.rds_security_group_id
  source_security_group_id = aws_security_group.lambda_evaluation.id
}

# ─── IAM: Lambda evaluation role ─────────────────────────────────────────────

resource "aws_iam_role" "lambda_evaluation" {
  name = "${var.project_name}-lambda-evaluation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-evaluation-role"
  }
}

data "aws_iam_policy" "lambda_vpc_execution" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_evaluation_vpc" {
  role       = aws_iam_role.lambda_evaluation.name
  policy_arn = data.aws_iam_policy.lambda_vpc_execution.arn
}

resource "aws_iam_role_policy" "lambda_evaluation" {
  name = "${var.project_name}-lambda-evaluation-policy"
  role = aws_iam_role.lambda_evaluation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvoke"
        Effect = "Allow"
        Action = ["bedrock:InvokeModel"]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.eval_pipeline.region}::foundation-model/anthropic.claude-*"
        ]
      },
      {
        Sid    = "S3ReadFiles"
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = [
          "${module.s3.files_bucket_arn}/*"
        ]
      },
      {
        Sid    = "SSMReadDbParams"
        Effect = "Allow"
        Action = ["ssm:GetParameter", "ssm:GetParameters"]
        Resource = [
          aws_ssm_parameter.db_host.arn,
          aws_ssm_parameter.db_port.arn,
          aws_ssm_parameter.db_name.arn,
          aws_ssm_parameter.db_username.arn,
          module.rds.db_master_secret_arn,
        ]
      },
      {
        Sid    = "SecretsManagerReadDbPassword"
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          module.rds.db_master_secret_arn
        ]
      }
    ]
  })
}

# ─── Lambda Layer: shared code + dependencies ─────────────────────────────────

data "archive_file" "lambda_shared_layer" {
  type        = "zip"
  source_dir  = "${path.module}/../app/lambdas/shared"
  output_path = "${path.module}/.terraform/lambda_layers/shared.zip"
}

resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${var.project_name}-lambda-shared"
  description         = "Shared DB, Bedrock, S3, and prompt utilities for evaluation Lambdas"
  filename            = data.archive_file.lambda_shared_layer.output_path
  source_code_hash    = data.archive_file.lambda_shared_layer.output_base64sha256
  compatible_runtimes = ["python3.12"]

  lifecycle {
    create_before_destroy = true
  }
}

# ─── Lambda Function: cv-analysis ────────────────────────────────────────────

data "archive_file" "lambda_cv_analysis" {
  type        = "zip"
  source_dir  = "${path.module}/../app/lambdas/cv_analysis"
  output_path = "${path.module}/.terraform/lambda_functions/cv_analysis.zip"
}

resource "aws_cloudwatch_log_group" "lambda_cv_analysis" {
  name              = "/aws/lambda/${var.project_name}-cv-analysis"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-lambda-cv-analysis-logs"
  }
}

resource "aws_lambda_function" "cv_analysis" {
  function_name    = "${var.project_name}-cv-analysis"
  description      = "Analyzes candidate CVs against position requirements using Bedrock"
  role             = aws_iam_role.lambda_evaluation.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda_cv_analysis.output_path
  source_code_hash = data.archive_file.lambda_cv_analysis.output_base64sha256
  memory_size      = 512
  timeout          = 300
  layers           = [aws_lambda_layer_version.shared.arn]

  reserved_concurrent_executions = 10

  vpc_config {
    subnet_ids         = module.networking.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_evaluation.id]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      S3_BUCKET_NAME   = module.s3.files_bucket_id
      DB_HOST          = module.rds.db_instance_address
      DB_PORT          = tostring(module.rds.db_instance_port)
      DB_NAME          = var.db_name
      DB_USERNAME      = var.db_username
      DB_SSM_PREFIX    = local.db_ssm_prefix
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_cv_analysis,
    aws_iam_role_policy_attachment.lambda_evaluation_vpc,
  ]

  tags = {
    Name = "${var.project_name}-cv-analysis"
    Type = "evaluation-lambda"
  }
}

# ─── Lambda Function: screening-eval ─────────────────────────────────────────

data "archive_file" "lambda_screening_eval" {
  type        = "zip"
  source_dir  = "${path.module}/../app/lambdas/screening_eval"
  output_path = "${path.module}/.terraform/lambda_functions/screening_eval.zip"
}

resource "aws_cloudwatch_log_group" "lambda_screening_eval" {
  name              = "/aws/lambda/${var.project_name}-screening-eval"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-lambda-screening-eval-logs"
  }
}

resource "aws_lambda_function" "screening_eval" {
  function_name    = "${var.project_name}-screening-eval"
  description      = "Analyzes candidate screening interview transcripts against position requirements using Bedrock"
  role             = aws_iam_role.lambda_evaluation.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda_screening_eval.output_path
  source_code_hash = data.archive_file.lambda_screening_eval.output_base64sha256
  memory_size      = 512
  timeout          = 300
  layers           = [aws_lambda_layer_version.shared.arn]

  reserved_concurrent_executions = 10

  vpc_config {
    subnet_ids         = module.networking.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_evaluation.id]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      S3_BUCKET_NAME   = module.s3.files_bucket_id
      DB_HOST          = module.rds.db_instance_address
      DB_PORT          = tostring(module.rds.db_instance_port)
      DB_NAME          = var.db_name
      DB_USERNAME      = var.db_username
      DB_SSM_PREFIX    = local.db_ssm_prefix
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_screening_eval,
    aws_iam_role_policy_attachment.lambda_evaluation_vpc,
  ]

  tags = {
    Name = "${var.project_name}-screening-eval"
    Type = "evaluation-lambda"
  }
}

# ─── Lambda Function: technical-eval ─────────────────────────────────────────

data "archive_file" "lambda_technical_eval" {
  type        = "zip"
  source_dir  = "${path.module}/../app/lambdas/technical_eval"
  output_path = "${path.module}/.terraform/lambda_functions/technical_eval.zip"
}

resource "aws_cloudwatch_log_group" "lambda_technical_eval" {
  name              = "/aws/lambda/${var.project_name}-technical-eval"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-lambda-technical-eval-logs"
  }
}

resource "aws_lambda_function" "technical_eval" {
  function_name    = "${var.project_name}-technical-eval"
  description      = "Scores candidate technical interview transcripts against rubric criteria using Bedrock"
  role             = aws_iam_role.lambda_evaluation.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda_technical_eval.output_path
  source_code_hash = data.archive_file.lambda_technical_eval.output_base64sha256
  memory_size      = 512
  timeout          = 300
  layers           = [aws_lambda_layer_version.shared.arn]

  reserved_concurrent_executions = 10

  vpc_config {
    subnet_ids         = module.networking.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_evaluation.id]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      S3_BUCKET_NAME   = module.s3.files_bucket_id
      DB_HOST          = module.rds.db_instance_address
      DB_PORT          = tostring(module.rds.db_instance_port)
      DB_NAME          = var.db_name
      DB_USERNAME      = var.db_username
      DB_SSM_PREFIX    = local.db_ssm_prefix
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_technical_eval,
    aws_iam_role_policy_attachment.lambda_evaluation_vpc,
  ]

  tags = {
    Name = "${var.project_name}-technical-eval"
    Type = "evaluation-lambda"
  }
}

# ─── Lambda Function: recommendation ─────────────────────────────────────────

data "archive_file" "lambda_recommendation" {
  type        = "zip"
  source_dir  = "${path.module}/../app/lambdas/recommendation"
  output_path = "${path.module}/.terraform/lambda_functions/recommendation.zip"
}

resource "aws_cloudwatch_log_group" "lambda_recommendation" {
  name              = "/aws/lambda/${var.project_name}-recommendation"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-lambda-recommendation-logs"
  }
}

resource "aws_lambda_function" "recommendation" {
  function_name    = "${var.project_name}-recommendation"
  description      = "Aggregates prior evaluation results and produces a hire/no-hire recommendation using Bedrock"
  role             = aws_iam_role.lambda_evaluation.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda_recommendation.output_path
  source_code_hash = data.archive_file.lambda_recommendation.output_base64sha256
  memory_size      = 512
  timeout          = 300
  layers           = [aws_lambda_layer_version.shared.arn]

  reserved_concurrent_executions = 10

  vpc_config {
    subnet_ids         = module.networking.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_evaluation.id]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      S3_BUCKET_NAME   = module.s3.files_bucket_id
      DB_HOST          = module.rds.db_instance_address
      DB_PORT          = tostring(module.rds.db_instance_port)
      DB_NAME          = var.db_name
      DB_USERNAME      = var.db_username
      DB_SSM_PREFIX    = local.db_ssm_prefix
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_recommendation,
    aws_iam_role_policy_attachment.lambda_evaluation_vpc,
  ]

  tags = {
    Name = "${var.project_name}-recommendation"
    Type = "evaluation-lambda"
  }
}

# ─── Lambda Function: feedback-gen ───────────────────────────────────────────

data "archive_file" "lambda_feedback_gen" {
  type        = "zip"
  source_dir  = "${path.module}/../app/lambdas/feedback_gen"
  output_path = "${path.module}/.terraform/lambda_functions/feedback_gen.zip"
}

resource "aws_cloudwatch_log_group" "lambda_feedback_gen" {
  name              = "/aws/lambda/${var.project_name}-feedback-gen"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-lambda-feedback-gen-logs"
  }
}

resource "aws_lambda_function" "feedback_gen" {
  function_name    = "${var.project_name}-feedback-gen"
  description      = "Generates candidate-facing rejection feedback from aggregated evaluation results using Bedrock"
  role             = aws_iam_role.lambda_evaluation.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda_feedback_gen.output_path
  source_code_hash = data.archive_file.lambda_feedback_gen.output_base64sha256
  memory_size      = 512
  timeout          = 300
  layers           = [aws_lambda_layer_version.shared.arn]

  reserved_concurrent_executions = 10

  vpc_config {
    subnet_ids         = module.networking.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_evaluation.id]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID = var.bedrock_model_id
      S3_BUCKET_NAME   = module.s3.files_bucket_id
      DB_HOST          = module.rds.db_instance_address
      DB_PORT          = tostring(module.rds.db_instance_port)
      DB_NAME          = var.db_name
      DB_USERNAME      = var.db_username
      DB_SSM_PREFIX    = local.db_ssm_prefix
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_feedback_gen,
    aws_iam_role_policy_attachment.lambda_evaluation_vpc,
  ]

  tags = {
    Name = "${var.project_name}-feedback-gen"
    Type = "evaluation-lambda"
  }
}

# ─── Step Functions: CloudWatch log group ────────────────────────────────────

resource "aws_cloudwatch_log_group" "sfn_evaluation_pipeline" {
  name              = "/aws/states/${var.project_name}-evaluation-pipeline"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-sfn-evaluation-pipeline-logs"
  }
}

# ─── IAM: Step Functions role ─────────────────────────────────────────────────

resource "aws_iam_role" "sfn_evaluation_pipeline" {
  name = "${var.project_name}-sfn-evaluation-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-sfn-evaluation-pipeline-role"
  }
}

resource "aws_iam_role_policy" "sfn_evaluation_pipeline" {
  name = "${var.project_name}-sfn-evaluation-pipeline-policy"
  role = aws_iam_role.sfn_evaluation_pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeLambdas"
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = [
          aws_lambda_function.cv_analysis.arn,
          "${aws_lambda_function.cv_analysis.arn}:*",
          aws_lambda_function.screening_eval.arn,
          "${aws_lambda_function.screening_eval.arn}:*",
          aws_lambda_function.technical_eval.arn,
          "${aws_lambda_function.technical_eval.arn}:*",
          aws_lambda_function.recommendation.arn,
          "${aws_lambda_function.recommendation.arn}:*",
          aws_lambda_function.feedback_gen.arn,
          "${aws_lambda_function.feedback_gen.arn}:*",
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutLogEvents",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups",
        ]
        Resource = "*"
      }
    ]
  })
}

# ─── Step Functions State Machine: evaluation-pipeline ───────────────────────

resource "aws_sfn_state_machine" "evaluation_pipeline" {
  name     = "${var.project_name}-evaluation-pipeline"
  role_arn = aws_iam_role.sfn_evaluation_pipeline.arn
  type     = "STANDARD"

  definition = jsonencode({
    Comment = "Lauter evaluation pipeline — routes each evaluation.requested event to the appropriate Lambda"
    StartAt = "RouteByStepType"
    States = {
      RouteByStepType = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.detail.step_type"
            StringEquals = "cv_analysis"
            Next         = "InvokeCvAnalysis"
          },
          {
            Variable     = "$.detail.step_type"
            StringEquals = "screening_eval"
            Next         = "InvokeScreeningEval"
          },
          {
            Variable     = "$.detail.step_type"
            StringEquals = "technical_eval"
            Next         = "InvokeTechnicalEval"
          },
          {
            Variable     = "$.detail.step_type"
            StringEquals = "recommendation"
            Next         = "InvokeRecommendation"
          },
          {
            Variable     = "$.detail.step_type"
            StringEquals = "feedback_gen"
            Next         = "InvokeFeedbackGen"
          }
        ]
        Default = "UnknownStepType"
      }

      InvokeCvAnalysis = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.cv_analysis.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "result.$" = "$.Payload"
        }
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.TooManyRequestsException", "States.TaskFailed"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "MarkCvAnalysisFailed"
            ResultPath  = "$.error"
          }
        ]
        Next = "EvaluationComplete"
      }

      MarkCvAnalysisFailed = {
        Type = "Pass"
        Parameters = {
          "step_type" = "cv_analysis"
          "status"    = "failed"
          "error.$"   = "$.error.Cause"
        }
        Next = "EvaluationComplete"
      }

      InvokeScreeningEval = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.screening_eval.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "result.$" = "$.Payload"
        }
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.TooManyRequestsException", "States.TaskFailed"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "MarkScreeningEvalFailed"
            ResultPath  = "$.error"
          }
        ]
        Next = "EvaluationComplete"
      }

      MarkScreeningEvalFailed = {
        Type = "Pass"
        Parameters = {
          "step_type" = "screening_eval"
          "status"    = "failed"
          "error.$"   = "$.error.Cause"
        }
        Next = "EvaluationComplete"
      }

      InvokeTechnicalEval = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.technical_eval.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "result.$" = "$.Payload"
        }
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.TooManyRequestsException", "States.TaskFailed"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "MarkTechnicalEvalFailed"
            ResultPath  = "$.error"
          }
        ]
        Next = "InvokeRecommendation"
      }

      MarkTechnicalEvalFailed = {
        Type = "Pass"
        Parameters = {
          "step_type" = "technical_eval"
          "status"    = "failed"
          "error.$"   = "$.error.Cause"
        }
        Next = "EvaluationComplete"
      }

      InvokeRecommendation = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.recommendation.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "result.$" = "$.Payload"
        }
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.TooManyRequestsException", "States.TaskFailed"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "MarkRecommendationFailed"
            ResultPath  = "$.error"
          }
        ]
        Next = "EvaluationComplete"
      }

      MarkRecommendationFailed = {
        Type = "Pass"
        Parameters = {
          "step_type" = "recommendation"
          "status"    = "failed"
          "error.$"   = "$.error.Cause"
        }
        Next = "EvaluationComplete"
      }

      InvokeFeedbackGen = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.feedback_gen.arn
          "Payload.$"  = "$"
        }
        ResultSelector = {
          "result.$" = "$.Payload"
        }
        Retry = [
          {
            ErrorEquals     = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException", "Lambda.TooManyRequestsException", "States.TaskFailed"]
            IntervalSeconds = 5
            MaxAttempts     = 2
            BackoffRate     = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "MarkFeedbackGenFailed"
            ResultPath  = "$.error"
          }
        ]
        Next = "EvaluationComplete"
      }

      MarkFeedbackGenFailed = {
        Type = "Pass"
        Parameters = {
          "step_type" = "feedback_gen"
          "status"    = "failed"
          "error.$"   = "$.error.Cause"
        }
        Next = "EvaluationComplete"
      }

      UnknownStepType = {
        Type  = "Fail"
        Error = "UnknownStepType"
        Cause = "The step_type in the event detail did not match any known evaluation step"
      }

      EvaluationComplete = {
        Type = "Succeed"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn_evaluation_pipeline.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  depends_on = [aws_cloudwatch_log_group.sfn_evaluation_pipeline]

  tags = {
    Name = "${var.project_name}-evaluation-pipeline"
    Type = "state-machine"
  }
}
