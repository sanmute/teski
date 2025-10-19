// >>> ANALYTICS START
export function logClient(event: string, props: Record<string, any> = {}) {
  try {
    console.info("[analytics]", event, props);
  } catch {
    // no-op in environments without console
  }
}
// <<< ANALYTICS END
