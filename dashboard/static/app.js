/**
 * Agent-Earns dashboard SPA
 */

const PAGE_TITLES = {
  overview: "Overview",
  leads: "Leads",
  upload: "Upload & Run",
  campaigns: "Campaigns",
  replies: "Replies",
  instantly: "Instantly",
  settings: "Settings",
};

const THEMES = ["arctic", "light", "warm", "dark"];
const THEME_KEY = "ae-theme";

let uploadedFilename = null;
let pollTimer = null;

function applyTheme(name) {
  if (!THEMES.includes(name)) name = "arctic";
  document.documentElement.setAttribute("data-theme", name);
  localStorage.setItem(THEME_KEY, name);
  document.querySelectorAll(".theme-option").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.theme === name);
  });
  const swatch = document.getElementById("themeSwatch");
  if (swatch) swatch.className = `theme-swatch theme-dot ${name}`;
}

function setupTheme() {
  const saved = localStorage.getItem(THEME_KEY) || "arctic";
  applyTheme(saved);

  const btn = document.getElementById("themeBtn");
  const menu = document.getElementById("themeMenu");

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isClosed = menu.classList.toggle("hidden");
    btn.setAttribute("aria-expanded", isClosed ? "false" : "true");
  });

  document.querySelectorAll(".theme-option").forEach((opt) => {
    opt.addEventListener("click", () => {
      applyTheme(opt.dataset.theme);
      menu.classList.add("hidden");
      btn.setAttribute("aria-expanded", "false");
      toast(`Theme: ${opt.textContent.trim()}`);
    });
  });

  document.addEventListener("click", () => {
    menu.classList.add("hidden");
    btn.setAttribute("aria-expanded", "false");
  });
  menu.addEventListener("click", (e) => e.stopPropagation());
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (res.status === 401) {
    toast("Session expired — refresh and log in again", "error");
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById("toasts").appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function setStatus(text) {
  document.getElementById("statusPill").textContent = text;
}

function navigate(page) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  document.getElementById(`page-${page}`)?.classList.add("active");
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add("active");
  document.getElementById("pageTitle").textContent = PAGE_TITLES[page] || page;
  document.getElementById("sidebar").classList.remove("open");

  const loaders = {
    overview: loadOverview,
    leads: loadLeads,
    campaigns: loadCampaigns,
    replies: loadReplies,
    settings: loadSettings,
  };
  loaders[page]?.();
}

async function loadAutopilotStatus() {
  try {
    const st = await api("/api/autopilot/status");
    document.getElementById("autopilotNext").textContent = st.next_hunt || st.message || "—";
    const markets = document.getElementById("autopilotMarkets");
    if (markets) {
      markets.textContent = st.markets_in_rotation
        ? `${st.markets_in_rotation} markets in rotation · Maps ${st.google_maps_ready ? "ON" : "needs API key"}`
        : "";
    }
    if (st.last_action) {
      document.getElementById("autopilotMessage").textContent =
        `Last: ${st.last_action.replace(/_/g, " ")} · ${st.last_run ? new Date(st.last_run).toLocaleString() : ""}`;
    }
  } catch (_) {}
}

async function loadOverview() {
  loadAutopilotStatus();
  const data = await api("/api/overview");
  const { stats, integrations } = data;

  const grid = document.getElementById("statGrid");
  const cards = [
    ["Total leads", stats.total],
    ["Contacted", stats.contacted],
    ["Replied", stats.replied],
    ["Draft ready", stats.draft_ready],
  ];
  grid.innerHTML = cards
    .map(
      ([label, val], i) => `
    <div class="stat-card" style="animation-delay:${i * 0.06}s">
      <b>${val}</b><span>${label}</span>
    </div>`
    )
    .join("");

  const names = {
    instantly: "Instantly",
    telegram: "Telegram",
    google_maps: "Google Maps",
    hunter: "Hunter.io",
    netlify: "Netlify demos",
  };
  document.getElementById("integrationRow").innerHTML = Object.entries(integrations)
    .map(([k, on]) => `<span class="badge ${on ? "on" : ""}">${names[k] || k}</span>`)
    .join("");
}

async function loadLeads() {
  const status = document.getElementById("leadStatusFilter").value;
  const q = document.getElementById("leadSearch").value.trim();
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (q) params.set("q", q);
  const data = await api(`/api/leads?${params}`);
  const tbody = document.getElementById("leadsTable");
  if (!data.items.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="muted">No leads found</td></tr>';
    return;
  }
  tbody.innerHTML = data.items
    .map(
      (l) => `
    <tr>
      <td><strong>${esc(l.business_name)}</strong></td>
      <td>${esc(l.email || "—")}</td>
      <td><span class="tag ${esc(l.status)}">${esc(l.status)}</span>
        ${l.reply_classification ? `<span class="tag interested">${esc(l.reply_classification)}</span>` : ""}</td>
      <td>${esc(l.niche || "")}</td>
      <td>${esc(l.location || "")}</td>
    </tr>`
    )
    .join("");
}

async function loadCampaigns() {
  const data = await api("/api/campaigns");
  const tbody = document.getElementById("campaignsTable");
  if (!data.items.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="muted">No campaigns yet</td></tr>';
    return;
  }
  tbody.innerHTML = data.items
    .map(
      (r) => `
    <tr>
      <td><code>${esc(r.id.slice(0, 8))}…</code></td>
      <td>${esc(r.niche)} @ ${esc(r.city)}</td>
      <td>${r.leads_processed}/${r.leads_requested}</td>
      <td>${r.emails_sent}</td>
      <td><span class="tag">${esc(r.status)}</span></td>
    </tr>`
    )
    .join("");
}

async function loadReplies() {
  const data = await api("/api/replies");
  const list = document.getElementById("replyList");
  if (!data.items.length) {
    list.innerHTML = '<p class="muted card">No replies yet. Run Sync replies after leads respond.</p>';
    return;
  }
  list.innerHTML = data.items
    .map(
      (l, i) => `
    <div class="reply-card" style="animation-delay:${i * 0.05}s">
      <h4>${esc(l.business_name)} · ${esc(l.email || "")}</h4>
      <p>${esc(l.reply_snippet || "Reply recorded")}</p>
      <span class="tag ${esc(l.reply_classification || l.status)}">${esc(l.reply_classification || l.status)}</span>
    </div>`
    )
    .join("");
}

async function loadSettings() {
  const data = await api("/api/settings");
  const p = data.prefs;
  document.getElementById("sName").value = p.your_name || "";
  document.getElementById("sDemoUrl").value = p.demo_site_base_url || data.env.demo_site_base_url || "";
  document.getElementById("sLeads").value = p.leads_per_run || 10;
  document.getElementById("sDailyLimit").value = p.instantly_daily_limit || 20;
  document.getElementById("sReplyMin").value = p.reply_sync_interval_minutes || 15;

  const env = data.env;
  document.getElementById("envList").innerHTML = `
    <div class="env-row"><span>Send mode</span><span>${esc(env.email_send_mode)}</span></div>
    <div class="env-row"><span>Instantly</span><span>${env.instantly_configured ? "Connected" : "Not set"}</span></div>
    <div class="env-row"><span>Campaign ID</span><span>${esc(env.instantly_campaign_id)}</span></div>
    <div class="env-row"><span>Telegram</span><span>${env.telegram_configured ? "On" : "Off"}</span></div>
    <div class="env-row"><span>Max emails/day</span><span>${env.max_emails_per_day}</span></div>
  `;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s ?? "";
  return d.innerHTML;
}

async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  setStatus("Uploading…");
  const data = await api("/api/upload", { method: "POST", body: fd });
  uploadedFilename = data.filename;
  document.getElementById("uploadMeta").textContent =
    `${data.filename} · ${data.rows} rows · columns: ${(data.headers || []).slice(0, 5).join(", ")}`;
  toast(`Queued ${data.rows} leads — agent will pick niche/city from file`);
  setStatus("Ready");
  if (document.getElementById("autoRunAfterUpload")?.checked) {
    await runAutopilotJob();
  }
}

async function runAutopilotJob() {
  const panel = document.getElementById("jobPanel");
  panel.classList.remove("hidden");
  document.getElementById("jobStatus").textContent = "Agent working…";
  setStatus("Autopilot…");
  try {
    const r = await api("/api/autopilot/run", { method: "POST" });
    document.getElementById("jobStatus").textContent = `${r.action}: ${r.detail}`;
    document.getElementById("jobLog").textContent = JSON.stringify(r, null, 2);
    toast(r.detail || "Done");
    loadAutopilotStatus();
    loadOverview();
  } catch (e) {
    document.getElementById("jobStatus").textContent = e.message;
    toast(e.message, "error");
  }
  setStatus("Ready");
}

function setupUpload() {
  const dropzone = document.getElementById("dropzone");
  const input = document.getElementById("csvFile");

  document.getElementById("pickFile").onclick = () => input.click();
  dropzone.onclick = () => input.click();

  input.onchange = () => {
    if (input.files[0]) uploadFile(input.files[0]);
  };

  dropzone.ondragover = (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  };
  dropzone.ondragleave = () => dropzone.classList.remove("dragover");
  dropzone.ondrop = (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const f = e.dataTransfer.files[0];
    if (f) uploadFile(f);
  };

}

document.getElementById("btnRunAutopilot")?.addEventListener("click", runAutopilotJob);

async function pollJob(jobId) {
  clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const job = await api(`/api/campaign/job/${jobId}`);
      document.getElementById("jobStatus").textContent = `${job.status}: ${job.message}`;
      if (job.result?.summary) {
        document.getElementById("jobLog").textContent = job.result.summary;
      }
      if (job.status === "completed") {
        clearInterval(pollTimer);
        setStatus("Ready");
        toast("Campaign completed");
        loadOverview();
      }
      if (job.status === "failed") {
        clearInterval(pollTimer);
        setStatus("Error");
        toast(job.message, "error");
      }
    } catch (err) {
      clearInterval(pollTimer);
    }
  }, 2000);
}

function setupNav() {
  document.querySelectorAll(".nav-item[data-page]").forEach((btn) => {
    btn.addEventListener("click", () => navigate(btn.dataset.page));
  });
  document.getElementById("menuToggle").onclick = () => {
    document.getElementById("sidebar").classList.toggle("open");
  };
}

document.getElementById("btnSyncReplies").onclick = async () => {
  setStatus("Syncing…");
  try {
    const r = await api("/api/reply-sync", { method: "POST" });
    toast(`Sync done — ${r.new_replies} new, ${r.interested} hot`);
    loadOverview();
  } catch (e) {
    toast(e.message, "error");
  }
  setStatus("Ready");
};

document.getElementById("btnConfigureInstantly").onclick = async () => {
  setStatus("Configuring…");
  try {
    const r = await api("/api/instantly/configure", { method: "POST" });
    toast(r.ok ? `Instantly updated (${r.daily_limit}/day)` : "Configure failed", r.ok ? "success" : "error");
  } catch (e) {
    toast(e.message, "error");
  }
  setStatus("Ready");
};

document.getElementById("settingsForm").onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    your_name: document.getElementById("sName").value,
    demo_site_base_url: document.getElementById("sDemoUrl").value,
    leads_per_run: parseInt(document.getElementById("sLeads").value, 10),
    instantly_daily_limit: parseInt(document.getElementById("sDailyLimit").value, 10),
    reply_sync_interval_minutes: parseInt(document.getElementById("sReplyMin").value, 10),
  };
  await api("/api/settings", { method: "POST", body: JSON.stringify(body) });
  toast("Settings saved");
};

document.getElementById("leadSearch").addEventListener(
  "input",
  debounce(() => loadLeads(), 300)
);
document.getElementById("leadStatusFilter").addEventListener("change", loadLeads);

function debounce(fn, ms) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

setupTheme();
setupNav();
setupUpload();
loadSettings().then(() => navigate("overview"));
