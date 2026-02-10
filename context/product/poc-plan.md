# POC Plan: Full Recruitment Workflow

**Scope:** n8n + AWS + Lever + Slack. Production-ready POC.

## Dependency Graph

```
[AWS Setup] ──────────────────────────────────────┐
     │                                             │
     ├─► [RDS PostgreSQL]                          │
     │        │                                    │
     ├─► [S3 Watched Folder] ◄─────┐               │
     │        │                    │               │
     └─► [ECS + n8n] ◄─────────────┼───────────────┘
              │                    │
              ├─► [Bedrock Claude] │
              │        │           │
              ├─► [Lever API] ─────┤
              │        │           │
              └─► [Slack Bot] ─────┘
                       │
                       ▼
              [Evaluation Pipeline]
                       │
                       ▼
              [Lever Write-back]
```

## Phases & Dependencies

### Phase 0: Prerequisites
- [ ] AWS account + IAM roles
- [ ] Bedrock Claude access enabled
- [ ] Lever API credentials (sandbox)
- [ ] Slack workspace admin access

### Phase 1: Infrastructure
**Depends on:** Phase 0

| Task | Depends On |
|------|------------|
| VPC + subnets | - |
| RDS PostgreSQL | VPC |
| S3 bucket | - |
| ECS cluster | VPC |
| n8n on ECS | ECS, RDS |
| CloudWatch logs | ECS |

### Phase 2: Integrations
**Depends on:** Phase 1 (n8n running)

| Task | Depends On |
|------|------------|
| Slack bot app | Slack admin |
| Slack → n8n webhook | n8n, Slack bot |
| S3 trigger → n8n | n8n, S3 |
| Lever API read | Lever creds |
| Bedrock client | Bedrock access |

### Phase 3: Evaluation Pipeline
**Depends on:** Phase 2 (integrations), Prototype (AI logic)

| Task | Depends On |
|------|------------|
| CV analysis workflow | Bedrock, Lever read |
| Screening processor | Bedrock, input mechanism |
| Technical evaluator | Bedrock, rubric |
| Recommendation engine | all evaluators |

### Phase 4: Output
**Depends on:** Phase 3

| Task | Depends On |
|------|------------|
| Feedback generator | evaluator output |
| Lever write-back | Lever API, evaluation |
| Audit logging | RDS, all workflows |

## Critical Path

```
AWS Setup → n8n on ECS → Bedrock integration → Evaluation workflows → Lever write-back
```

## Blockers / External Dependencies

| Dependency | Owner | Status |
|------------|-------|--------|
| AWS account (us-east-1) | Ops | ? |
| Bedrock Claude access | Ops | ? |
| Lever sandbox API key | HR/IT | **ACTION: Request** |
| Slack app approval | IT | ? |
| Sample transcripts | HR | ✓ |

## n8n Workflows to Build

1. `transcript-intake` - S3/Slack → parse → store
2. `cv-analysis` - Lever trigger → Claude → store
3. `screening-eval` - transcript → Claude → summary
4. `technical-eval` - transcript → Claude → rubric score
5. `recommendation` - aggregate → Claude → decision
6. `lever-sync` - evaluation → Lever notes

---

## Resolved

- **Bedrock region:** us-east-1
- **Lever sandbox:** Need to request from HR/IT (blocker)

## Unresolved Questions

1. **n8n licensing?** Self-hosted free tier sufficient?
2. **Metaview export format?** What's the transcript structure?
