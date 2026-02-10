# Prototype Plan: Minimal AI Evaluation

**Scope:** Claude prompts + Python CLI. No infra.

## Structure
```
src/
├── core/           # config, claude client
├── evaluation/     # cv, screening, technical, rubric, feedback
├── prompts/        # .md templates
└── cli.py
tests/fixtures/     # real transcripts
```

## Tasks
1. Init Python project (uv)
2. Claude API wrapper
3. CV analyzer prompt + module
4. Screening summary prompt + module
5. Technical evaluator + rubric engine
6. Feedback generator
7. CLI interface

## Default Rubric
| Criterion | Weight |
|-----------|--------|
| Technical Skills | 35% |
| Domain Knowledge | 20% |
| Communication | 15% |
| Culture Fit | 15% |
| Motivation | 15% |

Scale: 1-5. Hire ≥3.0. Strong Hire ≥4.0.

## CLI Usage
```bash
python -m src.cli cv resume.pdf
python -m src.cli screening transcript.txt
python -m src.cli technical interview.txt
python -m src.cli evaluate candidate_folder/
```

## Next: Option B
n8n + Slack bot locally after AI logic validated.

---

## Unresolved Questions
None - ready to implement.
