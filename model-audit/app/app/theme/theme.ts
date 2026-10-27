import { applyDocumentTheme, applyHostFonts, type App, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";

export type Theme = "light" | "dark";
type ThemeStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;

/** Override (sun/moon choice) wins, then the host's theme, then the OS preference. */
export function resolveTheme(override: Theme | null, host: Theme | undefined, system: Theme): Theme {
  return override ?? host ?? system;
}

/** The override after a toggle; null when the toggle lands back on the base theme (follow the host again). */
export function nextOverride(current: Theme, base: Theme): Theme | null {
  const next: Theme = current === "dark" ? "light" : "dark";
  return next === base ? null : next;
}

/** Storage that survives sandboxes: any storage error falls back to an in-memory value. */
export function createThemeStore(storage: ThemeStorage | undefined, key = "uv-theme") {
  let memory: Theme | null = null;
  const parse = (v: string | null): Theme | null => (v === "light" || v === "dark" ? v : null);
  return {
    read(): Theme | null {
      try {
        if (storage) return parse(storage.getItem(key)) ?? memory;
      } catch {
        // blocked storage: use memory
      }
      return memory;
    },
    write(value: Theme | null) {
      memory = value;
      try {
        if (value) storage?.setItem(key, value);
        else storage?.removeItem(key);
      } catch {
        // blocked storage: memory already updated
      }
    },
  };
}

function safeLocalStorage(): ThemeStorage | undefined {
  try {
    return window.localStorage;
  } catch {
    return undefined;
  }
}

function asTheme(value: unknown): Theme | undefined {
  return value === "light" || value === "dark" ? value : undefined;
}

/**
 * Follow the host's light/dark theme and fonts, with an optional sun/moon toggle.
 * Owns app.onhostcontextchanged — pass your own handler as options.onHostContextChanged.
 * The toggle button should contain elements with [data-icon="sun"] and [data-icon="moon"].
 */
export function initTheme(
  app: App,
  options: {
    toggle?: HTMLButtonElement;
    onHostContextChanged?: (ctx: McpUiHostContext) => void;
  } = {}
): void {
  const store = createThemeStore(safeLocalStorage());
  const media = window.matchMedia?.("(prefers-color-scheme: dark)");
  let hostTheme: Theme | undefined;

  const system = (): Theme => (media?.matches ? "dark" : "light");
  const base = (): Theme => hostTheme ?? system();
  const current = (): Theme => resolveTheme(store.read(), hostTheme, system());

  const apply = () => {
    const theme = current();
    applyDocumentTheme(theme);
    const toggle = options.toggle;
    if (!toggle) return;
    const sun = toggle.querySelector<HTMLElement>('[data-icon="sun"]');
    const moon = toggle.querySelector<HTMLElement>('[data-icon="moon"]');
    if (sun) sun.hidden = theme === "light";
    if (moon) moon.hidden = theme === "dark";
    const label = theme === "dark" ? "Switch to light" : "Switch to dark";
    toggle.title = label;
    toggle.setAttribute("aria-label", label);
  };

  const readHost = (ctx: Partial<McpUiHostContext> | undefined) => {
    hostTheme = asTheme(ctx?.theme) ?? hostTheme;
    const fonts = ctx?.styles?.css?.fonts;
    if (fonts) applyHostFonts(fonts);
  };

  options.toggle?.addEventListener("click", () => {
    store.write(nextOverride(current(), base()));
    apply();
  });
  media?.addEventListener?.("change", apply);
  app.onhostcontextchanged = (ctx) => {
    readHost(ctx);
    apply();
    options.onHostContextChanged?.(ctx);
  };

  apply();
}

/** Call after `await app.connect()` so the initial host theme/fonts apply immediately. */
export function applyInitialHostTheme(app: App): void {
  const ctx = app.getHostContext?.();
  if (!ctx) return;
  app.onhostcontextchanged?.(ctx);
}
