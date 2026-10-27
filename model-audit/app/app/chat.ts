import type { App } from "@modelcontextprotocol/ext-apps";
import { escapeHtml } from "./ui/html";

/**
 * Send an instruction to the chat. Hosts without the message capability (or a failed send) get a box with the
 * text and a Copy link above the dock instead. Resolves true when the host took the message.
 */
export async function sendToChat(app: App, text: string, view: HTMLElement): Promise<boolean> {
  view.querySelector(".prompt-box")?.remove();
  if (app.getHostCapabilities()?.message) {
    try {
      const r = (await app.sendMessage({ role: "user", content: [{ type: "text", text }] })) as { isError?: boolean };
      if (!r?.isError) return true;
    } catch {
      // fall through to the copy box
    }
  }
  const box = document.createElement("div");
  box.className = "prompt-box";
  box.innerHTML =
    `<p>This window cannot post to the chat here. Copy the instruction and paste it into the chat.</p>` +
    `<textarea readonly>${escapeHtml(text)}</textarea>` +
    `<button class="text-link" type="button" data-copy>Copy</button>`;
  const area = box.querySelector("textarea")!;
  box.querySelector<HTMLButtonElement>("[data-copy]")!.addEventListener("click", async (e) => {
    const btn = e.currentTarget as HTMLButtonElement;
    try {
      await navigator.clipboard.writeText(text);
      btn.textContent = "Copied";
    } catch {
      area.focus();
      area.select();
      btn.textContent = "Select all and copy";
    }
  });
  const dock = view.querySelector(".dock");
  if (dock) dock.before(box);
  else view.append(box);
  return false;
}
