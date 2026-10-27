// GBP Model Audit window. The two views (choose checks, overview) are added in later steps.
import { App } from "@modelcontextprotocol/ext-apps";
import { applyInitialHostTheme, initTheme } from "./theme/theme";

const app = new App({ name: "GBP Model Audit", version: "0.1.0" });
initTheme(app, { toggle: document.getElementById("btn-theme") as HTMLButtonElement });

await app.connect();
applyInitialHostTheme(app);
