# Onboarding Wizard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a multi-step onboarding wizard that explains Lauter's value and walks new users through creating their first team + position.

**Architecture:** Modal dialog wizard using the existing shadcn Dialog component. Feature hook manages step state + localStorage persistence. Widget renders steps. Mounted in the authenticated layout, triggered automatically on first login and manually via sidebar help button.

**Tech Stack:** React 19, TanStack Query mutations, shadcn/ui Dialog + Progress + Button + Input + Select, Lucide icons, localStorage, zod validation

---

### Task 1: Feature Hook — `useOnboardingWizard`

**Files:**
- Create: `src/features/onboarding/use-onboarding-wizard.ts`
- Create: `src/features/onboarding/index.ts`

**Step 1: Create the feature hook**

```typescript
// src/features/onboarding/use-onboarding-wizard.ts
import { useState, useCallback, useMemo } from "react";
import { useTeams } from "@/features/settings";
import { usePositions } from "@/features/positions";

const STORAGE_KEY = "lauter-onboarding-completed";

type WizardStep = "welcome" | "how-it-works" | "create-team" | "create-position" | "ready";

const ALL_STEPS: WizardStep[] = [
  "welcome",
  "how-it-works",
  "create-team",
  "create-position",
  "ready",
];

function isOnboardingCompleted(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function markOnboardingCompleted(): void {
  try {
    localStorage.setItem(STORAGE_KEY, "true");
  } catch {
    // localStorage unavailable — silently ignore
  }
}

export function useOnboardingWizard() {
  const [isOpen, setIsOpen] = useState(() => !isOnboardingCompleted());
  const [currentStep, setCurrentStep] = useState<WizardStep>("welcome");

  const { data: teams } = useTeams();
  const { data: positions } = usePositions({ limit: 1 });

  const hasTeams = (teams ?? []).length > 0;
  const hasPositions = (positions?.items ?? []).length > 0;

  const activeSteps = useMemo(() => {
    return ALL_STEPS.filter((step) => {
      if (step === "create-team" && hasTeams) return false;
      if (step === "create-position" && hasPositions) return false;
      return true;
    });
  }, [hasTeams, hasPositions]);

  const currentIndex = activeSteps.indexOf(currentStep);
  const progressPercent = ((currentIndex + 1) / activeSteps.length) * 100;

  const goNext = useCallback(() => {
    const nextIndex = currentIndex + 1;
    if (nextIndex < activeSteps.length) {
      setCurrentStep(activeSteps[nextIndex]);
    }
  }, [currentIndex, activeSteps]);

  const goBack = useCallback(() => {
    const prevIndex = currentIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(activeSteps[prevIndex]);
    }
  }, [currentIndex, activeSteps]);

  const complete = useCallback(() => {
    markOnboardingCompleted();
    setIsOpen(false);
    setCurrentStep("welcome");
  }, []);

  const open = useCallback(() => {
    setCurrentStep("welcome");
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setCurrentStep("welcome");
  }, []);

  return {
    isOpen,
    currentStep,
    activeSteps,
    progressPercent,
    isFirstStep: currentIndex === 0,
    isLastStep: currentIndex === activeSteps.length - 1,
    goNext,
    goBack,
    complete,
    open,
    close,
  };
}
```

```typescript
// src/features/onboarding/index.ts
export { useOnboardingWizard } from "./use-onboarding-wizard";
```

**Step 2: Verify the build**

Run: `cd /Users/nailbadiullin/Developer/provectus/recruitment-framework/app/frontend && bun run build`
Expected: PASS (hook is not imported anywhere yet, but should compile)

**Step 3: Commit**

```bash
git add src/features/onboarding/
git commit -m "feat(onboarding): add useOnboardingWizard hook with step management and localStorage"
```

---

### Task 2: Welcome Step Component

**Files:**
- Create: `src/widgets/onboarding/steps/welcome-step.tsx`

**Step 1: Create the welcome step**

```tsx
// src/widgets/onboarding/steps/welcome-step.tsx
import { Sparkles, ArrowRight, FileSearch, Scale } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface WelcomeStepProps {
  onNext: () => void;
}

const VALUE_POINTS = [
  {
    icon: FileSearch,
    title: "Automate candidate evaluation",
    description: "AI analyzes CVs and transcripts against your rubrics",
  },
  {
    icon: ArrowRight,
    title: "Connect your hiring pipeline",
    description: "From CV upload to hiring decision in one place",
  },
  {
    icon: Scale,
    title: "Consistent decisions across teams",
    description: "Rubric-based assessments ensure fair, structured evaluation",
  },
] as const;

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <div className="flex flex-col items-center text-center space-y-6 py-4">
      <div className="rounded-full bg-primary/10 p-4">
        <Sparkles className="h-8 w-8 text-primary" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-bold tracking-tight">Welcome to Lauter</h2>
        <p className="text-muted-foreground">
          Recruitment workflow automation for Provectus
        </p>
      </div>

      <div className="w-full space-y-4 text-left">
        {VALUE_POINTS.map((point) => (
          <div key={point.title} className="flex gap-3 items-start">
            <div className="rounded-lg bg-muted p-2 shrink-0">
              <point.icon className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <p className="font-medium text-sm">{point.title}</p>
              <p className="text-sm text-muted-foreground">{point.description}</p>
            </div>
          </div>
        ))}
      </div>

      <Button onClick={onNext} className="w-full">
        Let's get started
      </Button>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add src/widgets/onboarding/steps/welcome-step.tsx
git commit -m "feat(onboarding): add WelcomeStep component with value proposition"
```

---

### Task 3: How It Works Step Component

**Files:**
- Create: `src/widgets/onboarding/steps/how-it-works-step.tsx`

**Step 1: Create the how-it-works step**

```tsx
// src/widgets/onboarding/steps/how-it-works-step.tsx
import { Briefcase, Users, FileUp, Brain, ArrowDown } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface HowItWorksStepProps {
  onNext: () => void;
  onBack: () => void;
}

const WORKFLOW_STEPS = [
  {
    icon: Briefcase,
    label: "Create a Position",
    description: "Define what you're hiring for",
  },
  {
    icon: Users,
    label: "Add Candidates",
    description: "Link candidates to open positions",
  },
  {
    icon: FileUp,
    label: "Upload Documents",
    description: "Attach CVs and interview transcripts",
  },
  {
    icon: Brain,
    label: "AI Evaluates",
    description: "Get rubric-based assessments automatically",
  },
] as const;

export function HowItWorksStep({ onNext, onBack }: HowItWorksStepProps) {
  return (
    <div className="flex flex-col space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold tracking-tight">How Lauter works</h2>
        <p className="text-sm text-muted-foreground">
          Four steps from candidate to decision
        </p>
      </div>

      <div className="space-y-2">
        {WORKFLOW_STEPS.map((step, index) => (
          <div key={step.label}>
            <div className="flex items-center gap-3 rounded-lg border border-border/50 p-3">
              <div className="rounded-lg bg-primary/10 p-2 shrink-0">
                <step.icon className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-sm">{step.label}</p>
                <p className="text-xs text-muted-foreground">{step.description}</p>
              </div>
              <span className="text-xs font-medium text-muted-foreground/60">
                {index + 1}
              </span>
            </div>
            {index < WORKFLOW_STEPS.length - 1 && (
              <div className="flex justify-center py-1">
                <ArrowDown className="h-3 w-3 text-muted-foreground/40" />
              </div>
            )}
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground text-center italic">
        Hiring managers: you'll review AI-generated evaluations for your positions
      </p>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button onClick={onNext} className="flex-1">
          Continue
        </Button>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add src/widgets/onboarding/steps/how-it-works-step.tsx
git commit -m "feat(onboarding): add HowItWorksStep component with workflow visual"
```

---

### Task 4: Create Team Step Component

**Files:**
- Create: `src/widgets/onboarding/steps/create-team-step.tsx`

**Dependencies:**
- `useCreateTeam` from `@/features/settings` — mutation: `{ body: { name: string } }`

**Step 1: Create the team step**

```tsx
// src/widgets/onboarding/steps/create-team-step.tsx
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useCreateTeam } from "@/features/settings";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

interface CreateTeamStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function CreateTeamStep({ onNext, onBack }: CreateTeamStepProps) {
  const [teamName, setTeamName] = useState("");
  const [error, setError] = useState("");
  const createTeam = useCreateTeam();

  const handleCreate = () => {
    const trimmed = teamName.trim();
    if (!trimmed) {
      setError("Team name is required");
      return;
    }
    setError("");
    createTeam.mutate(
      { body: { name: trimmed } },
      {
        onSuccess: () => onNext(),
        onError: () => setError("Failed to create team. Try again."),
      }
    );
  };

  return (
    <div className="flex flex-col space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold tracking-tight">Create your first team</h2>
        <p className="text-sm text-muted-foreground">
          Teams organize positions and hiring managers
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="onboarding-team-name">Team name</Label>
        <Input
          id="onboarding-team-name"
          placeholder="e.g. Engineering, Design, Product"
          value={teamName}
          onChange={(e) => {
            setTeamName(e.target.value);
            setError("");
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleCreate();
          }}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button
          variant="outline"
          onClick={onNext}
          className="flex-1"
        >
          Skip
        </Button>
        <Button
          onClick={handleCreate}
          disabled={createTeam.isPending}
          className="flex-1"
        >
          {createTeam.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Create & continue
        </Button>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add src/widgets/onboarding/steps/create-team-step.tsx
git commit -m "feat(onboarding): add CreateTeamStep with inline team creation"
```

---

### Task 5: Create Position Step Component

**Files:**
- Create: `src/widgets/onboarding/steps/create-position-step.tsx`

**Dependencies:**
- `useCreatePosition` from `@/features/positions` — mutation: `{ body: { title, team_id, hiring_manager_id } }`
- `useTeams` from `@/features/settings` — returns `TeamResponse[]`
- `useUsers` from `@/features/positions` — returns user list for hiring manager dropdown
- `useAuth` from `@/features/auth` — current user for default hiring manager

**Step 1: Create the position step**

```tsx
// src/widgets/onboarding/steps/create-position-step.tsx
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { useCreatePosition, useUsers } from "@/features/positions";
import { useTeams } from "@/features/settings";
import { useAuth } from "@/features/auth";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";

interface CreatePositionStepProps {
  onNext: () => void;
  onBack: () => void;
}

export function CreatePositionStep({ onNext, onBack }: CreatePositionStepProps) {
  const { user } = useAuth();
  const { data: teams } = useTeams();
  const { data: users } = useUsers();
  const createPosition = useCreatePosition();

  const [title, setTitle] = useState("");
  const [teamId, setTeamId] = useState<number | null>(null);
  const [hiringManagerId, setHiringManagerId] = useState<number | null>(
    user?.id ?? null
  );
  const [error, setError] = useState("");

  const handleCreate = () => {
    if (!title.trim()) {
      setError("Position title is required");
      return;
    }
    if (!teamId) {
      setError("Please select a team");
      return;
    }
    if (!hiringManagerId) {
      setError("Please select a hiring manager");
      return;
    }
    setError("");
    createPosition.mutate(
      {
        body: {
          title: title.trim(),
          team_id: teamId,
          hiring_manager_id: hiringManagerId,
        },
      },
      {
        onSuccess: () => onNext(),
        onError: () => setError("Failed to create position. Try again."),
      }
    );
  };

  const teamList = teams ?? [];
  const userList = users ?? [];

  return (
    <div className="flex flex-col space-y-6 py-4">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold tracking-tight">Create your first position</h2>
        <p className="text-sm text-muted-foreground">
          Positions define what you're hiring for
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="onboarding-position-title">Position title</Label>
          <Input
            id="onboarding-position-title"
            placeholder="e.g. Senior Frontend Engineer"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setError("");
            }}
          />
        </div>

        <div className="space-y-2">
          <Label>Team</Label>
          {teamList.length > 0 ? (
            <Select
              value={teamId?.toString()}
              onValueChange={(v) => {
                setTeamId(parseInt(v, 10));
                setError("");
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a team" />
              </SelectTrigger>
              <SelectContent>
                {teamList.map((team) => (
                  <SelectItem key={team.id} value={team.id.toString()}>
                    {team.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <p className="text-sm text-muted-foreground">
              No teams yet — go back and create one first
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Hiring manager</Label>
          <Select
            value={hiringManagerId?.toString()}
            onValueChange={(v) => {
              setHiringManagerId(parseInt(v, 10));
              setError("");
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select hiring manager" />
            </SelectTrigger>
            <SelectContent>
              {userList.map((u) => (
                <SelectItem key={u.id} value={u.id.toString()}>
                  {u.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={onBack} className="flex-1">
          Back
        </Button>
        <Button variant="outline" onClick={onNext} className="flex-1">
          Skip
        </Button>
        <Button
          onClick={handleCreate}
          disabled={createPosition.isPending}
          className="flex-1"
        >
          {createPosition.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Create & continue
        </Button>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add src/widgets/onboarding/steps/create-position-step.tsx
git commit -m "feat(onboarding): add CreatePositionStep with inline position creation"
```

---

### Task 6: Ready Step Component

**Files:**
- Create: `src/widgets/onboarding/steps/ready-step.tsx`

**Step 1: Create the ready step**

```tsx
// src/widgets/onboarding/steps/ready-step.tsx
import { useNavigate } from "@tanstack/react-router";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface ReadyStepProps {
  onComplete: () => void;
}

export function ReadyStep({ onComplete }: ReadyStepProps) {
  const navigate = useNavigate();

  const handleGoToDashboard = () => {
    onComplete();
    navigate({ to: "/dashboard" });
  };

  const handleAddCandidate = () => {
    onComplete();
    navigate({ to: "/candidates" });
  };

  return (
    <div className="flex flex-col items-center text-center space-y-6 py-4">
      <div className="rounded-full bg-green-500/10 p-4">
        <CheckCircle2 className="h-8 w-8 text-green-500" />
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-bold tracking-tight">You're all set!</h2>
        <p className="text-sm text-muted-foreground">
          You can always re-open this guide from the help button in the sidebar
        </p>
      </div>

      <div className="w-full space-y-2">
        <Button onClick={handleAddCandidate} className="w-full">
          Add your first candidate
        </Button>
        <Button variant="outline" onClick={handleGoToDashboard} className="w-full">
          Go to Dashboard
        </Button>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add src/widgets/onboarding/steps/ready-step.tsx
git commit -m "feat(onboarding): add ReadyStep completion component"
```

---

### Task 7: Onboarding Wizard Widget (Dialog Wrapper)

**Files:**
- Create: `src/widgets/onboarding/onboarding-wizard.tsx`
- Create: `src/widgets/onboarding/index.ts`

**Step 1: Create the wizard dialog**

```tsx
// src/widgets/onboarding/onboarding-wizard.tsx
import {
  Dialog,
  DialogContent,
} from "@/shared/ui/dialog";
import { Progress } from "@/shared/ui/progress";
import { useOnboardingWizard } from "@/features/onboarding";
import { WelcomeStep } from "./steps/welcome-step";
import { HowItWorksStep } from "./steps/how-it-works-step";
import { CreateTeamStep } from "./steps/create-team-step";
import { CreatePositionStep } from "./steps/create-position-step";
import { ReadyStep } from "./steps/ready-step";

export function OnboardingWizard() {
  const wizard = useOnboardingWizard();

  return (
    <Dialog open={wizard.isOpen} onOpenChange={(open) => !open && wizard.close()}>
      <DialogContent className="sm:max-w-md" showCloseButton={false}>
        <div className="space-y-1 mb-2">
          <Progress value={wizard.progressPercent} />
          <p className="text-xs text-muted-foreground text-right">
            {wizard.activeSteps.indexOf(wizard.currentStep) + 1} of{" "}
            {wizard.activeSteps.length}
          </p>
        </div>

        {wizard.currentStep === "welcome" && (
          <WelcomeStep onNext={wizard.goNext} />
        )}
        {wizard.currentStep === "how-it-works" && (
          <HowItWorksStep onNext={wizard.goNext} onBack={wizard.goBack} />
        )}
        {wizard.currentStep === "create-team" && (
          <CreateTeamStep onNext={wizard.goNext} onBack={wizard.goBack} />
        )}
        {wizard.currentStep === "create-position" && (
          <CreatePositionStep onNext={wizard.goNext} onBack={wizard.goBack} />
        )}
        {wizard.currentStep === "ready" && (
          <ReadyStep onComplete={wizard.complete} />
        )}
      </DialogContent>
    </Dialog>
  );
}
```

```typescript
// src/widgets/onboarding/index.ts
export { OnboardingWizard } from "./onboarding-wizard";
```

**Step 2: Verify build**

Run: `cd /Users/nailbadiullin/Developer/provectus/recruitment-framework/app/frontend && bun run build`
Expected: PASS (widget not mounted yet, but should compile)

**Step 3: Commit**

```bash
git add src/widgets/onboarding/
git commit -m "feat(onboarding): add OnboardingWizard dialog with step rendering and progress bar"
```

---

### Task 8: Integration — Mount Wizard + Add Sidebar Help Button

**Files:**
- Modify: `src/routes/_authenticated.tsx` — mount `<OnboardingWizard />`
- Modify: `src/widgets/sidebar/sidebar.tsx` — add help button that triggers wizard

**Context:** The wizard self-manages its open/close state via the hook + localStorage. However, the sidebar needs a way to re-open it. We need a shared state between the sidebar and the wizard. Simplest approach: lift the `useOnboardingWizard` hook to the authenticated layout and pass `open` function down via a context or prop.

**Step 1: Create onboarding context to share wizard controls**

Create: `src/features/onboarding/onboarding-context.tsx`

```tsx
// src/features/onboarding/onboarding-context.tsx
import { createContext, useContext } from "react";

interface OnboardingContextValue {
  openWizard: () => void;
}

export const OnboardingContext = createContext<OnboardingContextValue | null>(null);

export function useOpenOnboarding(): () => void {
  const ctx = useContext(OnboardingContext);
  if (!ctx) throw new Error("useOpenOnboarding must be used within OnboardingContext");
  return ctx.openWizard;
}
```

Update: `src/features/onboarding/index.ts`

```typescript
export { useOnboardingWizard } from "./use-onboarding-wizard";
export { OnboardingContext, useOpenOnboarding } from "./onboarding-context";
```

**Step 2: Update authenticated layout**

Modify `src/routes/_authenticated.tsx`:

```tsx
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Sidebar } from "@/widgets/sidebar";
import { OnboardingWizard } from "@/widgets/onboarding";
import { useOnboardingWizard, OnboardingContext } from "@/features/onboarding";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: ({ context, location }) => {
    if (context.auth.isLoading) return;
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/login",
        search: { redirect: location.href, error: undefined },
      });
    }
  },
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  const wizard = useOnboardingWizard();

  return (
    <OnboardingContext value={{ openWizard: wizard.open }}>
      <div className="flex h-[calc(100vh-49px)]">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
      <OnboardingWizard />
    </OnboardingContext>
  );
}
```

But wait — `OnboardingWizard` currently calls `useOnboardingWizard` internally. We need to refactor so the layout owns the hook and passes it to the wizard.

Update `src/widgets/onboarding/onboarding-wizard.tsx` to accept wizard state as props:

```tsx
// src/widgets/onboarding/onboarding-wizard.tsx
import {
  Dialog,
  DialogContent,
} from "@/shared/ui/dialog";
import { Progress } from "@/shared/ui/progress";
import { WelcomeStep } from "./steps/welcome-step";
import { HowItWorksStep } from "./steps/how-it-works-step";
import { CreateTeamStep } from "./steps/create-team-step";
import { CreatePositionStep } from "./steps/create-position-step";
import { ReadyStep } from "./steps/ready-step";

type WizardStep = "welcome" | "how-it-works" | "create-team" | "create-position" | "ready";

interface OnboardingWizardProps {
  isOpen: boolean;
  currentStep: WizardStep;
  activeSteps: WizardStep[];
  progressPercent: number;
  goNext: () => void;
  goBack: () => void;
  complete: () => void;
  close: () => void;
}

export function OnboardingWizard({
  isOpen,
  currentStep,
  activeSteps,
  progressPercent,
  goNext,
  goBack,
  complete,
  close,
}: OnboardingWizardProps) {
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && close()}>
      <DialogContent className="sm:max-w-md" showCloseButton={false}>
        <div className="space-y-1 mb-2">
          <Progress value={progressPercent} />
          <p className="text-xs text-muted-foreground text-right">
            {activeSteps.indexOf(currentStep) + 1} of {activeSteps.length}
          </p>
        </div>

        {currentStep === "welcome" && <WelcomeStep onNext={goNext} />}
        {currentStep === "how-it-works" && (
          <HowItWorksStep onNext={goNext} onBack={goBack} />
        )}
        {currentStep === "create-team" && (
          <CreateTeamStep onNext={goNext} onBack={goBack} />
        )}
        {currentStep === "create-position" && (
          <CreatePositionStep onNext={goNext} onBack={goBack} />
        )}
        {currentStep === "ready" && <ReadyStep onComplete={complete} />}
      </DialogContent>
    </Dialog>
  );
}
```

Update `src/routes/_authenticated.tsx` to pass props:

```tsx
function AuthenticatedLayout() {
  const wizard = useOnboardingWizard();

  return (
    <OnboardingContext value={{ openWizard: wizard.open }}>
      <div className="flex h-[calc(100vh-49px)]">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
      <OnboardingWizard
        isOpen={wizard.isOpen}
        currentStep={wizard.currentStep}
        activeSteps={wizard.activeSteps}
        progressPercent={wizard.progressPercent}
        goNext={wizard.goNext}
        goBack={wizard.goBack}
        complete={wizard.complete}
        close={wizard.close}
      />
    </OnboardingContext>
  );
}
```

**Step 3: Add help button to sidebar**

Modify `src/widgets/sidebar/sidebar.tsx` — add a `HelpCircle` button above the collapse toggle:

```tsx
// Add to imports:
import { HelpCircle } from "lucide-react";
import { useOpenOnboarding } from "@/features/onboarding";

// Inside Sidebar component, add before the collapse section:
const openOnboarding = useOpenOnboarding();

// In JSX — between <Separator /> and the collapse <div>:
<div className="p-2 pb-0">
  <Button
    variant="ghost"
    size="sm"
    className={cn(
      "w-full text-muted-foreground hover:text-foreground",
      collapsed ? "justify-center" : "justify-start px-3"
    )}
    onClick={openOnboarding}
    title="Getting started guide"
  >
    <HelpCircle className={cn("h-4 w-4", !collapsed && "mr-3")} />
    {!collapsed && <span className="text-sm">Getting Started</span>}
  </Button>
</div>
```

**Step 4: Verify build + lint**

Run: `cd /Users/nailbadiullin/Developer/provectus/recruitment-framework/app/frontend && bun run build && bun run lint`
Expected: PASS

**Step 5: Commit**

```bash
git add src/features/onboarding/ src/widgets/onboarding/ src/widgets/sidebar/sidebar.tsx src/routes/_authenticated.tsx
git commit -m "feat(onboarding): integrate wizard into authenticated layout with sidebar help button"
```

---

### Task 9: Manual Testing + Polish

**Step 1: Clear localStorage and test**

1. Open browser dev tools → Application → localStorage → delete `lauter-onboarding-completed`
2. Refresh the app
3. Verify wizard auto-opens on dashboard
4. Walk through all steps
5. Verify "Skip" buttons work
6. Create a team + position via the wizard
7. Verify localStorage flag is set after completion
8. Verify wizard doesn't auto-open on next refresh
9. Click sidebar "Getting Started" button → verify wizard re-opens

**Step 2: Test skip-all flow**

1. Clear localStorage again
2. Refresh
3. Skip through all steps without creating data
4. Verify wizard completes without errors

**Step 3: Test with existing data**

1. Ensure teams and positions exist in the DB
2. Clear localStorage
3. Refresh → wizard should skip create-team and create-position steps
4. Should go: welcome → how-it-works → ready (3 steps)

**Step 4: Final build + lint**

Run: `cd /Users/nailbadiullin/Developer/provectus/recruitment-framework/app/frontend && bun run build && bun run lint`
Expected: PASS

**Step 5: Commit any polish fixes**

```bash
git add -A
git commit -m "fix(onboarding): polish wizard flow and fix any issues from testing"
```
