/**
 * Popovers: each `.pop-wrap` toggles `.open` from its first button.
 * One open at a time; closes on an outside click or Esc; keeps `aria-expanded` in sync.
 */
export function initPopovers() {
  const wraps = Array.from(document.querySelectorAll<HTMLElement>(".pop-wrap"));
  const triggerOf = (wrap: HTMLElement) => wrap.querySelector<HTMLButtonElement>("button");

  function setOpen(target: HTMLElement | null) {
    for (const wrap of wraps) {
      const open = wrap === target;
      wrap.classList.toggle("open", open);
      triggerOf(wrap)?.setAttribute("aria-expanded", open ? "true" : "false");
    }
  }
  const closeAll = () => setOpen(null);

  for (const wrap of wraps) {
    triggerOf(wrap)?.addEventListener("click", (event) => {
      event.stopPropagation();
      setOpen(wrap.classList.contains("open") ? null : wrap);
    });
  }
  document.addEventListener("click", (event) => {
    const target = event.target as Node | null;
    if (target && !wraps.some((wrap) => wrap.contains(target))) closeAll();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });
  return { closeAll };
}
