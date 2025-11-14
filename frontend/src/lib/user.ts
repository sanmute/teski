const USER_ID_STORAGE_KEY = "teski-user-id";
const NIL_UUID = "00000000-0000-0000-0000-000000000000";
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function generateUserId(): string {
  if (typeof window === "undefined") {
    return NIL_UUID;
  }
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  if (typeof crypto !== "undefined" && typeof crypto.getRandomValues === "function") {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }
  let timestamp = Date.now();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const r = ((timestamp + Math.random() * 16) % 16) | 0;
    timestamp = Math.floor(timestamp / 16);
    const value = char === "x" ? r : (r & 0x3) | 0x8;
    return value.toString(16);
  });
}

function isValidUuid(value: string | null): value is string {
  return typeof value === "string" && UUID_REGEX.test(value);
}

export function getClientUserId(): string {
  if (typeof window === "undefined") {
    return NIL_UUID;
  }
  const existing = window.localStorage.getItem(USER_ID_STORAGE_KEY);
  if (isValidUuid(existing)) {
    return existing;
  }
  const fresh = generateUserId();
  window.localStorage.setItem(USER_ID_STORAGE_KEY, fresh);
  return fresh;
}
