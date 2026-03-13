# Local Evaluation Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable end-to-end local evaluation pipeline testing with mock Bedrock and a local orchestrator docker-compose service.

**Architecture:** Add `MOCK_BEDROCK` flag to Lambda shared layer that returns canned JSON instead of calling AWS. Add a local orchestrator service that polls Postgres for pending evaluations and dispatches to Lambda handlers directly. Both run as part of `docker compose up`.

**Tech Stack:** Python 3.12, psycopg2, SQLAlchemy, boto3, Docker

---

### Task 1: Add new config vars to `shared/config.py`

**Files:**
- Modify: `app/lambdas/shared/config.py`

**Step 1: Add env var reads**

Add these lines to `app/lambdas/shared/config.py`:

```python
S3_ENDPOINT_URL: str = os.environ.get("S3_ENDPOINT_URL", "")
MOCK_BEDROCK: bool = os.environ.get("MOCK_BEDROCK", "").lower() in ("true", "1", "yes")
MOCK_BEDROCK_DELAY_SECONDS: float = float(os.environ.get("MOCK_BEDROCK_DELAY_SECONDS", "3"))
MOCK_EVALUATION_FAILURES: list[str] = [
    s.strip() for s in os.environ.get("MOCK_EVALUATION_FAILURES", "").split(",") if s.strip()
]
```

**Step 2: Commit**

```bash
git add app/lambdas/shared/config.py
git commit -m "feat(lambdas): add mock bedrock and S3 endpoint config vars"
```

---

### Task 2: Add S3 endpoint URL support for MinIO

**Files:**
- Modify: `app/lambdas/shared/s3.py`

**Step 1: Update `get_client()` to use `S3_ENDPOINT_URL`**

Replace the `get_client()` function in `app/lambdas/shared/s3.py`:

```python
def get_client():
    global _client
    if _client is None:
        kwargs = {"region_name": config.AWS_REGION}
        if config.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = config.S3_ENDPOINT_URL
        _client = boto3.client("s3", **kwargs)
    return _client
```

**Step 2: Commit**

```bash
git add app/lambdas/shared/s3.py
git commit -m "feat(lambdas): add S3 endpoint URL support for MinIO"
```

---

### Task 3: Create mock Bedrock module

**Files:**
- Create: `app/lambdas/shared/mock_bedrock.py`

**Step 1: Create the mock module**

Create `app/lambdas/shared/mock_bedrock.py` with:
- A `MOCK_RESPONSES` dict mapping each step type to a canned JSON string
- A `mock_invoke_claude()` function that:
  1. Sleeps for `config.MOCK_BEDROCK_DELAY_SECONDS`
  2. Checks if `step_type` is in `config.MOCK_EVALUATION_FAILURES` — if so, raises `RuntimeError(f"Mock Bedrock failure for {step_type}")`
  3. Returns the canned response string for that step type
  4. Falls back to a generic response if step type is unknown

```python
import json
import time

from shared import config

MOCK_RESPONSES: dict[str, dict] = {
    "cv_analysis": {
        "skills_match": [
            {"skill": "Python", "present": True, "notes": "5 years of professional experience with Python, including FastAPI and Django."},
            {"skill": "AWS", "present": True, "notes": "Experience with EC2, S3, and Lambda mentioned in two previous roles."},
            {"skill": "PostgreSQL", "present": True, "notes": "Used as primary database in last three positions."},
            {"skill": "Docker", "present": True, "notes": "Docker and Docker Compose used for local development and CI/CD."},
            {"skill": "TypeScript", "present": False, "notes": "No mention of TypeScript or frontend development experience."},
        ],
        "experience_relevance": "Candidate has 6 years of backend engineering experience directly relevant to the role. Previous work at two mid-size SaaS companies involved building and maintaining microservices at scale.",
        "education": "B.S. in Computer Science from a well-regarded university. Coursework in distributed systems and databases is relevant to the position requirements.",
        "signals_and_red_flags": "Positive signals include consistent career progression and open-source contributions. One concern is a 4-month employment gap between the last two roles, though this may have a reasonable explanation.",
        "overall_fit": "Strong technical match for the backend engineering role. The candidate's experience with Python, AWS, and PostgreSQL aligns well with the tech stack. Recommend proceeding to screening.",
    },
    "screening_eval": {
        "key_topics": [
            "Career motivation and reasons for exploring new opportunities",
            "Experience with distributed systems and microservices architecture",
            "Team collaboration and communication style",
            "Understanding of the company's product and market",
        ],
        "strengths": [
            "Articulate and well-prepared — clearly researched the company before the call",
            "Demonstrated genuine enthusiasm for the technical challenges of the role",
            "Provided concrete examples when discussing past projects and achievements",
        ],
        "concerns": [
            "Mentioned salary expectations that may be above the budgeted range for this level",
            "Limited experience with the specific industry vertical, though transferable skills are strong",
        ],
        "communication_quality": "The candidate communicated clearly and professionally throughout the screening. Responses were well-structured, concise, and demonstrated strong active listening skills.",
        "motivation_culture_fit": "Genuine interest in the company's mission and growth trajectory. Values alignment with the team's collaborative culture was evident. Expressed interest in mentoring junior engineers, which aligns with team needs.",
    },
    "technical_eval": {
        "criteria_scores": [
            {
                "criterion_name": "Algorithm Design",
                "category_name": "Problem Solving",
                "score": 4,
                "max_score": 5,
                "weight": 0.25,
                "evidence": "Candidate identified the optimal approach using a sliding window technique and implemented it correctly within 15 minutes.",
                "reasoning": "Strong analytical thinking. Considered edge cases proactively and optimized from O(n^2) to O(n) without prompting.",
            },
            {
                "criterion_name": "System Design",
                "category_name": "Architecture",
                "score": 3,
                "max_score": 5,
                "weight": 0.25,
                "evidence": "Proposed a reasonable microservices architecture but did not address data consistency between services.",
                "reasoning": "Adequate understanding of distributed systems. Could benefit from deeper knowledge of eventual consistency patterns.",
            },
            {
                "criterion_name": "Code Quality",
                "category_name": "Engineering Practices",
                "score": 4,
                "max_score": 5,
                "weight": 0.25,
                "evidence": "Code was clean, well-named, and included error handling. Added unit test outlines when asked.",
                "reasoning": "Exceeds expectations for code organization and readability. Testing mindset is present.",
            },
            {
                "criterion_name": "Communication",
                "category_name": "Soft Skills",
                "score": 4,
                "max_score": 5,
                "weight": 0.25,
                "evidence": "Explained thought process clearly while coding. Asked clarifying questions before starting each problem.",
                "reasoning": "Strong technical communication. Would integrate well into a collaborative engineering team.",
            },
        ],
        "weighted_total": 3.75,
        "strengths_summary": [
            "Strong algorithmic problem-solving with proactive optimization",
            "Clean, readable code with good engineering practices",
            "Excellent technical communication throughout the interview",
        ],
        "improvement_areas": [
            "Deeper knowledge of distributed systems consistency patterns",
            "Could explore more advanced system design topics like CQRS and event sourcing",
        ],
    },
    "recommendation": {
        "recommendation": "hire",
        "confidence": "high",
        "reasoning": "The candidate demonstrated strong technical skills across all evaluation stages. CV analysis confirmed relevant experience with the required tech stack. Screening revealed good cultural alignment and genuine motivation. Technical interview scores averaged 3.75/5 with particular strength in problem-solving and code quality. The only area for growth is system design depth, which is expected at this level and can be developed on the job.",
        "missing_inputs": [],
    },
    "feedback_gen": {
        "feedback_text": "Thank you for taking the time to interview with us for the Backend Engineer position. We genuinely appreciated your thoughtful preparation and the depth of experience you shared throughout the process.\n\nYour strong problem-solving skills were evident during the technical interview, particularly your ability to optimize solutions and write clean, well-structured code. Your communication style is clear and collaborative, which stood out positively.\n\nWhile your technical fundamentals are solid, we felt that deeper experience with distributed systems architecture would better align with the current needs of this particular role. We would encourage you to explore topics like eventual consistency patterns and event-driven architectures, as these would complement your already strong skill set.\n\nWe were impressed by your profile and would welcome the opportunity to stay connected for future roles that may be a better match. Please don't hesitate to reach out or apply again as our team continues to grow.",
        "rejection_stage": "technical",
    },
}


def mock_invoke_claude(step_type: str) -> str:
    time.sleep(config.MOCK_BEDROCK_DELAY_SECONDS)

    if step_type in config.MOCK_EVALUATION_FAILURES:
        raise RuntimeError(f"Mock Bedrock failure for {step_type}")

    response = MOCK_RESPONSES.get(step_type)
    if response is None:
        raise ValueError(f"No mock response defined for step type: {step_type}")

    return json.dumps(response)
```

**Step 2: Commit**

```bash
git add app/lambdas/shared/mock_bedrock.py
git commit -m "feat(lambdas): add mock Bedrock module with canned responses and failure simulation"
```

---

### Task 4: Wire mock into `shared/bedrock.py`

**Files:**
- Modify: `app/lambdas/shared/bedrock.py`

**Step 1: Add mock check to `invoke_claude()`**

Add a `step_type` parameter and mock check at the top of `invoke_claude()`:

```python
def invoke_claude(
    prompt: str,
    max_tokens: int = 4096,
    system_prompt: str = "",
    step_type: str = "",
) -> str:
    if config.MOCK_BEDROCK and step_type:
        from shared.mock_bedrock import mock_invoke_claude
        return mock_invoke_claude(step_type)

    # ... rest of existing function unchanged
```

**Step 2: Update all 5 handler files to pass `step_type`**

In each handler (`cv_analysis`, `screening_eval`, `technical_eval`, `recommendation`, `feedback_gen`), update the `bedrock_module.invoke_claude()` call to include `step_type`:

For example in `app/lambdas/cv_analysis/handler.py`:
```python
raw_response = bedrock_module.invoke_claude(
    prompt=user_prompt,
    system_prompt=system_prompt,
    step_type="cv_analysis",
)
```

Repeat for all 5 handlers with their respective step type strings.

**Step 3: Commit**

```bash
git add app/lambdas/shared/bedrock.py app/lambdas/*/handler.py
git commit -m "feat(lambdas): wire mock Bedrock into invoke_claude with step_type routing"
```

---

### Task 5: Create local orchestrator script

**Files:**
- Create: `app/lambdas/local_orchestrator.py`

**Step 1: Create the orchestrator**

```python
import importlib
import logging
import sys
import time

from shared import config
from shared.db import get_session
from shared.models import Evaluation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("local-orchestrator")

POLL_INTERVAL_SECONDS = 2

HANDLER_MODULES = {
    "cv_analysis": "cv_analysis.handler",
    "screening_eval": "screening_eval.handler",
    "technical_eval": "technical_eval.handler",
    "recommendation": "recommendation.handler",
    "feedback_gen": "feedback_gen.handler",
}


def build_event(evaluation: Evaluation) -> dict:
    return {
        "detail": {
            "evaluation_id": evaluation.id,
            "candidate_position_id": evaluation.candidate_position_id,
            "step_type": evaluation.step_type,
        }
    }


def dispatch(evaluation: Evaluation) -> None:
    step_type = evaluation.step_type
    module_path = HANDLER_MODULES.get(step_type)
    if module_path is None:
        logger.error(f"Unknown step_type: {step_type}")
        return

    module = importlib.import_module(module_path)
    event = build_event(evaluation)

    logger.info(
        f"Dispatching evaluation {evaluation.id} "
        f"(step={step_type}, version={evaluation.version})"
    )

    try:
        module.handler(event, None)
        logger.info(f"Evaluation {evaluation.id} completed")
    except Exception:
        logger.exception(f"Evaluation {evaluation.id} failed")


def poll_and_dispatch() -> None:
    with get_session() as session:
        pending = (
            session.query(Evaluation)
            .filter(Evaluation.status == "pending")
            .order_by(Evaluation.created_at.asc())
            .all()
        )

    for evaluation in pending:
        dispatch(evaluation)


def main() -> None:
    logger.info("Local orchestrator started")
    logger.info(f"  MOCK_BEDROCK={config.MOCK_BEDROCK}")
    logger.info(f"  MOCK_BEDROCK_DELAY_SECONDS={config.MOCK_BEDROCK_DELAY_SECONDS}")
    logger.info(f"  MOCK_EVALUATION_FAILURES={config.MOCK_EVALUATION_FAILURES}")
    logger.info(f"  DB: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")

    while True:
        try:
            poll_and_dispatch()
        except Exception:
            logger.exception("Error during poll cycle")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add app/lambdas/local_orchestrator.py
git commit -m "feat(lambdas): add local orchestrator for evaluation pipeline"
```

---

### Task 6: Create Dockerfile.local

**Files:**
- Create: `app/lambdas/Dockerfile.local`

**Step 1: Create the Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "local_orchestrator.py"]
```

**Step 2: Commit**

```bash
git add app/lambdas/Dockerfile.local
git commit -m "feat(lambdas): add Dockerfile.local for orchestrator service"
```

---

### Task 7: Add evaluator service to docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`

**Step 1: Add the `evaluator` service**

Add after the `backend` service block:

```yaml
  evaluator:
    build:
      context: ./app/lambdas
      dockerfile: Dockerfile.local
    depends_on:
      db:
        condition: service_healthy
      minio:
        condition: service_healthy
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: lauter
      DB_USERNAME: postgres
      DB_PASSWORD: postgres
      S3_ENDPOINT_URL: http://minio:9000
      S3_BUCKET_NAME: lauter-files
      MOCK_BEDROCK: "true"
      MOCK_BEDROCK_DELAY_SECONDS: "3"
      MOCK_EVALUATION_FAILURES: ""
      AWS_ACCESS_KEY_ID: minioadmin
      AWS_SECRET_ACCESS_KEY: minioadmin
```

**Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat(docker): add evaluator service for local pipeline testing"
```

---

### Task 8: End-to-end smoke test

**Step 1: Build and start all services**

```bash
docker compose up -d --build
```

**Step 2: Verify evaluator starts and polls**

```bash
docker compose logs -f evaluator
```

Expected: Logs showing orchestrator started with config values, polling every 2s.

**Step 3: Trigger an evaluation via the UI or API**

Upload a CV through the frontend or call the backend API directly. Watch the evaluator logs — it should pick up the pending evaluation, dispatch to the handler, and log completion (or failure if step is in `MOCK_EVALUATION_FAILURES`).

**Step 4: Test failure simulation**

```bash
docker compose up -d -e MOCK_EVALUATION_FAILURES=cv_analysis
```

Or update the env var in `docker-compose.yml`, restart evaluator, and trigger another evaluation. Verify status becomes `failed` with the mock error message.

**Step 5: Verify SSE streaming**

Open the candidate detail page in the frontend. Trigger an evaluation. Confirm the UI updates in real-time via SSE as status changes from `pending` → `running` → `completed`.
