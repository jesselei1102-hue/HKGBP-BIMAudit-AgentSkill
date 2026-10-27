// Post an instruction to the chat. Hosts differ in what they declare: Claude lists the message capability, Cursor
// handles ui/message without listing it. So always try, and let the caller fall back only when the host refuses.

export type ChatHost = {
  sendMessage(params: { role: "user"; content: { type: "text"; text: string }[] }): Promise<{ isError?: boolean } | unknown>;
};

export async function postToChat(app: ChatHost, text: string): Promise<boolean> {
  try {
    const r = (await app.sendMessage({ role: "user", content: [{ type: "text", text }] })) as { isError?: boolean } | undefined;
    return !r?.isError;
  } catch {
    return false;
  }
}
