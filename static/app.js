// LinkedIn Agent — frontend logic (SSE streaming + live markdown render)

const themeEl  = document.getElementById("theme");
const runBtn   = document.getElementById("run");
const shellEl  = document.getElementById("output-shell");
const outputEl = document.getElementById("output");
const statusEl = document.getElementById("status");
const copyBtn  = document.getElementById("copy");
const resetBtn = document.getElementById("reset");
const chips    = document.querySelectorAll(".chip");

let accumulated = "";  // running buffer of all text received so far
let running = false;   // guard against double-clicks

// gfm = GitHub-flavored markdown (tables, fenced code), breaks = treat \n as <br>
marked.setOptions({ gfm: true, breaks: true });

// Preset chips: clicking one fills the textarea
chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    themeEl.value = chip.dataset.theme;
    themeEl.focus();
  });
});

// Cmd/Ctrl + Enter to fire — common keyboard convention for "submit"
themeEl.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    run();
  }
});

runBtn.addEventListener("click", run);

copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(accumulated).then(() => {
    copyBtn.textContent = "COPIED ✓";
    setTimeout(() => (copyBtn.textContent = "COPY MARKDOWN"), 1400);
  });
});

resetBtn.addEventListener("click", () => {
  shellEl.hidden = true;
  outputEl.innerHTML = "";
  accumulated = "";
  themeEl.value = "";
  themeEl.focus();
});

async function run() {
  if (running) return;
  const theme = themeEl.value.trim();
  if (theme.length < 2) { themeEl.focus(); return; }

  // UI state: lock the button, show the output panel, reset state
  running = true;
  runBtn.disabled = true;
  runBtn.querySelector(".run-label").textContent = "RUNNING…";
  shellEl.hidden = false;
  outputEl.classList.add("streaming");
  outputEl.innerHTML = "";
  accumulated = "";
  statusEl.textContent = "STREAMING…";
  statusEl.classList.remove("done");
  shellEl.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || "Request failed");
    }

    // ReadableStream gives us chunks of bytes as they arrive over the network
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE format: events separated by "\n\n". Split, parse complete ones,
      // keep any incomplete tail for the next iteration.
      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const evt of events) {
        if (!evt.startsWith("data: ")) continue;
        const payload = evt.slice(6);
        let data;
        try { data = JSON.parse(payload); } catch { continue; }

        if (data.error) throw new Error(data.error);
        if (data.text) {
          accumulated += data.text;
          outputEl.innerHTML = marked.parse(accumulated);
        }
        if (data.done) finish();
      }
    }
    finish();
  } catch (err) {
    outputEl.innerHTML = `<p style="color: var(--accent)"><strong>Agent error.</strong> ${escapeHtml(err.message)}</p>`;
    statusEl.textContent = "ERROR";
    statusEl.classList.add("done");
    outputEl.classList.remove("streaming");
  } finally {
    running = false;
    runBtn.disabled = false;
    runBtn.querySelector(".run-label").textContent = "RUN AGENT";
  }
}

function finish() {
  outputEl.classList.remove("streaming");
  statusEl.textContent = "COMPLETE";
  statusEl.classList.add("done");
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}