from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.dependencies.auth import get_current_user
from app.main import app
from app.models.candidate import Candidate
from app.models.candidate_position import CandidatePosition
from app.models.enums import DocumentStatus
from app.models.position import Position
from app.models.team import Team
from app.models.user import User


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    user = User(
        email="test@provectus.com",
        google_id="test123",
        full_name="Test User",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(autouse=True)
def override_auth(test_user: User):
    mock_user = User(
        id=test_user.id,
        email=test_user.email,
        google_id=test_user.google_id,
        full_name=test_user.full_name,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def candidate_position(session: AsyncSession) -> CandidatePosition:
    candidate = Candidate(
        full_name="Alice Johnson",
        email="alice@example.com",
    )
    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)

    team = Team(name="Engineering")
    session.add(team)
    await session.commit()
    await session.refresh(team)

    user = User(
        email="hm@provectus.com",
        google_id="hm123",
        full_name="Hiring Manager",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    position = Position(
        title="Backend Engineer",
        team_id=team.id,
        hiring_manager_id=user.id,
        status="open",
    )
    session.add(position)
    await session.commit()
    await session.refresh(position)

    cp = CandidatePosition(
        candidate_id=candidate.id,
        position_id=position.id,
        stage="new",
    )
    session.add(cp)
    await session.commit()
    await session.refresh(cp)

    return cp


@pytest.fixture
async def interviewer(session: AsyncSession) -> User:
    user = User(
        email="interviewer@provectus.com",
        google_id="interviewer123",
        full_name="Jane Interviewer",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@patch("app.services.storage_service.generate_upload_url")
async def test_presign_cv_happy_path(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["upload_url"] == "https://s3.amazonaws.com/fake-upload-url"
    assert "s3_key" in data
    assert "documents/" in data["s3_key"]
    assert "resume.pdf" in data["s3_key"]

    mock_generate_upload_url.assert_called_once()
    call_kwargs = mock_generate_upload_url.call_args.kwargs
    assert call_kwargs["content_type"] == "application/pdf"
    assert call_kwargs["max_size"] == 1024000


@patch("app.services.storage_service.generate_upload_url")
async def test_presign_transcript_happy_path(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "interview-transcript.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
            "notes": "First round technical interview",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert data["upload_url"] == "https://s3.amazonaws.com/fake-upload-url"
    assert "s3_key" in data
    assert "documents/" in data["s3_key"]
    assert "interview-transcript.txt" in data["s3_key"]


@patch("app.services.storage_service.generate_upload_url")
async def test_complete_upload_happy_path(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    session: AsyncSession,
    candidate_position: CandidatePosition,
    test_user: User,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    presign_response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign_response.status_code == 201
    document_id = presign_response.json()["document_id"]

    complete_response = await client.post(f"/api/documents/{document_id}/complete")
    assert complete_response.status_code == 200

    data = complete_response.json()
    assert data["id"] == document_id
    assert data["status"] == DocumentStatus.active
    assert data["type"] == "cv"
    assert data["candidate_position_id"] == candidate_position.id
    assert data["file_name"] == "resume.pdf"
    assert data["content_type"] == "application/pdf"
    assert data["file_size"] == 1024000
    assert data["uploaded_by_id"] == test_user.id
    assert data["uploaded_by_name"] == "Test User"
    assert "created_at" in data
    assert "updated_at" in data


async def test_presign_oversize_file(
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "huge-resume.pdf",
            "content_type": "application/pdf",
            "file_size": 26_214_401,
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        "file_size" in str(error).lower() or "25 MB" in str(error)
        for error in data["detail"]
    )


async def test_presign_bad_content_type(
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024000,
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("content_type" in str(error).lower() for error in data["detail"])


async def test_presign_missing_transcript_metadata_interview_stage(
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "transcript.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        "interview_stage" in str(error).lower() or "required" in str(error).lower()
        for error in data["detail"]
    )


async def test_presign_missing_transcript_metadata_interviewer_id(
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "transcript.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interview_stage": "technical",
            "interview_date": "2025-01-15",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        "interviewer_id" in str(error).lower() or "required" in str(error).lower()
        for error in data["detail"]
    )


async def test_presign_missing_transcript_metadata_interview_date(
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "transcript.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        "interview_date" in str(error).lower() or "required" in str(error).lower()
        for error in data["detail"]
    )


async def test_presign_invalid_document_type(
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "invalid",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any("type" in str(error).lower() for error in data["detail"])


async def test_presign_nonexistent_candidate_position_id(client: AsyncClient):
    response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": 99999,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@patch("app.services.storage_service.generate_upload_url")
async def test_complete_already_completed_document(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    session: AsyncSession,
    candidate_position: CandidatePosition,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    presign_response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign_response.status_code == 201
    document_id = presign_response.json()["document_id"]

    first_complete = await client.post(f"/api/documents/{document_id}/complete")
    assert first_complete.status_code == 200

    second_complete = await client.post(f"/api/documents/{document_id}/complete")
    assert second_complete.status_code == 409
    data = second_complete.json()
    assert "detail" in data
    assert "already completed" in data["detail"].lower()


async def test_complete_nonexistent_document(client: AsyncClient):
    response = await client.post("/api/documents/99999/complete")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@patch("app.services.storage_service.generate_upload_url")
async def test_presign_all_allowed_content_types(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    allowed_types = [
        ("resume.pdf", "application/pdf"),
        (
            "resume.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("notes.md", "text/markdown"),
        ("transcript.txt", "text/plain"),
    ]

    for file_name, content_type in allowed_types:
        response = await client.post(
            "/api/documents/presign",
            json={
                "type": "cv",
                "candidate_position_id": candidate_position.id,
                "file_name": file_name,
                "content_type": content_type,
                "file_size": 1024000,
            },
        )
        assert response.status_code == 201, f"Failed for {content_type}"


@patch("app.services.storage_service.generate_upload_url")
async def test_complete_returns_interviewer_name(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    session: AsyncSession,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    presign_response = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "transcript.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
        },
    )
    assert presign_response.status_code == 201
    document_id = presign_response.json()["document_id"]

    complete_response = await client.post(f"/api/documents/{document_id}/complete")
    assert complete_response.status_code == 200

    data = complete_response.json()
    assert data["interviewer_id"] == interviewer.id
    assert data["interviewer_name"] == "Jane Interviewer"
    assert data["interview_stage"] == "technical"
    assert data["interview_date"] == "2025-01-15"


@patch("app.services.storage_service.put_text_object")
async def test_paste_transcript_happy_path(
    mock_put_text_object: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    mock_put_text_object.return_value = None

    response = await client.post(
        "/api/documents/paste",
        json={
            "candidate_position_id": candidate_position.id,
            "content": "This is the interview transcript content.",
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
            "notes": "Great technical discussion",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == DocumentStatus.active
    assert data["type"] == "transcript"
    assert data["input_method"] == "paste"
    assert data["interview_stage"] == "technical"
    assert data["interviewer_id"] == interviewer.id
    assert data["interviewer_name"] == "Jane Interviewer"
    assert data["interview_date"] == "2025-01-15"
    assert data["notes"] == "Great technical discussion"
    assert data["content_type"] == "text/plain"
    assert data["file_name"] is None

    mock_put_text_object.assert_called_once()
    call_args = mock_put_text_object.call_args.args
    assert "documents/" in call_args[0]
    assert call_args[1] == "This is the interview transcript content."
    assert call_args[2] == "text/plain"


async def test_paste_transcript_missing_metadata_interview_stage(
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    response = await client.post(
        "/api/documents/paste",
        json={
            "candidate_position_id": candidate_position.id,
            "content": "This is the interview transcript content.",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


async def test_paste_transcript_empty_content(
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    response = await client.post(
        "/api/documents/paste",
        json={
            "candidate_position_id": candidate_position.id,
            "content": "",
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@patch("app.services.storage_service.generate_view_url")
@patch("app.services.storage_service.generate_upload_url")
async def test_get_document_with_view_url(
    mock_generate_upload_url: AsyncMock,
    mock_generate_view_url: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"
    mock_generate_view_url.return_value = "https://s3.example.com/view-url"

    presign_response = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign_response.status_code == 201
    document_id = presign_response.json()["document_id"]

    complete_response = await client.post(f"/api/documents/{document_id}/complete")
    assert complete_response.status_code == 200

    get_response = await client.get(f"/api/documents/{document_id}")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["id"] == document_id
    assert data["view_url"] == "https://s3.example.com/view-url"
    assert data["type"] == "cv"
    assert data["file_name"] == "resume.pdf"

    mock_generate_view_url.assert_called_once()
    call_kwargs = mock_generate_view_url.call_args.kwargs
    assert call_kwargs["expiration"] == 3600


async def test_get_nonexistent_document(client: AsyncClient):
    response = await client.get("/api/documents/999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@patch("app.services.storage_service.generate_upload_url")
async def test_list_candidate_documents(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    presign_cv = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign_cv.status_code == 201
    cv_id = presign_cv.json()["document_id"]
    await client.post(f"/api/documents/{cv_id}/complete")

    presign_transcript = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "interview.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
        },
    )
    assert presign_transcript.status_code == 201
    transcript_id = presign_transcript.json()["document_id"]
    await client.post(f"/api/documents/{transcript_id}/complete")

    response = await client.get(
        f"/api/candidates/{candidate_position.candidate_id}/documents"
    )

    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 2
    assert any(doc["id"] == cv_id for doc in documents)
    assert any(doc["id"] == transcript_id for doc in documents)


@patch("app.services.storage_service.generate_upload_url")
async def test_list_candidate_documents_with_position_filter(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    session: AsyncSession,
    candidate_position: CandidatePosition,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    first_position = await session.get(Position, candidate_position.position_id)
    assert first_position is not None

    second_position = Position(
        title="Frontend Engineer",
        team_id=first_position.team_id,
        hiring_manager_id=first_position.hiring_manager_id,
        status="open",
    )
    session.add(second_position)
    await session.commit()
    await session.refresh(second_position)

    second_cp = CandidatePosition(
        candidate_id=candidate_position.candidate_id,
        position_id=second_position.id,
        stage="new",
    )
    session.add(second_cp)
    await session.commit()
    await session.refresh(second_cp)

    presign1 = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume1.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign1.status_code == 201
    doc1_id = presign1.json()["document_id"]
    await client.post(f"/api/documents/{doc1_id}/complete")

    presign2 = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": second_cp.id,
            "file_name": "resume2.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign2.status_code == 201
    doc2_id = presign2.json()["document_id"]
    await client.post(f"/api/documents/{doc2_id}/complete")

    response = await client.get(
        f"/api/candidates/{candidate_position.candidate_id}/documents",
        params={"position_id": candidate_position.position_id},
    )

    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1
    assert documents[0]["id"] == doc1_id
    assert documents[0]["candidate_position_id"] == candidate_position.id


@patch("app.services.storage_service.generate_upload_url")
async def test_list_candidate_documents_with_type_filter(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    candidate_position: CandidatePosition,
    interviewer: User,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    presign_cv = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign_cv.status_code == 201
    cv_id = presign_cv.json()["document_id"]
    await client.post(f"/api/documents/{cv_id}/complete")

    presign_transcript = await client.post(
        "/api/documents/presign",
        json={
            "type": "transcript",
            "candidate_position_id": candidate_position.id,
            "file_name": "interview.txt",
            "content_type": "text/plain",
            "file_size": 512000,
            "interview_stage": "technical",
            "interviewer_id": interviewer.id,
            "interview_date": "2025-01-15",
        },
    )
    assert presign_transcript.status_code == 201
    transcript_id = presign_transcript.json()["document_id"]
    await client.post(f"/api/documents/{transcript_id}/complete")

    response = await client.get(
        f"/api/candidates/{candidate_position.candidate_id}/documents",
        params={"type": "cv"},
    )

    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1
    assert documents[0]["id"] == cv_id
    assert documents[0]["type"] == "cv"


@patch("app.services.storage_service.generate_upload_url")
async def test_list_candidate_documents_with_candidate_position_id_filter(
    mock_generate_upload_url: AsyncMock,
    client: AsyncClient,
    session: AsyncSession,
    candidate_position: CandidatePosition,
):
    mock_generate_upload_url.return_value = "https://s3.amazonaws.com/fake-upload-url"

    first_position = await session.get(Position, candidate_position.position_id)
    assert first_position is not None

    second_position = Position(
        title="Frontend Engineer",
        team_id=first_position.team_id,
        hiring_manager_id=first_position.hiring_manager_id,
        status="open",
    )
    session.add(second_position)
    await session.commit()
    await session.refresh(second_position)

    second_cp = CandidatePosition(
        candidate_id=candidate_position.candidate_id,
        position_id=second_position.id,
        stage="new",
    )
    session.add(second_cp)
    await session.commit()
    await session.refresh(second_cp)

    presign1 = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": candidate_position.id,
            "file_name": "resume1.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign1.status_code == 201
    doc1_id = presign1.json()["document_id"]
    await client.post(f"/api/documents/{doc1_id}/complete")

    presign2 = await client.post(
        "/api/documents/presign",
        json={
            "type": "cv",
            "candidate_position_id": second_cp.id,
            "file_name": "resume2.pdf",
            "content_type": "application/pdf",
            "file_size": 1024000,
        },
    )
    assert presign2.status_code == 201
    doc2_id = presign2.json()["document_id"]
    await client.post(f"/api/documents/{doc2_id}/complete")

    response = await client.get(
        f"/api/candidates/{candidate_position.candidate_id}/documents",
        params={"candidate_position_id": candidate_position.id},
    )

    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1
    assert documents[0]["id"] == doc1_id
    assert documents[0]["candidate_position_id"] == candidate_position.id
