import path from "node:path";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  root: "app",
  plugins: [viteSingleFile()],
  build: {
    outDir: path.resolve("build/app"),
    emptyOutDir: true,
    cssMinify: true,
    minify: true,
    rollupOptions: {
      input: path.resolve("app/app.html"),
    },
  },
});
