import path from "node:path";

/** A path that would leave the folder the server is allowed to read or write. */
export class PathError extends Error {
  constructor(rel: string) {
    super(`Path is outside the allowed folder: ${rel}`);
    this.name = "PathError";
  }
}

/** True when `abs` is `root` or lies under it. */
export function isInside(root: string, abs: string): boolean {
  const rel = path.relative(path.resolve(root), path.resolve(abs));
  return rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel));
}

/** `rel` resolved under `root`; absolute paths and anything that climbs out are refused. */
export function resolveInside(root: string, rel: string): string {
  if (path.isAbsolute(rel) || path.win32.isAbsolute(rel) || rel.startsWith("/")) throw new PathError(rel);
  const abs = path.resolve(root, rel);
  if (!isInside(root, abs)) throw new PathError(rel);
  return abs;
}
