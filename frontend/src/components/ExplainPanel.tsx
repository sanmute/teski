import { useEffect, useMemo, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";

import { generateExplanation } from "@/api/explanations";
import { ExplanationBlock, ExplanationResponse, ExplanationStyle } from "@/types/explanations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { cn } from "@/lib/utils";

interface ExplainPanelProps {
  text: string;
  mode?: string;
}

const STYLE_LABELS: Record<ExplanationStyle, string> = {
  step_by_step: "Step-by-step",
  big_picture: "Big picture",
  analogy: "Analogy",
  visual: "Visual outline",
  problems: "Practice-oriented",
};

const STYLE_CONTROLS = [
  { value: "auto", label: "Auto" },
  { value: "step_by_step", label: "Steps" },
  { value: "big_picture", label: "Big picture" },
  { value: "analogy", label: "Analogy" },
  { value: "visual", label: "Visual" },
  { value: "problems", label: "Problems" },
] as const;

export function ExplainPanel({ text, mode = "auto" }: ExplainPanelProps) {
  const [activeMode, setActiveMode] = useState(mode);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshCounter, setRefreshCounter] = useState(0);

  useEffect(() => {
    setActiveMode(mode);
  }, [mode]);

  useEffect(() => {
    const trimmed = text?.trim();
    if (!trimmed) {
      setError("No text provided to explain.");
      setData(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    const fetchExplanation = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await generateExplanation(trimmed, activeMode);
        if (!cancelled) {
          setData(response);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to generate explanation");
          setData(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchExplanation();

    return () => {
      cancelled = true;
    };
  }, [text, activeMode, refreshCounter]);

  const chosenLabel = useMemo(() => {
    if (!data) return null;
    return STYLE_LABELS[data.chosen_style];
  }, [data]);

  const renderBlock = (block: ExplanationBlock, index: number) => {
    switch (block.style) {
      case "step_by_step":
        return renderStepBlock(block);
      case "big_picture":
        return renderBigPictureBlock(block, index);
      case "analogy":
        return renderAnalogyBlock(block);
      case "visual":
        return renderVisualBlock(block);
      case "problems":
        return renderProblemsBlock(block);
      default:
        return renderDefaultBlock(block);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Mode</p>
          <p className="text-base font-semibold">
            {chosenLabel ?? "Preparing explanation…"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {STYLE_CONTROLS.map(({ value, label }) => (
            <Button
              key={value}
              size="sm"
              variant={activeMode === value ? "default" : "outline"}
              onClick={() => setActiveMode(value)}
              disabled={loading && activeMode === value}
            >
              {label}
            </Button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="space-y-3 animate-in fade-in duration-200">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && data && (
        <div className="space-y-4 transition-opacity">
          {data.blocks.map((block, idx) => (
            <div key={`${block.style}-${idx}`} className="mt-4 first:mt-0">
              {renderBlock(block, idx)}
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end pt-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setRefreshCounter((count) => count + 1)}
          disabled={loading}
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating…
            </span>
          ) : (
            "Regenerate"
          )}
        </Button>
      </div>
    </div>
  );
}

function renderStepBlock(block: ExplanationBlock) {
  const steps = block.content.split(/\n+/).filter(Boolean);
  return (
    <Card className="border-primary/30 shadow-sm">
      <CardHeader>
        <CardTitle className="text-base">{block.title ?? "Step-by-step explanation"}</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
          {steps.map((step, idx) => (
            <li key={`${idx}-${step.slice(0, 8)}`}>{step}</li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function renderBigPictureBlock(block: ExplanationBlock, index: number) {
  const isSummary = block.title?.toLowerCase().includes("summary") || index === 0;
  if (isSummary) {
    return (
      <Card className="border border-primary/40 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-base">{block.title ?? "Summary"}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground leading-relaxed">{block.content}</p>
        </CardContent>
      </Card>
    );
  }
  return (
    <Accordion type="single" collapsible className="w-full rounded-md border">
      <AccordionItem value="details">
        <AccordionTrigger>Details</AccordionTrigger>
        <AccordionContent>
          <p className="whitespace-pre-wrap text-sm text-muted-foreground">{block.content}</p>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

function renderAnalogyBlock(block: ExplanationBlock) {
  const isAnalogy = block.title?.toLowerCase().includes("analogy");
  return (
    <Card
      className={cn(
        "shadow-inner",
        isAnalogy ? "border-amber-300 bg-amber-50/60" : "border-border"
      )}
    >
      <CardHeader>
        <CardTitle className="text-base">
          {block.title ?? (isAnalogy ? "Analogy" : "Explanation")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm leading-relaxed text-foreground">{block.content}</p>
      </CardContent>
    </Card>
  );
}

function renderVisualBlock(block: ExplanationBlock) {
  return (
    <Card className="border-l-4 border-l-primary/80 shadow-none">
      <CardHeader>
        <CardTitle className="text-base">{block.title ?? "Outline"}</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="whitespace-pre-wrap font-mono text-sm text-muted-foreground">{block.content}</pre>
      </CardContent>
    </Card>
  );
}

function renderProblemsBlock(block: ExplanationBlock) {
  const isExample = block.title?.toLowerCase().includes("example");
  return (
    <Card className={cn("shadow-sm", isExample ? "border-sky-200 bg-sky-50/60" : "border-border")}>
      <CardHeader>
        <CardTitle className="text-base">{block.title ?? (isExample ? "Example" : "Explanation")}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm leading-relaxed text-muted-foreground">{block.content}</p>
      </CardContent>
    </Card>
  );
}

function renderDefaultBlock(block: ExplanationBlock) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{block.title ?? "Explanation"}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{block.content}</p>
      </CardContent>
    </Card>
  );
}
