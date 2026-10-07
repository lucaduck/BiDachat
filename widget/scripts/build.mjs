import { copyFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const source = fileURLToPath(new URL("../src/bidachat-widget.js", import.meta.url));
const directory = fileURLToPath(new URL("../dist/", import.meta.url));
const destination = fileURLToPath(new URL("../dist/bidachat-widget.js", import.meta.url));

await mkdir(directory, { recursive: true });
await copyFile(source, destination);
