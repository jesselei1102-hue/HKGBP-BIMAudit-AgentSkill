/** The slice of the ext-apps App this helper needs (App satisfies it). */
export type ContextHost = {
  getHostCapabilities(): { updateModelContext?: unknown } | undefined;
  updateModelContext(params: { content: { type: "text"; text: string }[] }): Promise<unknown>;
};

/**
 * Share app state with the host model. Debounced; skips unchanged text; silently does nothing on
 * hosts without updateModelContext (e.g. Cursor); a failed send is retried on the next schedule().
 */
export function createModelContext(host: ContextHost, build: () => string, delayMs = 400) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  let last = "";

  async function publish() {
    if (!host.getHostCapabilities()?.updateModelContext) return;
    const text = build();
    if (text === last) return;
    last = text;
    try {
      await host.updateModelContext({ content: [{ type: "text", text }] });
    } catch {
      last = "";
    }
  }

  return {
    schedule() {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => void publish(), delayMs);
    },
  };
}
