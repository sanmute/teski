import { useState } from "react";

import { ExplainPanel } from "@/components/ExplainPanel";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export default function Help() {
  const [text, setText] = useState("");
  const [submittedText, setSubmittedText] = useState<string | null>(null);

  const handleExplain = () => {
    if (text.trim()) {
      setSubmittedText(text);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-lg border p-4">
        <h2 className="text-lg font-semibold">What Teski can do</h2>
        <ul className="mt-2 list-disc pl-5 text-sm text-muted-foreground space-y-1">
          <li>Break tasks into personalized study blocks.</li>
          <li>Adjust durations to your time-estimation patterns.</li>
          <li>Generate explanations in the style that works best for you.</li>
        </ul>
      </section>

      <section className="rounded-lg border p-4 space-y-3">
        <h2 className="text-lg font-semibold">Try an explanation</h2>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste a passage and see how Teski explains it…"
        />
        <Button onClick={handleExplain} disabled={!text.trim()}>
          Explain this
        </Button>
      </section>

      {submittedText && (
        <section className="rounded-lg border">
          <ExplainPanel text={submittedText} />
        </section>
      )}
    </div>
  );
}
