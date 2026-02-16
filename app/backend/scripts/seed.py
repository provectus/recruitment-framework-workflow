"""Seed local Postgres with realistic dev data.

Usage:
    cd app/backend && uv run python -m scripts.seed
"""

import asyncio

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import async_session_factory
from app.models import (
    Candidate,
    CandidatePosition,
    Position,
    Team,
    User,
)
from app.models.enums import PipelineStage, PositionStatus

TEAMS = [
    {"name": "Engineering"},
    {"name": "Data Science"},
    {"name": "Design"},
    {"name": "Product"},
]

USERS = [
    {"email": "alex.morgan@provectus.com", "google_id": "seed_gid_001", "full_name": "Alex Morgan"},
    {"email": "jamie.chen@provectus.com", "google_id": "seed_gid_002", "full_name": "Jamie Chen"},
    {"email": "sam.patel@provectus.com", "google_id": "seed_gid_003", "full_name": "Sam Patel"},
    {"email": "taylor.kim@provectus.com", "google_id": "seed_gid_004", "full_name": "Taylor Kim"},
    {"email": "jordan.lee@provectus.com", "google_id": "seed_gid_005", "full_name": "Jordan Lee"},
    {"email": "casey.ward@provectus.com", "google_id": "seed_gid_006", "full_name": "Casey Ward"},
]

POSITIONS = [
    {"title": "Senior Backend Engineer", "status": PositionStatus.open, "team_idx": 0, "manager_idx": 0},
    {"title": "ML Engineer", "status": PositionStatus.open, "team_idx": 1, "manager_idx": 1},
    {"title": "Senior Frontend Engineer", "status": PositionStatus.open, "team_idx": 0, "manager_idx": 0},
    {"title": "Data Analyst", "status": PositionStatus.on_hold, "team_idx": 1, "manager_idx": 1},
    {"title": "UX Designer", "status": PositionStatus.open, "team_idx": 2, "manager_idx": 3},
    {"title": "Product Manager", "status": PositionStatus.open, "team_idx": 3, "manager_idx": 4},
    {"title": "DevOps Engineer", "status": PositionStatus.closed, "team_idx": 0, "manager_idx": 2},
    {"title": "Junior Python Developer", "status": PositionStatus.open, "team_idx": 0, "manager_idx": 2},
    {"title": "Research Scientist", "status": PositionStatus.on_hold, "team_idx": 1, "manager_idx": 1},
    {"title": "UI Designer", "status": PositionStatus.open, "team_idx": 2, "manager_idx": 3},
]

CANDIDATES = [
    {"full_name": "Olivia Martinez", "email": "olivia.martinez@gmail.com"},
    {"full_name": "Liam Johnson", "email": "liam.johnson@outlook.com"},
    {"full_name": "Emma Williams", "email": "emma.w@yahoo.com"},
    {"full_name": "Noah Brown", "email": "noah.brown@protonmail.com"},
    {"full_name": "Ava Davis", "email": "ava.davis@gmail.com"},
    {"full_name": "Ethan Wilson", "email": "ethan.wilson@hotmail.com"},
    {"full_name": "Sophia Garcia", "email": "sophia.g@gmail.com"},
    {"full_name": "Mason Anderson", "email": "mason.anderson@outlook.com"},
    {"full_name": "Isabella Thomas", "email": "isabella.t@yahoo.com"},
    {"full_name": "Lucas Taylor", "email": "lucas.taylor@gmail.com"},
    {"full_name": "Mia Moore", "email": "mia.moore@protonmail.com"},
    {"full_name": "Alexander Jackson", "email": "alex.jackson@gmail.com"},
    {"full_name": "Charlotte White", "email": "charlotte.w@outlook.com"},
    {"full_name": "Benjamin Harris", "email": "ben.harris@gmail.com"},
    {"full_name": "Amelia Clark", "email": "amelia.clark@yahoo.com"},
    {"full_name": "James Lewis", "email": "james.lewis@gmail.com"},
    {"full_name": "Harper Robinson", "email": "harper.r@protonmail.com"},
    {"full_name": "Daniel Walker", "email": "daniel.walker@outlook.com"},
    {"full_name": "Evelyn Young", "email": "evelyn.young@gmail.com"},
    {"full_name": "Henry Allen", "email": "henry.allen@hotmail.com"},
    {"full_name": "Scarlett King", "email": "scarlett.king@gmail.com"},
    {"full_name": "Sebastian Wright", "email": "seb.wright@outlook.com"},
    {"full_name": "Grace Scott", "email": "grace.scott@yahoo.com"},
    {"full_name": "Jack Green", "email": "jack.green@gmail.com"},
    {"full_name": "Chloe Adams", "email": "chloe.adams@protonmail.com"},
]

CANDIDATE_POSITIONS = [
    (0, 0, PipelineStage.technical),
    (0, 2, PipelineStage.screening),
    (1, 0, PipelineStage.offer),
    (1, 7, PipelineStage.new),
    (2, 1, PipelineStage.hired),
    (3, 0, PipelineStage.rejected),
    (3, 7, PipelineStage.screening),
    (4, 4, PipelineStage.technical),
    (5, 0, PipelineStage.new),
    (5, 2, PipelineStage.new),
    (6, 1, PipelineStage.screening),
    (6, 3, PipelineStage.new),
    (7, 7, PipelineStage.technical),
    (8, 5, PipelineStage.offer),
    (9, 0, PipelineStage.screening),
    (9, 2, PipelineStage.rejected),
    (10, 1, PipelineStage.technical),
    (10, 8, PipelineStage.new),
    (11, 6, PipelineStage.hired),
    (12, 4, PipelineStage.new),
    (12, 9, PipelineStage.screening),
    (13, 0, PipelineStage.technical),
    (14, 5, PipelineStage.screening),
    (15, 2, PipelineStage.offer),
    (15, 7, PipelineStage.new),
    (16, 1, PipelineStage.rejected),
    (17, 6, PipelineStage.screening),
    (18, 3, PipelineStage.new),
    (18, 8, PipelineStage.technical),
    (19, 9, PipelineStage.new),
    (20, 0, PipelineStage.new),
    (20, 5, PipelineStage.technical),
    (21, 2, PipelineStage.screening),
    (22, 4, PipelineStage.offer),
    (23, 7, PipelineStage.rejected),
    (24, 1, PipelineStage.new),
    (24, 8, PipelineStage.screening),
]

TRUNCATE_ORDER = [
    "documents",
    "candidate_positions",
    "candidates",
    "positions",
    "users",
    "teams",
]


async def seed() -> None:
    async with async_session_factory() as session:
        session: AsyncSession

        for table in TRUNCATE_ORDER:
            await session.exec(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        await session.commit()

        teams = [Team(**t) for t in TEAMS]
        session.add_all(teams)
        await session.flush()

        users = [User(**u) for u in USERS]
        session.add_all(users)
        await session.flush()

        positions = []
        for p in POSITIONS:
            positions.append(
                Position(
                    title=p["title"],
                    status=p["status"],
                    team_id=teams[p["team_idx"]].id,
                    hiring_manager_id=users[p["manager_idx"]].id,
                )
            )
        session.add_all(positions)
        await session.flush()

        candidates = [Candidate(**c) for c in CANDIDATES]
        session.add_all(candidates)
        await session.flush()

        cp_records = []
        for cand_idx, pos_idx, stage in CANDIDATE_POSITIONS:
            cp_records.append(
                CandidatePosition(
                    candidate_id=candidates[cand_idx].id,
                    position_id=positions[pos_idx].id,
                    stage=stage,
                )
            )
        session.add_all(cp_records)
        await session.commit()

    print(
        f"Seeded: {len(teams)} teams, {len(users)} users, "
        f"{len(positions)} positions, {len(candidates)} candidates, "
        f"{len(cp_records)} candidate-positions"
    )


if __name__ == "__main__":
    asyncio.run(seed())
