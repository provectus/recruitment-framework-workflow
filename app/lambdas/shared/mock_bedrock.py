import json
import time

from shared import config

MOCK_RESPONSES: dict[str, dict] = {
    "cv_analysis": {
        "skills_match": [
            {
                "skill": "Python",
                "present": True,
                "notes": "5 years of professional experience with Python, including FastAPI and Django.",
            },
            {
                "skill": "AWS",
                "present": True,
                "notes": "Experience with EC2, S3, and Lambda mentioned in two previous roles.",
            },
            {
                "skill": "PostgreSQL",
                "present": True,
                "notes": "Used as primary database in last three positions.",
            },
            {
                "skill": "Docker",
                "present": True,
                "notes": "Docker and Docker Compose used for local development and CI/CD.",
            },
            {
                "skill": "TypeScript",
                "present": False,
                "notes": "No mention of TypeScript or frontend development experience.",
            },
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
        "requirements_alignment": [
            {
                "requirement": "Python",
                "status": "met",
                "evidence": "Discussed 5 years of professional Python experience across multiple roles.",
            },
            {
                "requirement": "AWS",
                "status": "met",
                "evidence": "Mentioned working with EC2, S3, and Lambda in previous positions.",
            },
            {
                "requirement": "PostgreSQL",
                "status": "met",
                "evidence": "Confirmed as primary database in recent work.",
            },
            {
                "requirement": "Docker",
                "status": "partially_met",
                "evidence": "Mentioned using Docker for local development but depth unclear.",
            },
            {
                "requirement": "TypeScript",
                "status": "not_assessed",
                "evidence": "Topic was not covered during the screening.",
            },
            {
                "requirement": "CI/CD",
                "status": "not_assessed",
                "evidence": "Topic was not covered during the screening.",
            },
        ],
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
        "cv_alignment": "Interview performance strongly confirms CV claims. The candidate's stated 5 years of Python experience was evident in their fluent use of language features and library knowledge during the coding challenge. Their AWS experience aligned with the system design discussion. No contradictions found between CV claims and demonstrated ability.",
        "screening_consistency": "Technical interview is consistent with screening signals. The communication strengths noted in screening were confirmed — the candidate explained complex concepts clearly throughout. The concern about limited industry vertical experience was partially addressed, as the candidate demonstrated strong transferable problem-solving skills.",
        "skill_gaps": [
            "Distributed systems consistency patterns (eventual consistency, CQRS) — gap between role requirements and demonstrated depth",
            "Event-driven architecture — mentioned briefly but lacked hands-on examples",
        ],
        "follow_up_questions": [
            "Can you walk through a scenario where you had to handle data consistency across multiple microservices?",
            "Describe your experience with event-driven architectures — what messaging systems have you used and what challenges did you face?",
            "How would you approach debugging a distributed system where data is inconsistent across services?",
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


def mock_invoke_claude_structured(step_type: str) -> dict:
    time.sleep(config.MOCK_BEDROCK_DELAY_SECONDS)

    if step_type in config.MOCK_EVALUATION_FAILURES:
        raise RuntimeError(f"Mock Bedrock failure for {step_type}")

    response = MOCK_RESPONSES.get(step_type)
    if response is None:
        raise ValueError(f"No mock response defined for step type: {step_type}")

    return response
