import path from "node:path";

export type Config = { packageRoot: string; runsRoot: string };

/**
 * `here` is the folder of the running server file (app/build or app/src); the package root is the folder above app/.
 * Audit runs: --runs <dir>, else GBP_AUDIT_RUNS, else model-audit-runs next to the package.
 */
export function resolveConfig(argv: string[], env: NodeJS.ProcessEnv, here: string): Config {
  const packageRoot = path.resolve(here, "..", "..");
  const i = argv.indexOf("--runs");
  const arg = i >= 0 ? argv[i + 1] : undefined;
  const runsRoot = path.resolve(arg || env.GBP_AUDIT_RUNS || path.join(packageRoot, "..", "model-audit-runs"));
  return { packageRoot, runsRoot };
}
