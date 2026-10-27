import type { App } from "@modelcontextprotocol/ext-apps";
import { postToChat } from "./logic/post";
import { escapeHtml } from "./ui/html";

/**
 * Copy text. Hosts often run the window without clipboard permission, so: the Clipboard API, then the older copy
 * command, and when both fail a selected text box above the dock for Ctrl+C. Resolves true only when copied.
 */
export async function copyText(text: string, view: HTMLElement): Promise<boolean> {
  view.querySelector(".copy-box")?.remove();
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // no clipboard permission in this host
  }
  const area = document.createElement("textarea");
  area.value = text;
  area.readOnly = true;
  const box = document.createElement("div");
  box.className = "prompt-box copy-box";
  box.innerHTML = "<p>This window cannot use the clipboard here. The text is selected: press Ctrl+C to copy it.</p>";
  box.append(area);
  const dock = view.querySelector(".dock");
  if (dock) dock.before(box);
  else view.append(box);
  area.focus();
  area.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  if (ok) box.querySelector("p")!.textContent = "Copied. (The text is also shown here.)";
  return ok;
}

/**
 * Send an instruction to the chat. It is always tried (Cursor accepts it without declaring the capability); only
 * when the host refuses does a box with the text and a Copy link appear above the dock. Resolves true when sent.
 */
export async function sendToChat(app: App, text: string, view: HTMLElement): Promise<boolean> {
  view.querySelector(".prompt-box")?.remove();
  if (await postToChat(app, text)) return true;          // tried even when not declared (Cursor), as the Schedule app does
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
