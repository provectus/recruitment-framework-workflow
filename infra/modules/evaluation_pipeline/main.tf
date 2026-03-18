data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

locals {
  db_ssm_prefix = "/${var.project_name}/db"

  evaluation_functions = {
    "cv-analysis" = {
      description = "Analyzes candidate CVs against position requirements using Bedrock"
      source_dir  = "cv_analysis"
      model_id    = var.bedrock_model_id_light
    }
    "screening-eval" = {
      description = "Analyzes candidate screening interview transcripts against position requirements using Bedrock"
      source_dir  = "screening_eval"
      model_id    = var.bedrock_model_id_heavy
    }
    "technical-eval" = {
      description = "Scores candidate technical interview transcripts against rubric criteria using Bedrock"
      source_dir  = "technical_eval"
      model_id    = var.bedrock_model_id_heavy
    }
    "recommendation" = {
      description = "Aggregates prior evaluation results and produces a hire/no-hire recommendation using Bedrock"
      source_dir  = "recommendation"
      model_id    = var.bedrock_model_id_heavy
    }
    "feedback-gen" = {
      description = "Generates candidate-facing rejection feedback from aggregated evaluation results using Bedrock"
      source_dir  = "feedback_gen"
      model_id    = var.bedrock_model_id_light
    }
  }
}

# ─── SSM Parameters: DB connection details for Lambda cold-start reads ───────

resource "aws_ssm_parameter" "db_host" {
  name        = "${local.db_ssm_prefix}/host"
  description = "RDS hostname for ${var.project_name} Lambda functions"
  type        = "String"
  value       = var.rds_instance_address

  tags = {
    Name = "${var.project_name}-db-host-param"
  }
}

resource "aws_ssm_parameter" "db_port" {
  name        = "${local.db_ssm_prefix}/port"
  description = "RDS port for ${var.project_name} Lambda functions"
  type        = "String"
  value       = tostring(var.rds_instance_port)

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
  vpc_id      = var.vpc_id

  egress {
    description     = "PostgreSQL to RDS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.rds_security_group_id]
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

resource "aws_security_group_rule" "rds_from_lambda" {
  type                     = "ingress"
  description              = "PostgreSQL from evaluation Lambda functions"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.rds_security_group_id
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
          "arn:aws:bedrock:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:inference-profile/${var.bedrock_model_id_heavy}",
          "arn:aws:bedrock:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:inference-profile/${var.bedrock_model_id_light}",
          "arn:aws:bedrock:*::foundation-model/anthropic.*",
        ]
      },
      {
        Sid    = "S3ReadFiles"
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = [
          "${var.files_bucket_arn}/*"
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
        ]
      },
      {
        Sid    = "SecretsManagerReadDbPassword"
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          var.db_master_secret_arn
        ]
      }
    ]
  })
}

# ─── Lambda Layer: shared code + pip dependencies ────────────────────────────

locals {
  layer_build_dir = "${abspath(path.module)}/.terraform/lambda_layer_build"
  layer_zip_path  = "${abspath(path.module)}/.terraform/lambda_layers/shared.zip"

  shared_source_hash = sha256(join("", [
    for f in sort(fileset("${var.lambdas_source_path}/shared", "**")) :
    filesha256("${var.lambdas_source_path}/shared/${f}")
    if !strcontains(f, "__pycache__")
  ]))
  requirements_hash = filesha256("${var.lambdas_source_path}/requirements-layer.txt")
  layer_hash        = sha256("${local.shared_source_hash}-${local.requirements_hash}")
}

resource "null_resource" "lambda_layer_build" {
  triggers = {
    layer_hash = local.layer_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      rm -rf "${local.layer_build_dir}"
      mkdir -p "${local.layer_build_dir}/python/shared"

      cp -r "${var.lambdas_source_path}/shared/"* "${local.layer_build_dir}/python/shared/"
      find "${local.layer_build_dir}" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

      python3 -m pip install --quiet --target "${local.layer_build_dir}/python" \
        --platform manylinux2014_x86_64 --implementation cp --python-version 3.12 \
        --only-binary=:all: --no-deps \
        -r "${var.lambdas_source_path}/requirements-layer.txt"

      mkdir -p "$(dirname "${local.layer_zip_path}")"
      cd "${local.layer_build_dir}"
      zip -qr "${local.layer_zip_path}" python/
    EOT
  }
}

resource "aws_lambda_layer_version" "shared" {
  layer_name          = "${var.project_name}-lambda-shared"
  description         = "Shared DB, Bedrock, S3, and prompt utilities for evaluation Lambdas"
  filename            = local.layer_zip_path
  source_code_hash    = local.layer_hash
  compatible_runtimes = ["python3.12"]

  depends_on = [null_resource.lambda_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}

# ─── Lambda Functions: evaluation (for_each) ─────────────────────────────────

data "archive_file" "lambda_function" {
  for_each    = local.evaluation_functions
  type        = "zip"
  source_dir  = "${var.lambdas_source_path}/${each.value.source_dir}"
  output_path = "${path.module}/.terraform/lambda_functions/${each.value.source_dir}.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = local.evaluation_functions
  name              = "/aws/lambda/${var.project_name}-${each.key}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-lambda-${each.key}-logs"
  }
}

resource "aws_lambda_function" "evaluation" {
  for_each         = local.evaluation_functions
  function_name    = "${var.project_name}-${each.key}"
  description      = each.value.description
  role             = aws_iam_role.lambda_evaluation.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.lambda_function[each.key].output_path
  source_code_hash = data.archive_file.lambda_function[each.key].output_base64sha256
  memory_size      = 512
  timeout          = 300
  layers           = [aws_lambda_layer_version.shared.arn]

  reserved_concurrent_executions = 10

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_evaluation.id]
  }

  environment {
    variables = {
      BEDROCK_MODEL_ID       = each.value.model_id
      S3_BUCKET_NAME         = var.files_bucket_id
      DB_PASSWORD_SECRET_ARN = var.db_master_secret_arn
      DB_SSM_PREFIX          = local.db_ssm_prefix
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_evaluation_vpc,
  ]

  tags = {
    Name = "${var.project_name}-${each.key}"
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

# CloudWatch Logs resource policy — allows Step Functions to deliver logs
resource "aws_cloudwatch_log_resource_policy" "sfn_logging" {
  policy_name = "${var.project_name}-sfn-logs-policy"
  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = [
          "logs:PutLogEvents",
          "logs:CreateLogStream",
          "logs:DescribeLogStreams",
        ]
        Resource = "${aws_cloudwatch_log_group.sfn_evaluation_pipeline.arn}:*"
      }
    ]
  })
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
        Resource = flatten([
          for key, fn in aws_lambda_function.evaluation : [fn.arn, "${fn.arn}:*"]
        ])
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:CreateLogStream",
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
          FunctionName = aws_lambda_function.evaluation["cv-analysis"].arn
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
          FunctionName = aws_lambda_function.evaluation["screening-eval"].arn
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
          FunctionName = aws_lambda_function.evaluation["technical-eval"].arn
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
        Next = "EvaluationComplete"
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
          FunctionName = aws_lambda_function.evaluation["recommendation"].arn
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
          FunctionName = aws_lambda_function.evaluation["feedback-gen"].arn
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

  depends_on = [
    aws_cloudwatch_log_group.sfn_evaluation_pipeline,
    aws_cloudwatch_log_resource_policy.sfn_logging,
  ]

  tags = {
    Name = "${var.project_name}-evaluation-pipeline"
    Type = "state-machine"
  }
}
