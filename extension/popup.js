const $ = id => document.getElementById(id);
const send = msg => chrome.runtime.sendMessage(msg);

function esc(s) {
  return String(s || "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function show(text, cls) {
  $("msg").textContent = text;
  $("msg").className = cls || "";
}

async function refreshStatus() {
  const st = await send({ type: "status" });
  const ok = st && st.ts && st.bot;
  $("dot").className = "dot " + (ok ? "ok" : "err");
  $("status").textContent = ok ? st.bot : (st && st.ts === false ? "TS kapalı" : "bağlantı yok");
  if (!ok && st && st.error) show(st.error, "err");
}

async function refreshTrack() {
  let t = null;
  try { t = await send({ type: "current" }); } catch (e) {}
  if (!t) {
    $("track").innerHTML = '<div class="artist">YouTube / Yandex Music\'te çalan şarkı yok</div>';
    $("play").disabled = true;
    return;
  }
  $("track").innerHTML =
    `<div class="src">${esc(t.source)}${t.playing ? " · çalıyor" : ""}</div>` +
    `<div class="title">${esc(t.title)}</div>` +
    (t.artist ? `<div class="artist">${esc(t.artist)}</div>` : "");
  $("play").disabled = false;
}

$("play").onclick = async () => {
  $("play").disabled = true;
  show("Gönderiliyor...");
  const r = await send({ type: "playCurrent" });
  show(r && r.ok ? "Gönderildi: " + r.link : (r && r.error) || "Hata", r && r.ok ? "ok" : "err");
  $("play").disabled = false;
};

$("stop").onclick = async () => {
  const r = await send({ type: "stop" });
  show(r && r.ok ? "Durduruldu" : (r && r.error) || "Hata", r && r.ok ? "ok" : "err");
};

$("auto").onchange = e => chrome.storage.local.set({ auto: e.target.checked });
chrome.storage.local.get("auto").then(v => { $("auto").checked = v.auto === true; });

refreshStatus();
refreshTrack();
