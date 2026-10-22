const BRIDGE = "http://127.0.0.1:8765";
const SITES = /^https?:\/\/([^/]*\.)?(youtube\.com|music\.yandex\.(ru|com|com\.tr|kz|by))\//;

async function bridge(path, body) {
  try {
    const r = await fetch(BRIDGE + path, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    return await r.json();
  } catch (e) {
    return { ok: false, error: "Kopru calismiyor (bridge.py'yi baslat)" };
  }
}

// Once ses cikaran destekli sekme, yoksa aktif sekme
async function findMusicTab() {
  const audible = (await chrome.tabs.query({ audible: true })).filter(t => SITES.test(t.url || ""));
  if (audible.length) return audible[0];
  const [active] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (active && SITES.test(active.url || "")) return active;
  const any = (await chrome.tabs.query({})).filter(t => SITES.test(t.url || ""));
  return any[0] || null;
}

async function getTrack() {
  const tab = await findMusicTab();
  if (!tab) return null;
  try {
    return await chrome.tabs.sendMessage(tab.id, { type: "getTrack" });
  } catch (e) {
    // Eklenti kurulmadan once acilmis sekme: content script'i simdi enjekte et
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    return await chrome.tabs.sendMessage(tab.id, { type: "getTrack" });
  }
}

function badge(ok) {
  chrome.action.setBadgeBackgroundColor({ color: ok ? "#16a34a" : "#dc2626" });
  chrome.action.setBadgeText({ text: ok ? "✓" : "!" });
  setTimeout(() => chrome.action.setBadgeText({ text: "" }), 2500);
}

async function play(track, force) {
  if (!track) { badge(false); return { ok: false, error: "Calan sarki bulunamadi" }; }
  const res = await bridge("/play", { url: track.url, query: track.query, title: track.title, force });
  if (!res.skipped) badge(res.ok);
  return res;
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  (async () => {
    if (msg.type === "play") return play(msg.track, false);
    if (msg.type === "playCurrent") return play(await getTrack(), true);
    if (msg.type === "current") return getTrack();
    if (msg.type === "status") return bridge("/status");
    if (msg.type === "stop") return bridge("/stop", {});
  })().then(reply, e => reply({ ok: false, error: String(e) }));
  return true;
});

chrome.commands.onCommand.addListener(async cmd => {
  if (cmd === "send-current") play(await getTrack(), true);
});
