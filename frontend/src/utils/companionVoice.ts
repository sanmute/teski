import { CompanionCharacter } from "@/components/PetFrog";

type CompanionEvent = "mark-done" | "undo";

const getIntensityLevel = (): "mild" | "medium" | "spicy" => {
  if (typeof window === "undefined") return "medium";
  const raw = window.localStorage.getItem("frog-intensity");
  const value = raw ? parseInt(raw, 10) : 5;
  if (Number.isNaN(value)) return "medium";
  if (value <= 3) return "mild";
  if (value <= 6) return "medium";
  return "spicy";
};

export const getCompanionMessage = (
  companion: CompanionCharacter,
  event: CompanionEvent,
  taskTitle: string
): string => {
  if (companion === "cat") {
    if (event === "mark-done") {
      return `Purrfect. “${taskTitle}” is off the list. I’ll allow you a smug grin.`;
    }
    return `Uh oh. “${taskTitle}” is back. Try not to leave claw marks next time.`;
  }

  const intensity = getIntensityLevel();

  if (event === "mark-done") {
    switch (intensity) {
      case "mild":
        return `Nice hop! “${taskTitle}” is handled. Keep the ripples going.`;
      case "medium":
        return `Splash! “${taskTitle}” is history. Don’t lose momentum.`;
      case "spicy":
      default:
        return `BOOM! “${taskTitle}” obliterated. Feed me another deadline.`;
    }
  }

  // undo
  switch (intensity) {
    case "mild":
      return `Alright, “${taskTitle}” is back in the pond. We’ve got this.`;
    case "medium":
      return `Croak! “${taskTitle}” returned. No more lily-pad lounging.`;
    case "spicy":
    default:
      return `Seriously? “${taskTitle}” is back?! Hop to it, now!`;
  }
};

