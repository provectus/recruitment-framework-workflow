# POC Cost Estimate

**Region:** us-east-1
**Assumptions:** ~50 candidates/month, ~100 evaluations/month

---

## AWS Infrastructure

| Service | Spec | Monthly Cost |
|---------|------|--------------|
| **ECS Fargate** (n8n) | 0.5 vCPU, 1GB RAM, 24/7 | ~$15 |
| **RDS PostgreSQL** | db.t4g.micro, 20GB | ~$15 |
| **S3** | <1GB storage, minimal requests | ~$1 |
| **CloudWatch** | Basic logs/metrics | ~$5 |
| **NAT Gateway** | If needed for VPC | ~$35 |
| **Secrets Manager** | 3-4 secrets | ~$2 |

**AWS Subtotal:** ~$73/month (with NAT) or ~$38/month (without NAT)

---

## Amazon Bedrock (Claude)

| Model | Input | Output | Per Eval |
|-------|-------|--------|----------|
| Claude 3.5 Sonnet | $3/1M tokens | $15/1M tokens | ~$0.05-0.10 |
| Claude 3 Haiku | $0.25/1M tokens | $1.25/1M tokens | ~$0.005-0.01 |

**Per candidate (full pipeline):**
- CV analysis: ~2K input, ~1K output
- Screening summary: ~5K input, ~2K output
- Technical eval: ~8K input, ~3K output
- Recommendation: ~3K input, ~1K output
- Feedback: ~2K input, ~1K output

**Total per candidate:** ~20K input, ~8K output tokens

| Model | Per Candidate | 50 candidates/month |
|-------|---------------|---------------------|
| Sonnet | ~$0.18 | ~$9 |
| Haiku | ~$0.015 | ~$0.75 |

**Recommendation:** Use Haiku for summaries, Sonnet for evaluation/recommendation.

**Bedrock Subtotal:** ~$5-10/month

---

## External Services

| Service | Tier | Cost |
|---------|------|------|
| **Lever API** | Included in Lever subscription | $0 |
| **Slack API** | Free tier (bot) | $0 |
| **Metaview** | Manual export | $0 (existing sub) |
| **n8n** | Self-hosted (free) | $0 |

**External Subtotal:** $0

---

## Total Monthly Cost

| Scenario | Cost |
|----------|------|
| **Minimal** (no NAT, Haiku only) | ~$40/month |
| **Standard** (with NAT, mixed models) | ~$85/month |
| **High volume** (100+ candidates) | ~$100-150/month |

---

## One-Time Setup Costs

| Item | Effort | Notes |
|------|--------|-------|
| AWS infrastructure | Dev time | Terraform/manual setup |
| n8n workflows | Dev time | 6 workflows to build |
| Prompt engineering | Dev time | Testing & iteration |
| Lever API integration | Dev time | Read + write endpoints |

---

## Cost Optimization Options

1. **Use Haiku for all steps** → Save ~$8/month
2. **Spot instances for ECS** → Save ~30% on compute
3. **Skip NAT Gateway** → Save $35/month (use VPC endpoints instead)
4. **Reserved RDS instance** → Save ~40% if committed for 1 year

---

## Comparison: Build vs Buy

| Approach | Monthly | Notes |
|----------|---------|-------|
| **This POC** | $40-85 | Full control, customizable |
| **Metaview AI features** | ? | Check if included in plan |
| **Lever integrations** | ? | May have native AI features |

---

## ROI Consideration

**Time saved per candidate:**
- Manual: ~30-45 min (gather data, analyze, write summary)
- With POC: ~5 min (review AI output, make decision)

**At 50 candidates/month:**
- Time saved: ~25-35 hours/month
- At $50/hr loaded cost: $1,250-1,750/month saved
- POC cost: ~$85/month
- **ROI: ~15-20x**
