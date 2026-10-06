(function () {
  "use strict";

  const script = document.currentScript;
  const chatbotId = script?.dataset.chatbotId;
  if (!chatbotId || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(chatbotId)) {
    console.error("BIDACHAT: se requiere un identificador válido de chatbot.");
    return;
  }
  const fontUrl = new URL("/fonts/inter-variable.woff2", script.src).href;
  const apiBase = script.dataset.apiBase || new URL("/api/v1", script.src).href;
  const accent = /^#[0-9a-f]{6}$/i.test(script.dataset.primaryColor || "")
    ? script.dataset.primaryColor : "#14a8ce";
  const title = (script.dataset.title || "BIDACHAT").slice(0, 200);
  const welcome = (script.dataset.welcomeMessage || "¿En qué puedo ayudarte?").slice(0, 300);
  const icon = ["bot", "chat", "chart", "book", "sparkles", "headset"].includes(script.dataset.icon) ? script.dataset.icon : "bot";
  const IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"];
  const MAX_IMAGE_BYTES = 4 * 1024 * 1024;
  const symbols = {
    bot: '<rect x="5" y="7" width="14" height="12" rx="3"/><path d="M12 4v3M9 12h.01M15 12h.01M9 16h6"/>',
    chat: '<path d="M4 5h16v12H8l-4 3V5Z"/><path d="M8 9h8M8 13h5"/>',
    chart: '<path d="M4 19h16M6 16v-4M12 16V8M18 16V5"/>',
    book: '<path d="M12 5v15M12 5C9 3 6 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1Z"/>',
    sparkles: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3ZM20 2v4M18 4h4"/>',
    headset: '<path d="M4 13v-2a8 8 0 0 1 16 0v6a4 4 0 0 1-4 4h-4"/><rect x="3" y="11" width="4" height="7" rx="2"/><rect x="17" y="11" width="4" height="7" rx="2"/>',
    close: '<path d="M6 6l12 12M18 6 6 18"/>',
    attach: '<path d="m8 12.5 5.7-5.7a3 3 0 0 1 4.2 4.2l-7.8 7.8a5 5 0 0 1-7.1-7.1l8-8"/>',
    capture: '<path d="M4 7h3l1.5-2h7L17 7h3v12H4V7Z"/><circle cx="12" cy="13" r="3"/>',
    send: '<path d="m3 20 18-8L3 4l2.5 8L3 20Z"/><path d="M5.5 12H21"/>',
  };
  const svg = (name) => `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${symbols[name]}</svg>`;
  const visualPreview = script.dataset.preview === "true";
  const host = document.createElement("bidachat-widget");
  host.dataset.chatbotId = chatbotId;
  host.dataset.theme = script.dataset.theme === "dark" ? "dark" : "light";
  host.dataset.preview = String(visualPreview);
  host.style.setProperty("--widget-accent", accent);
  const channels = [1, 3, 5].map((index) => parseInt(accent.slice(index, index + 2), 16) / 255);
  const luminance = channels
    .map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
    .reduce((total, value, index) => total + value * [0.2126, 0.7152, 0.0722][index], 0);
  host.style.setProperty("--widget-on-accent", luminance > 0.18 ? "#08111f" : "#ffffff");

  const shadow = host.attachShadow({ mode: "open" });
  shadow.innerHTML = `
    <style>
      @font-face {font-family:"BIDACHAT Inter";src:url("${fontUrl}") format("woff2");font-weight:100 900;font-display:swap;}
      :host { all: initial; --w-text:#163247;--w-muted:#526a7e;--w-border:#d5e2eb;--w-surface:#fff;--w-canvas:#f5f8fb;--w-subtle:#e7f6fa;--w-link:#086e89;--w-danger:#b02c38;--w-danger-bg:#fff0f1; position: fixed; right: 24px; bottom: 24px; z-index: 2147483000; font: 14px/1.45 "BIDACHAT Inter", ui-sans-serif, system-ui, sans-serif; color: var(--w-text); }
      *, *::before, *::after { box-sizing: border-box; }
      button, input { font: inherit; }
      button { cursor: pointer; }
      button:focus-visible, input:focus-visible { outline: 2px solid var(--w-link); outline-offset: 2px; }
      svg { width: 18px; height: 18px; flex: none; }
      .launcher { display: flex; align-items: center; gap: 10px; min-height: 48px; max-width: min(340px, calc(100vw - 32px)); padding: 10px 16px; border: 0; border-radius: 12px; background: var(--widget-accent); color: var(--widget-on-accent); font-weight: 700; box-shadow: 0 10px 28px rgb(16 51 70 / .2); }
      .launcher span { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
      .launcher[hidden], .panel[hidden], .attachment-preview[hidden], .status[hidden] { display: none; }
      .panel { display: flex; flex-direction: column; width: min(420px, calc(100vw - 32px)); height: min(640px, calc(100dvh - 48px)); overflow: hidden; border: 1px solid var(--w-border); border-radius: 16px; background: var(--w-surface); box-shadow: 0 20px 45px rgb(20 62 83 / .18), 0 3px 10px rgb(18 52 72 / .06); }
      .header { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 68px; padding: 12px 16px; border-bottom: 1px solid var(--w-border); background: var(--w-surface); }
      .identity { display: flex; align-items: center; gap: 10px; min-width: 0; }
      .avatar { display: grid; place-items: center; width: 40px; height: 40px; flex: none; border: 1px solid var(--w-border); border-radius: 11px; background: var(--w-subtle); color: var(--w-link); }
      .identity-copy { min-width: 0; }
      .identity strong { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; line-height: 1.3; color: var(--w-text); }
      .identity small { display: block; margin-top: 2px; color: var(--w-muted); font-size: 11px; }
      .close { display: grid; place-items: center; width: 32px; height: 32px; flex: none; border: 0; border-radius: 8px; background: transparent; color: var(--w-muted); }
      .close:hover { background: var(--w-canvas); color: var(--w-text); }
      .messages { display: flex; flex: 1; flex-direction: column; gap: 12px; min-height: 0; overflow-y: auto; padding: 18px 16px; background: var(--w-canvas); scrollbar-color: #c7d9e2 transparent; scrollbar-width: thin; }
      .message-row { display: flex; align-items: flex-start; gap: 8px; max-width: 100%; }
      .message-row-user { justify-content: flex-end; }
      .message-avatar { display: grid; place-items: center; width: 25px; height: 25px; flex: none; margin-top: 2px; border-radius: 7px; background: var(--widget-accent); color: var(--widget-on-accent); font-size: 10px; font-weight: 800; }
      .message { max-width: 88%; margin: 0; padding: 10px 12px; border: 1px solid var(--w-border); border-radius: 13px 13px 13px 3px; background: var(--w-surface); color: var(--w-text); white-space: pre-wrap; overflow-wrap: anywhere; box-shadow: 0 2px 6px rgb(22 52 71 / .035); }
      .message-user { border-color: transparent; border-radius: 13px 13px 3px 13px; background: var(--widget-accent); color: var(--widget-on-accent); }
      .message img { display: block; max-width: 190px; max-height: 145px; margin-bottom: 8px; border-radius: 7px; object-fit: contain; }
      .feedback { align-self: flex-start; max-width: 95%; padding: 9px 11px; border: 1px solid #d5e9ef; border-radius: 9px; background: #eef8fb; color: #24586c; font-size: 12px; }
      .feedback-error { border-color: var(--w-border); background: var(--w-danger-bg); color: var(--w-danger); }
      .footer { display: grid; gap: 9px; padding: 12px; border-top: 1px solid var(--w-border); background: var(--w-surface); }
      .attachment-preview { display: flex; align-items: center; gap: 9px; min-width: 0; padding: 6px 8px; border: 1px solid var(--w-border); border-radius: 9px; background: var(--w-canvas); }
      .attachment-preview img { width: 32px; height: 32px; flex: none; border-radius: 6px; object-fit: cover; }
      .attachment-info { min-width: 0; flex: 1; }
      .attachment-info strong { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12px; font-weight: 600; }
      .attachment-info small { display: block; color: var(--w-muted); font-size: 11px; }
      .remove-attachment { display: grid; place-items: center; width: 28px; height: 28px; border: 0; border-radius: 6px; background: transparent; color: var(--w-muted); }
      .remove-attachment:hover { background: var(--w-canvas); color: var(--w-danger); }
      .composer { display: flex; align-items: center; gap: 6px; min-width: 0; }
      .action { display: flex; align-items: center; justify-content: center; width: 40px; min-height: 40px; flex: none; padding: 0; border: 1px solid var(--w-border); border-radius: 10px; background: var(--w-surface); color: var(--w-muted); }
      .action span { display: none; }
      .action:hover { border-color: var(--widget-accent); background: var(--w-subtle); color: var(--w-link); }
      .question { width: 100%; min-width: 0; height: 40px; flex: 1; padding: 0 11px; border: 1px solid var(--w-border); border-radius: 10px; background: var(--w-canvas); color: var(--w-text); font-size: 13px; }
      .question::placeholder { color: var(--w-muted); opacity: 1; }
      .question:focus { background: var(--w-surface); }
      .send { display: flex; align-items: center; justify-content: center; gap: 5px; min-height: 40px; flex: none; padding: 0 12px; border: 0; border-radius: 10px; background: var(--widget-accent); color: var(--widget-on-accent); font-size: 12px; font-weight: 700; }
      .send:hover { filter: brightness(.94); }
      .composer :disabled { cursor: not-allowed; opacity: .6; }
      .file-input { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }
      .hint { margin: 0 2px; color: var(--w-muted); font-size: 11px; }
      .status { margin: 0 2px; color: var(--w-danger); font-size: 12px; }
      @media (max-width: 480px) { :host { right: 12px; bottom: 12px; } .panel { width: calc(100vw - 24px); height: min(640px, calc(100dvh - 24px)); } .header { padding-inline: 12px; } .messages { padding-inline: 12px; } }
      @media (max-width: 350px) { .send span { display: none; } .send { width: 40px; padding: 0; } }

:host([data-theme="dark"]){color-scheme:dark;--w-text:#eef5fb;--w-muted:#a6bdce;--w-border:#2b465a;--w-surface:#102332;--w-canvas:#091521;--w-subtle:#153a48;--w-link:#76d8ea;--w-danger:#ffadb6;--w-danger-bg:#422832}
:host([data-preview="true"]){position:relative;display:block;inset:auto;z-index:auto;width:100%;height:100%}:host([data-preview="true"]) .panel{width:100%;height:100%;border:0;border-radius:0;box-shadow:none}:host([data-preview="true"]) .close{display:none}.messages:focus-visible{outline:2px solid var(--widget-accent);outline-offset:-4px}
    </style>
    <section class="panel" id="bidachat-panel" role="dialog" aria-label="Asistente BIDACHAT" hidden>
      <header class="header">
        <div class="identity"><span class="avatar">${svg(icon)}</span><span class="identity-copy"><strong></strong><small>Asistente del dashboard</small></span></div>
        <button class="close" type="button" aria-label="Cerrar asistente" title="Cerrar asistente">${svg("close")}</button>
      </header>
      <div class="messages" role="log" aria-label="Conversación" aria-live="polite" tabindex="0"></div>
      <div class="footer">
        <div class="attachment-preview" hidden><span class="attachment-info"><strong></strong><small></small></span><button class="remove-attachment" type="button" aria-label="Quitar imagen adjunta" title="Quitar imagen">${svg("close")}</button></div>
        <form class="composer">
          <button class="action attach" type="button" aria-label="Adjuntar imagen" title="Adjuntar imagen">${svg("attach")}<span>Adjuntar</span></button>
          <button class="action capture" type="button" aria-label="Capturar pantalla" title="Capturar pantalla">${svg("capture")}<span>Capturar</span></button>
          <input class="question" type="text" aria-label="Pregunta" placeholder="Escribe una pregunta…" maxlength="4000" required>
          <button class="send" type="submit" title="Enviar consulta" aria-label="Enviar consulta"><span>Enviar</span>${svg("send")}</button>
        </form>
        <input class="file-input" type="file" accept="image/png,image/jpeg,image/webp" aria-label="Seleccionar imagen">
        <p class="status" role="status" hidden></p>
        <p class="hint">Adjunta, pega con Ctrl+V o captura una imagen · Máximo 4 MB.</p>
      </div>
    </section>
    <button class="launcher" type="button" aria-controls="bidachat-panel" aria-expanded="false" aria-label="Abrir asistente BIDACHAT">${svg(icon)}<span></span></button>
  `;

  const panel = shadow.querySelector(".panel");
  const launcher = shadow.querySelector(".launcher");
  const messages = shadow.querySelector(".messages");
  const form = shadow.querySelector(".composer");
  const questionInput = shadow.querySelector(".question");
  const fileInput = shadow.querySelector(".file-input");
  const preview = shadow.querySelector(".attachment-preview");
  const status = shadow.querySelector(".status");
  let attachment = null;
  let attachmentUrl = null;
  let sending = false;
  shadow.querySelector(".identity strong").textContent = title;
  launcher.querySelector("span").textContent = title;

  function setOpen(open) {
    panel.hidden = !open;
    launcher.hidden = open;
    launcher.setAttribute("aria-expanded", String(open));
    (open ? questionInput : launcher).focus();
  }

  function setStatus(message) {
    status.textContent = message;
    status.hidden = !message;
  }

  function addMessage(content, kind, imageFile = null) {
    const row = document.createElement("div");
    row.className = `message-row message-row-${kind}`;
    if (kind === "assistant") {
      const avatar = document.createElement("span");
      avatar.className = "message-avatar";
      avatar.textContent = "AI";
      row.appendChild(avatar);
    }
    const bubble = document.createElement("div");
    bubble.className = `message message-${kind}`;
    if (imageFile) {
      const image = document.createElement("img");
      const messageImageUrl = URL.createObjectURL(imageFile);
      image.src = messageImageUrl;
      image.onload = () => URL.revokeObjectURL(messageImageUrl);
      image.onerror = () => URL.revokeObjectURL(messageImageUrl);
      image.alt = "Imagen enviada";
      bubble.appendChild(image);
    }
    const text = document.createElement("span");
    text.textContent = content;
    bubble.appendChild(text);
    row.appendChild(bubble);
    messages.appendChild(row);
    messages.scrollTop = messages.scrollHeight;
    return row;
  }

  function clearAttachment() {
    attachment = null;
    fileInput.value = "";
    if (attachmentUrl) URL.revokeObjectURL(attachmentUrl);
    attachmentUrl = null;
    preview.querySelector("img")?.remove();
    preview.hidden = true;
  }

  function setAttachment(file) {
    if (!IMAGE_TYPES.includes(file.type) || !file.size || file.size > MAX_IMAGE_BYTES) {
      clearAttachment();
      setStatus("Usa una imagen PNG, JPEG o WebP de hasta 4 MB.");
      return;
    }
    clearAttachment();
    attachment = file;
    attachmentUrl = URL.createObjectURL(file);
    const thumbnail = document.createElement("img");
    thumbnail.src = attachmentUrl;
    thumbnail.alt = "Imagen adjunta";
    preview.prepend(thumbnail);
    preview.querySelector("strong").textContent = file.name;
    preview.querySelector("small").textContent = `${Math.max(1, Math.round(file.size / 1024))} KB`;
    preview.hidden = false;
    setStatus("");
  }

  async function captureScreen() {
    if (!navigator.mediaDevices?.getDisplayMedia) {
      setStatus("Este navegador no permite capturas. Usa Adjuntar para cargar una imagen.");
      return;
    }
    let stream;
    const video = document.createElement("video");
    try {
      stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      video.srcObject = stream;
      video.muted = true;
      await video.play();
      if (!video.videoWidth || !video.videoHeight) throw new Error("No se recibió la imagen de pantalla.");
      const scale = Math.min(1, 1800 / Math.max(video.videoWidth, video.videoHeight));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      host.style.visibility = "hidden";
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.82));
      if (!blob) throw new Error("No se pudo crear la captura.");
      setAttachment(new File([blob], "captura-dashboard.jpg", { type: "image/jpeg" }));
    } catch (error) {
      if (error?.name !== "NotAllowedError") {
        setStatus("No se pudo capturar. Prueba con otra pestaña o usa Adjuntar.");
      }
    } finally {
      host.style.visibility = "";
      stream?.getTracks().forEach((track) => track.stop());
      video.srcObject = null;
    }
  }

  function readImage(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result).split(",")[1]);
      reader.onerror = () => reject(new Error("No se pudo leer la imagen."));
      reader.readAsDataURL(file);
    });
  }

  shadow.querySelector(".close").addEventListener("click", () => setOpen(false));
  launcher.addEventListener("click", () => setOpen(true));
  shadow.querySelector(".attach").addEventListener("click", () => fileInput.click());
  shadow.querySelector(".capture").addEventListener("click", captureScreen);
  shadow.querySelector(".remove-attachment").addEventListener("click", clearAttachment);
  fileInput.addEventListener("change", () => {
    if (fileInput.files?.[0]) setAttachment(fileInput.files[0]);
  });
  questionInput.addEventListener("paste", (event) => {
    const image = Array.from(event.clipboardData?.items ?? [])
      .find((item) => item.kind === "file" && IMAGE_TYPES.includes(item.type))
      ?.getAsFile();
    if (!image) return;
    event.preventDefault();
    const extension = image.type === "image/jpeg" ? "jpg" : image.type.split("/")[1];
    setAttachment(new File([image], `imagen-pegada.${extension}`, { type: image.type }));
  });
  shadow.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) setOpen(false);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = questionInput.value.trim();
    if (!question || sending || visualPreview) return;
    const image = attachment;
    const submittedMessage = addMessage(question, "user", image);
    questionInput.value = "";
    sending = true;
    panel.setAttribute("aria-busy", "true");
    shadow.querySelector(".remove-attachment").disabled = true;
    for (const control of form.elements) control.disabled = true;
    fileInput.disabled = true;
    setStatus("");
    const feedback = document.createElement("div");
    feedback.className = "feedback";
    feedback.setAttribute("role", "status");
    feedback.textContent = "Procesando consulta…";
    messages.appendChild(feedback);
    messages.scrollTop = messages.scrollHeight;
    try {
      const payload = { question };
      if (image) {
        payload.image_base64 = await readImage(image);
        payload.image_mime_type = image.type;
      }
      const response = await fetch(`${apiBase.replace(/\/$/, "")}/chatbots/${chatbotId}/queries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const failure = await response.json().catch(() => null);
        throw new Error(typeof failure?.detail === "string" ? failure.detail : `Error ${response.status}`);
      }
      const result = await response.json();
      feedback.remove();
      addMessage(result.answer, "assistant");
      if (attachment === image) clearAttachment();
    } catch (error) {
      submittedMessage.remove();
      feedback.classList.add("feedback-error");
      const message = error instanceof TypeError || error instanceof SyntaxError ? "Revisa la conexión y que este sitio esté autorizado para usar el chatbot." : error instanceof Error ? error.message : "Inténtalo nuevamente.";
      feedback.textContent = `No se pudo obtener una respuesta. ${message}`;
      questionInput.value = question;
    } finally {
      sending = false;
      panel.removeAttribute("aria-busy");
      shadow.querySelector(".remove-attachment").disabled = false;
      for (const control of form.elements) control.disabled = false;
      fileInput.disabled = false;
      questionInput.focus();
    }
  });

  addMessage(welcome, "assistant");
  if (visualPreview) { panel.hidden=false; launcher.hidden=true; for (const control of form.elements) control.disabled=true; fileInput.disabled=true; shadow.querySelector(".hint").textContent="Vista de apariencia · La conversación se prueba en Publicación."; }
  if (document.body) document.body.appendChild(host);
  else document.addEventListener("DOMContentLoaded", () => document.body.appendChild(host), { once: true });
})();
