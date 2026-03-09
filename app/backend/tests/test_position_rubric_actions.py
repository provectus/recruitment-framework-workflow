from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from tests.helpers import VALID_RUBRIC_STRUCTURE, create_test_position

UPDATED_STRUCTURE = {
    "categories": [
        {
            "name": "Problem Solving",
            "description": None,
            "weight": 100,
            "sort_order": 0,
            "criteria": [
                {
                    "name": "Algorithms",
                    "description": None,
                    "weight": 100,
                    "sort_order": 0,
                }
            ],
        }
    ]
}


async def create_rubric_for_position(client: AsyncClient, position_id: int) -> dict:
    response = await client.post(
        f"/api/positions/{position_id}/rubric",
        json={"source": "custom", "structure": VALID_RUBRIC_STRUCTURE},
    )
    assert response.status_code == 201
    return response.json()


async def test_update_creates_new_version(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    response = await authenticated_client.put(
        f"/api/positions/{position.id}/rubric",
        json={"structure": UPDATED_STRUCTURE},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 2
    assert data["structure"]["categories"][0]["name"] == "Problem Solving"


async def test_update_invalid_weights_returns_422(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    bad_structure = {
        "categories": [
            {
                "name": "Technical",
                "description": None,
                "weight": 50,
                "sort_order": 0,
                "criteria": [
                    {
                        "name": "Coding",
                        "description": None,
                        "weight": 100,
                        "sort_order": 0,
                    }
                ],
            },
            {
                "name": "Other",
                "description": None,
                "weight": 30,
                "sort_order": 1,
                "criteria": [
                    {
                        "name": "Misc",
                        "description": None,
                        "weight": 100,
                        "sort_order": 0,
                    }
                ],
            },
        ]
    }

    response = await authenticated_client.put(
        f"/api/positions/{position.id}/rubric",
        json={"structure": bad_structure},
    )
    assert response.status_code == 422


async def test_update_404_if_no_rubric(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)

    response = await authenticated_client.put(
        f"/api/positions/{position.id}/rubric",
        json={"structure": VALID_RUBRIC_STRUCTURE},
    )
    assert response.status_code == 404


async def test_delete_rubric(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    delete_response = await authenticated_client.delete(
        f"/api/positions/{position.id}/rubric"
    )
    assert delete_response.status_code == 204

    get_response = await authenticated_client.get(
        f"/api/positions/{position.id}/rubric"
    )
    assert get_response.status_code == 404


async def test_delete_404_if_no_rubric(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)

    response = await authenticated_client.delete(f"/api/positions/{position.id}/rubric")
    assert response.status_code == 404


async def test_list_versions_returns_all_sorted_desc(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    await authenticated_client.put(
        f"/api/positions/{position.id}/rubric",
        json={"structure": UPDATED_STRUCTURE},
    )

    response = await authenticated_client.get(
        f"/api/positions/{position.id}/rubric/versions"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["version_number"] == 2
    assert data["items"][1]["version_number"] == 1


async def test_get_specific_version(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    await authenticated_client.put(
        f"/api/positions/{position.id}/rubric",
        json={"structure": UPDATED_STRUCTURE},
    )

    response = await authenticated_client.get(
        f"/api/positions/{position.id}/rubric/versions/1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 1
    assert data["structure"]["categories"][0]["name"] == "Technical"


async def test_revert_creates_new_version_with_old_structure(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    await authenticated_client.put(
        f"/api/positions/{position.id}/rubric",
        json={"structure": UPDATED_STRUCTURE},
    )

    response = await authenticated_client.post(
        f"/api/positions/{position.id}/rubric/revert/1"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 3
    assert data["structure"]["categories"][0]["name"] == "Technical"


async def test_save_as_template(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)
    await create_rubric_for_position(authenticated_client, position.id)

    response = await authenticated_client.post(
        f"/api/positions/{position.id}/rubric/save-as-template",
        json={"name": "My Template", "description": "A saved template"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Template"
    assert data["description"] == "A saved template"
    assert data["structure"]["categories"][0]["name"] == "Technical"
    assert data["is_archived"] is False


async def test_save_as_template_404_if_no_rubric(
    authenticated_client: AsyncClient,
    session: AsyncSession,
):
    position = await create_test_position(session)

    response = await authenticated_client.post(
        f"/api/positions/{position.id}/rubric/save-as-template",
        json={"name": "My Template"},
    )
    assert response.status_code == 404
