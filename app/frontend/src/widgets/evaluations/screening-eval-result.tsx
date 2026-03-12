import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/shared/ui/collapsible";

interface ScreeningEvalResult {
  key_topics: string[];
  strengths: string[];
  concerns: string[];
  communication_quality: string;
  motivation_culture_fit: string;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
      {children}
    </p>
  );
}

function BulletList({
  items,
  className,
}: {
  items: string[];
  className?: string;
}) {
  return (
    <ul className={`space-y-1 ${className ?? ""}`}>
      {items.map((item, idx) => (
        <li key={idx} className="flex items-start gap-2 text-sm">
          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-current opacity-50" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

const COLLAPSE_THRESHOLD = 4;

function CollapsibleSection({
  label,
  items,
  listClassName,
}: {
  label: string;
  items: string[];
  listClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const shouldCollapse = items.length > COLLAPSE_THRESHOLD;

  if (!shouldCollapse) {
    return (
      <div>
        <SectionLabel>{label}</SectionLabel>
        <BulletList items={items} className={listClassName} />
      </div>
    );
  }

  return (
    <div>
      <SectionLabel>{label}</SectionLabel>
      <Collapsible open={open} onOpenChange={setOpen}>
        <BulletList items={items.slice(0, COLLAPSE_THRESHOLD)} className={listClassName} />
        <CollapsibleContent>
          <BulletList items={items.slice(COLLAPSE_THRESHOLD)} className={listClassName} />
        </CollapsibleContent>
        <CollapsibleTrigger className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
          {open ? (
            <>
              <ChevronDown className="size-3" /> Show less
            </>
          ) : (
            <>
              <ChevronRight className="size-3" /> Show {items.length - COLLAPSE_THRESHOLD} more
            </>
          )}
        </CollapsibleTrigger>
      </Collapsible>
    </div>
  );
}

export function ScreeningEvalResult({
  result,
}: {
  result: ScreeningEvalResult;
}) {
  return (
    <div className="space-y-6">
      <CollapsibleSection label="Key Topics" items={result.key_topics} />

      <div className="bg-green-50/50 rounded-lg p-3">
        <CollapsibleSection
          label="Strengths"
          items={result.strengths}
          listClassName="text-green-800 dark:text-green-400"
        />
      </div>

      <div className="bg-amber-50/50 rounded-lg p-3">
        <CollapsibleSection
          label="Concerns"
          items={result.concerns}
          listClassName="text-amber-800 dark:text-amber-400"
        />
      </div>

      <div>
        <SectionLabel>Communication Quality</SectionLabel>
        <p className="text-sm leading-relaxed">{result.communication_quality}</p>
      </div>

      <div>
        <SectionLabel>Motivation &amp; Culture Fit</SectionLabel>
        <p className="text-sm leading-relaxed">{result.motivation_culture_fit}</p>
      </div>
    </div>
  );
}
