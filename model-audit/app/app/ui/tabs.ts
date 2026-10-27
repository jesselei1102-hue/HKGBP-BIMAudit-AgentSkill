/**
 * Tabs: buttons `.tab[data-tab="x"]` switch panels `#panel-x`, looked up inside `root` (default: the document).
 * Keeps `.on`, `aria-selected` and the panels' `hidden` in sync. Starts on the first tab.
 */
export function initTabs(onChange?: (name: string) => void, root: ParentNode = document) {
  const buttons = Array.from(root.querySelectorAll<HTMLButtonElement>(".tab[data-tab]"));
  let active = buttons[0]?.dataset.tab ?? "";

  function set(name: string) {
    active = name;
    for (const button of buttons) {
      const tab = button.dataset.tab ?? "";
      const on = tab === name;
      button.classList.toggle("on", on);
      button.setAttribute("aria-selected", on ? "true" : "false");
      const panel = root.querySelector<HTMLElement>(`#panel-${tab}`);
      if (panel) panel.hidden = !on;
    }
    onChange?.(name);
  }

  for (const button of buttons) {
    button.addEventListener("click", () => set(button.dataset.tab ?? ""));
  }
  if (active) set(active);
  return { set, current: () => active };
}
