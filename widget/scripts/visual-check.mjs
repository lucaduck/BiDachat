import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const edgePath = process.env.BROWSER_PATH ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const artifactDirectory = fileURLToPath(new URL("../dist/", import.meta.url));
const exampleUrl = new URL("../example/dashboard.html", import.meta.url).href;
const port = 9248;

await mkdir(artifactDirectory, { recursive: true });
const browser = spawn(edgePath, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${fileURLToPath(new URL("../dist/edge-profile-visual/", import.meta.url))}`,
  "about:blank",
], { windowsHide: true, stdio: "ignore" });

async function waitForTarget() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`);
      const targets = await response.json();
      const target = targets.find((item) => item.type === "page");
      if (target) return target.webSocketDebuggerUrl;
    } catch { /* Browser startup is still in progress. */ }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error("Edge did not expose a page target.");
}

function connect(url) {
  const socket = new WebSocket(url);
  const pending = new Map();
  const events = new Map();
  let nextId = 1;
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id) {
      const promise = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) promise.reject(new Error(message.error.message));
      else promise.resolve(message.result);
    } else if (events.has(message.method)) {
      events.get(message.method)(message.params);
      events.delete(message.method);
    }
  };
  return {
    ready: new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; }),
    send(method, params = {}) {
      const id = nextId++;
      socket.send(JSON.stringify({ id, method, params }));
      return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
    },
    once(method) { return new Promise((resolve) => events.set(method, resolve)); },
    close() { socket.close(); },
  };
}

try {
  const client = connect(await waitForTarget());
  await client.ready;
  await client.send("Page.enable");
  await client.send("Runtime.enable");

  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    await client.send("Emulation.setDeviceMetricsOverride", { ...viewport, screenWidth: viewport.width, screenHeight: viewport.height, deviceScaleFactor: 1, mobile: viewport.width < 500 });
    const loaded = client.once("Page.loadEventFired");
    await client.send("Page.navigate", { url: exampleUrl });
    await loaded;
    const check = await client.send("Runtime.evaluate", { expression: `(() => { const widget = document.querySelector('bidachat-widget'); if (!widget) return null; const launcher = widget.shadowRoot.querySelector('.launcher'); return { hostColor: getComputedStyle(document.querySelector('#dashboard-filter')).backgroundColor, widgetColor: getComputedStyle(launcher).backgroundColor, width: innerWidth }; })()`, returnByValue: true });
    const values = check.result.value;
    if (!values || values.width !== viewport.width || values.hostColor !== "rgb(36, 89, 164)" || values.widgetColor !== "rgb(20, 168, 206)") throw new Error(`Widget isolation failed at ${viewport.width}px: ${JSON.stringify(values)}`);
    await client.send("Runtime.evaluate", { expression: "document.querySelector('bidachat-widget').shadowRoot.querySelector('.launcher').click()" });
    const screenshot = await client.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    await writeFile(fileURLToPath(new URL(`../dist/widget-open-${viewport.width}.png`, import.meta.url)), Buffer.from(screenshot.data, "base64"));
    process.stdout.write(`Widget visual check passed at ${viewport.width}px.\n`);
  }
  client.close();
} finally {
  browser.kill();
}
