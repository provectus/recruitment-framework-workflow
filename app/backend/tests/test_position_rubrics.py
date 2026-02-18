from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from tests.helpers import (
    VALID_RUBRIC_STRUCTURE,
    create_test_position,
    create_test_template,
)


async def test_create_from_template(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    template = await create_test_template(session)

    response = await authenticated_client.post(
        f"/api/positions/{position.id}/rubric",
        json={
            "source": "template",
            "template_id": template.id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["position_id"] == position.id
    assert data["source_template_name"] == "Test Template"
    assert data["version_number"] == 1
    assert data["structure"]["categories"][0]["name"] == "Technical"


async def test_create_custom(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)

    response = await authenticated_client.post(
        f"/api/positions/{position.id}/rubric",
        json={
            "source": "custom",
            "structure": VALID_RUBRIC_STRUCTURE,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["position_id"] == position.id
    assert data["source_template_name"] is None
    assert data["version_number"] == 1


async def test_create_conflict(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)

    await authenticated_client.post(
        f"/api/positions/{position.id}/rubric",
        json={"source": "custom", "structure": VALID_RUBRIC_STRUCTURE},
    )

    response = await authenticated_client.post(
        f"/api/positions/{position.id}/rubric",
        json={"source": "custom", "structure": VALID_RUBRIC_STRUCTURE},
    )
    assert response.status_code == 409


async def test_create_position_not_found(
    authenticated_client: AsyncClient,
):
    response = await authenticated_client.post(
        "/api/positions/99999/rubric",
        json={"source": "custom", "structure": VALID_RUBRIC_STRUCTURE},
    )
    assert response.status_code == 404


async def test_unauthenticated(
    client: AsyncClient,
):
    response = await client.post(
        "/api/positions/1/rubric",
        json={"source": "custom", "structure": VALID_RUBRIC_STRUCTURE},
    )
    assert response.status_code == 401


async def test_get_rubric(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)

    await authenticated_client.post(
        f"/api/positions/{position.id}/rubric",
        json={"source": "custom", "structure": VALID_RUBRIC_STRUCTURE},
    )

    response = await authenticated_client.get(f"/api/positions/{position.id}/rubric")
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 1
    assert data["created_by"] == "Test User"


async def test_get_rubric_not_found(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    response = await authenticated_client.get(f"/api/positions/{position.id}/rubric")
    assert response.status_code == 404
