import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const publicDirectory = fileURLToPath(new URL("../public/", import.meta.url));
const widgetSource = fileURLToPath(
  new URL("../../widget/src/bidachat-widget.js", import.meta.url),
);
const exampleSource = fileURLToPath(
  new URL("../../widget/example/dashboard.html", import.meta.url),
);
await mkdir(publicDirectory, { recursive: true });
await copyFile(
  widgetSource,
  fileURLToPath(new URL("../public/bidachat-widget.js", import.meta.url)),
);
const example = (await readFile(exampleSource, "utf8")).replace(
  "../dist/bidachat-widget.js",
  "/bidachat-widget.js",
);
await writeFile(
  fileURLToPath(new URL("../public/widget-example.html", import.meta.url)),
  example,
);
