# Onboarding Wizard Design

## Problem
New users land on an empty dashboard with no understanding of what TAP does or what to do first. The natural workflow (team -> position -> candidate -> upload -> AI evaluation) is invisible.

## Target Audience
- Recruitment team: manages candidates, positions, uploads documents
- Hiring managers / technical evaluators: review AI-generated evaluations

## Approach
Multi-step modal wizard. Auto-opens on first login. Explains value prop, shows workflow, optionally walks through creating first team + position. Always re-accessible from sidebar help button.

## Wizard Steps

### Step 1: Welcome
- Title: "Welcome to Tap"
- Three bullets: automate candidate eval with AI, connect hiring pipeline from CV to decision, consistent rubric-based decisions across teams
- CTA: "Let's get started"

### Step 2: How It Works
- 4-step visual flow with icons:
  1. Create Position (define what you're hiring for)
  2. Add Candidates (link them to positions)
  3. Upload Documents (CVs and transcripts)
  4. AI Evaluates (rubric-based assessments)
- Note for hiring managers: "You'll review AI-generated evaluations for your positions"

### Step 3: Create Team (skipped if teams exist)
- Single input: team name
- Uses existing `useCreateTeam` mutation
- "Skip" or "Create & Continue"

### Step 4: Create Position (skipped if positions exist)
- Fields: title, team (dropdown), hiring manager
- Uses existing `useCreatePosition` mutation
- "Skip" or "Create & Continue"

### Step 5: You're Ready
- Summary of what was created (or skipped)
- Actions: "Go to Dashboard" / "Add Your First Candidate"
- Sets localStorage flag `tap-onboarding-completed`

## Behavior
- Auto-opens on first login (localStorage check)
- Progress bar at top showing current step
- Back/Skip navigation on all steps
- Re-accessible via "?" button at bottom of sidebar
- When re-opened: starts from step 1, skips setup steps if data exists

## Component Architecture (FSD)

```
src/
  features/onboarding/
    use-onboarding-wizard.ts     -- step state, nav, localStorage
    index.ts
  widgets/onboarding/
    onboarding-wizard.tsx         -- Dialog + progress bar + step rendering
    steps/
      welcome-step.tsx
      how-it-works-step.tsx
      create-team-step.tsx
      create-position-step.tsx
      ready-step.tsx
    index.ts
```

## Integration Points
- `_authenticated.tsx` renders `<OnboardingWizard />`
- `Sidebar` gets help button that triggers wizard
- Uses existing: Dialog, Progress, Button, Input, Select, Label components
- Uses existing: `useCreateTeam`, `useCreatePosition` mutations
- localStorage key: `tap-onboarding-completed`

## Existing Patterns Used
- Multi-step dialog pattern from GlobalUploadMenu
- shadcn Dialog component
- FSD: features/ for hooks, widgets/ for UI composition
- TanStack Query mutations for data creation
