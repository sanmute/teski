import { useEffect } from "react";

import type { CharacterId } from "@/types/characters";

const STORAGE_KEY = "teski.activeCharacter";

export function useCharacterTheme(activeCharacter: CharacterId) {
  useEffect(() => {
    const root = document.documentElement;
    root.dataset.character = activeCharacter;

    try {
      window.localStorage.setItem(STORAGE_KEY, activeCharacter);
    } catch {
      /* ignore storage errors */
    }

    return () => {
      root.dataset.character = "";
    };
  }, [activeCharacter]);
}

export function getInitialCharacter(): CharacterId {
  if (typeof window === "undefined") return "character1";
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY) as CharacterId | null;
    if (
      stored === "character1" ||
      stored === "character2" ||
      stored === "character3" ||
      stored === "character4" ||
      stored === "character5"
    ) {
      return stored;
    }
  } catch {
    /* ignore */
  }
  return "character1";
}
