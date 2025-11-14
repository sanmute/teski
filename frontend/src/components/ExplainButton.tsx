import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ExplainPanel } from "@/components/ExplainPanel";

interface ExplainButtonProps {
  text: string;
}

export function ExplainButton({ text }: ExplainButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="secondary" size="sm">
          Explain this
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Explain this</DialogTitle>
          <DialogDescription>
            Personalized explanation generated with your learning profile.
          </DialogDescription>
        </DialogHeader>
        <ExplainPanel text={text} />
      </DialogContent>
    </Dialog>
  );
}
