import { useEffect, useState } from "react";

import type { CharacterId } from "@/types/characters";

export type SessionPhase = "prepare" | "focus" | "close";

type Mood = "neutral" | "encouraging" | "celebrate" | "concerned";

interface CompanionState {
  line: string;
  mood: Mood;
}

const SCRIPTS: Record<
  CharacterId,
  {
    prepareStart: string[];
    focusStart: string[];
    focusMid: string[];
    focusIdle: string[];
    closeStart: string[];
    closeDone: string[];
  }
> = {
  character1: {
    prepareStart: ["Let's keep this simple and doable.", "We’ll take this one step at a time."],
    focusStart: ["Good, you’ve started. Stay with this block.", "Nice. Just focus on the next small step."],
    focusMid: ["You’re doing fine. Keep the pace comfortable.", "Stay with it. You don’t need to rush."],
    focusIdle: ["Still here? Take a breath and pick one step to continue."],
    closeStart: ["Almost there. Let’s wrap this block up calmly."],
    closeDone: ["Session done. That’s real progress.", "Good work. Future you will appreciate this."],
  },
  character2: {
    prepareStart: ["Alright, short block, big impact. Let’s go.", "We’re not overthinking this. Just start."],
    focusStart: ["Timer’s ticking. Show this task who's boss.", "You started. That’s the hardest part."],
    focusMid: ["One more push. You’ve got this.", "Don’t bail now. You’re already in it."],
    focusIdle: ["You paused. Tap into that energy and do one more step."],
    closeStart: ["Last stretch. Finish strong."],
    closeDone: ["Block cleared. Nice.", "Done. That’s a win on the board."],
  },
  character3: {
    prepareStart: ["Define a clear, small goal for this block.", "Let’s structure this: warm-up, core, review."],
    focusStart: ["Focus on executing the plan, one step at a time.", "Stay systematic. Don’t skip the fundamentals."],
    focusMid: ["Check in: are you still following the structure?", "Good. Keep the logic clear as you work."],
    focusIdle: ["Regroup. Identify the next precise step and continue."],
    closeStart: ["Time to summarize what you actually did."],
    closeDone: ["Session complete. You just added another data point of effort."],
  },
  character4: {
    prepareStart: ["You starting this is already a big step.", "Let’s turn this block into something you’re proud of."],
    focusStart: ["You’re doing great. Just keep moving gently forward.", "Stay kind to yourself and keep going."],
    focusMid: ["Look at you, still here. That matters.", "You’re handling this better than you think."],
    focusIdle: ["It’s okay to pause. When you’re ready, take one small step."],
    closeStart: ["Deep breath. Let’s close this with a small reflection."],
    closeDone: ["Beautiful work. That’s one more step towards your goals."],
  },
  character5: {
    prepareStart: ["You chose this block. Now we follow through.", "Set a clear target and commit to it."],
    focusStart: ["No distractions. Just this task.", "Stay on it. You’re here to work."],
    focusMid: ["Maintain focus. Finish what you started.", "Keep the quality up for a few minutes longer."],
    focusIdle: ["You stopped. Re-engage and finish the block."],
    closeStart: ["Wrap up properly. Don’t just walk away."],
    closeDone: ["Session complete. Discipline executed."],
  },
};

function pickRandom(lines: string[]): string {
  if (!lines.length) return "";
  return lines[Math.floor(Math.random() * lines.length)];
}

export function useSessionCompanion(phase: SessionPhase, elapsedMinutes: number, character: CharacterId): CompanionState {
  const [state, setState] = useState<CompanionState>({
    line: "",
    mood: "neutral",
  });

  useEffect(() => {
    const script = SCRIPTS[character];
    if (!script) return;

    if (phase === "prepare") {
      setState({
        line: pickRandom(script.prepareStart),
        mood: "neutral",
      });
      return;
    }

    if (phase === "focus") {
      if (elapsedMinutes === 0) {
        setState({
          line: pickRandom(script.focusStart),
          mood: "encouraging",
        });
      } else if (elapsedMinutes > 0 && elapsedMinutes % 10 === 0) {
        setState({
          line: pickRandom(script.focusMid),
          mood: "encouraging",
        });
      }
      return;
    }

    if (phase === "close") {
      setState({
        line: pickRandom(script.closeStart),
        mood: "neutral",
      });
    }
  }, [character, elapsedMinutes, phase]);

  return state;
}
