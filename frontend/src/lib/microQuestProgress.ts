const STORAGE_KEY = "teski_microquest_runs_v1";

type RunHistory = Record<string, number>;

const formatDateKey = (date: Date = new Date()): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const readHistory = (): RunHistory => {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as RunHistory;
  } catch {
    return {};
  }
};

const writeHistory = (history: RunHistory) => {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
};

const pruneHistory = (history: RunHistory, keepDays = 14): RunHistory => {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - keepDays);
  const cutoffKey = formatDateKey(cutoff);
  return Object.fromEntries(
    Object.entries(history).filter(([key]) => key >= cutoffKey),
  );
};

export const recordMicroQuestRun = (count = 1) => {
  if (typeof window === "undefined") return;
  const history = pruneHistory(readHistory());
  const key = formatDateKey();
  history[key] = (history[key] ?? 0) + count;
  writeHistory(history);
  window.dispatchEvent(new Event("teski-microquest-run"));
};

export const getMicroQuestTodayCount = () => {
  if (typeof window === "undefined") return 0;
  const history = readHistory();
  const key = formatDateKey();
  return history[key] ?? 0;
};

export const getMicroQuestWeeklyCount = (days = 7) => {
  if (typeof window === "undefined") return 0;
  const history = readHistory();
  let total = 0;
  for (let offset = 0; offset < days; offset += 1) {
    const date = new Date();
    date.setDate(date.getDate() - offset);
    const key = formatDateKey(date);
    total += history[key] ?? 0;
  }
  return total;
};
