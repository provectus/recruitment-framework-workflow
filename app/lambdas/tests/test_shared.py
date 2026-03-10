import json
import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
os.environ.setdefault("AWS_REGION", "us-east-1")


class TestS3GetDocumentText:
    def test_plain_text(self):
        from shared import s3 as s3_module

        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: b"Hello, world!")
        }

        with patch.object(s3_module, "get_client", return_value=mock_client):
            result = s3_module.get_document_text("resume.txt")

        assert result == "Hello, world!"
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="resume.txt"
        )

    def test_pdf_extraction(self):
        from shared import s3 as s3_module

        mock_client = MagicMock()
        pdf_bytes = b"%PDF-1.4 fake content"
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: pdf_bytes)
        }

        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF text"
        mock_reader.pages = [mock_page]

        with (
            patch.object(s3_module, "get_client", return_value=mock_client),
            patch.object(s3_module, "PdfReader", return_value=mock_reader),
        ):
            result = s3_module.get_document_text("resume.pdf")

        assert result == "Extracted PDF text"

    def test_docx_extraction(self):
        from shared import s3 as s3_module

        mock_client = MagicMock()
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: b"fake docx bytes")
        }

        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "Paragraph text"
        mock_doc.paragraphs = [mock_para]

        with (
            patch.object(s3_module, "get_client", return_value=mock_client),
            patch.object(s3_module, "docx") as mock_docx_module,
        ):
            mock_docx_module.Document.return_value = mock_doc
            result = s3_module.get_document_text("resume.docx")

        assert result == "Paragraph text"

    def test_file_not_found_raises(self):
        from shared import s3 as s3_module

        mock_client = MagicMock()
        mock_client.exceptions.NoSuchKey = KeyError
        mock_client.get_object.side_effect = KeyError("NoSuchKey")

        with (
            patch.object(s3_module, "get_client", return_value=mock_client),
            pytest.raises(FileNotFoundError),
        ):
            s3_module.get_document_text("missing.txt")


class TestBedrockInvokeClaude:
    def _make_mock_client(self, response_text: str) -> MagicMock:
        mock_client = MagicMock()
        mock_client.exceptions.ThrottlingException = type(
            "ThrottlingException", (Exception,), {}
        )
        mock_client.exceptions.ModelTimeoutException = type(
            "ModelTimeoutException", (Exception,), {}
        )
        payload = {"content": [{"text": response_text}]}
        mock_response = {
            "body": MagicMock(read=lambda: json.dumps(payload).encode())
        }
        mock_client.invoke_model.return_value = mock_response
        return mock_client

    def test_returns_text(self):
        from shared import bedrock as bedrock_module

        mock_client = self._make_mock_client("Claude response text")

        with patch.object(bedrock_module, "get_client", return_value=mock_client):
            result = bedrock_module.invoke_claude("Hello")

        assert result == "Claude response text"

    def test_sends_system_prompt(self):
        from shared import bedrock as bedrock_module

        mock_client = self._make_mock_client("response")

        with patch.object(bedrock_module, "get_client", return_value=mock_client):
            bedrock_module.invoke_claude("user msg", system_prompt="be helpful")

        call_kwargs = mock_client.invoke_model.call_args[1]
        body = json.loads(call_kwargs["body"])
        assert body["system"] == "be helpful"
        assert body["messages"][0]["content"] == "user msg"

    def test_retries_on_throttling(self):
        from shared import bedrock as bedrock_module

        ThrottlingException = type("ThrottlingException", (Exception,), {})
        mock_client = MagicMock()
        mock_client.exceptions.ThrottlingException = ThrottlingException
        mock_client.exceptions.ModelTimeoutException = type(
            "ModelTimeoutException", (Exception,), {}
        )

        payload = {"content": [{"text": "ok"}]}
        success_response = {
            "body": MagicMock(read=lambda: json.dumps(payload).encode())
        }
        mock_client.invoke_model.side_effect = [
            ThrottlingException("throttled"),
            success_response,
        ]

        with (
            patch.object(bedrock_module, "get_client", return_value=mock_client),
            patch("shared.bedrock.time.sleep"),
        ):
            result = bedrock_module.invoke_claude("Hello")

        assert result == "ok"
        assert mock_client.invoke_model.call_count == 2


class TestCvAnalysisPromptBuilder:
    def test_returns_tuple(self):
        from shared.prompts.cv_analysis import build_cv_analysis_prompt

        system_prompt, user_prompt = build_cv_analysis_prompt(
            position_title="Python Engineer",
            position_description="Build backend services",
            required_skills=["Python", "FastAPI"],
            cv_text="5 years Python experience",
        )

        assert isinstance(system_prompt, str)
        assert isinstance(user_prompt, str)
        assert len(system_prompt) > 0
        assert len(user_prompt) > 0

    def test_user_prompt_contains_position_info(self):
        from shared.prompts.cv_analysis import build_cv_analysis_prompt

        _, user_prompt = build_cv_analysis_prompt(
            position_title="Senior Python Engineer",
            position_description="Build scalable APIs",
            required_skills=["Python", "PostgreSQL"],
            cv_text="Experienced developer",
        )

        assert "Senior Python Engineer" in user_prompt
        assert "Build scalable APIs" in user_prompt
        assert "Python" in user_prompt
        assert "PostgreSQL" in user_prompt
        assert "Experienced developer" in user_prompt

    def test_system_prompt_instructs_json(self):
        from shared.prompts.cv_analysis import build_cv_analysis_prompt

        system_prompt, _ = build_cv_analysis_prompt(
            position_title="Role",
            position_description="Desc",
            required_skills=[],
            cv_text="CV",
        )

        assert "JSON" in system_prompt
        assert "skills_match" in system_prompt
        assert "overall_fit" in system_prompt
