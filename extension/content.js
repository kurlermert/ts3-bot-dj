// Sayfada calan sarkiyi algilar; otomatik mod aciksa sarki degisince bota gonderir.
(() => {
  if (window.__ts3BotDj) return;
  window.__ts3BotDj = true;

  const host = location.hostname;
  const isYouTube = host.endsWith("youtube.com");

  function youtubeVideoId() {
    const u = new URL(location.href);
    if (u.searchParams.get("v")) return u.searchParams.get("v");
    const m = u.pathname.match(/^\/(?:shorts|live)\/([\w-]{11})/);
    return m ? m[1] : null;
  }

  function isAd() {
    return !!document.querySelector(".ad-showing, .ad-interrupting");
  }

  function isPlaying() {
    const ms = navigator.mediaSession && navigator.mediaSession.playbackState;
    if (ms === "playing") return true;
    if (ms === "paused") return false;
    return [...document.querySelectorAll("video, audio")].some(m => !m.paused && !m.ended);
  }

  function getTrack() {
    const md = navigator.mediaSession && navigator.mediaSession.metadata;
    const title = (md && md.title) || "";
    const artist = (md && md.artist) || "";
    if (isYouTube) {
      const id = youtubeVideoId();
      if (!id) return null;
      return {
        source: host.startsWith("music.") ? "YouTube Music" : "YouTube",
        url: "https://www.youtube.com/watch?v=" + id,
        title: title || document.title.replace(/ - YouTube( Music)?$/, ""),
        artist,
        playing: isPlaying() && !isAd()
      };
    }
    // Yandex Music: link bot tarafinda calmaz, sanatci + baslik ile YouTube'da aranir
    if (!title) return null;
    return {
      source: "Yandex Music",
      url: null,
      query: (artist ? artist + " - " : "") + title,
      title,
      artist,
      playing: isPlaying()
    };
  }

  chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
    if (msg && msg.type === "getTrack") reply(getTrack());
  });

  // Otomatik mod: sarki 3 sn boyunca degismeden caliyorsa gonder
  let sentKey = null, pendingKey = null, pendingSince = 0;
  setInterval(async () => {
    let auto = false;
    try { auto = (await chrome.storage.local.get("auto")).auto === true; } catch (e) { return; }
    if (!auto) { sentKey = null; return; }
    const t = getTrack();
    if (!t || !t.playing) return;
    const key = t.url || t.query;
    if (key === sentKey) return;
    if (key !== pendingKey) { pendingKey = key; pendingSince = Date.now(); return; }
    if (Date.now() - pendingSince < 3000) return;
    sentKey = key;
    chrome.runtime.sendMessage({ type: "play", track: t });
  }, 1000);
})();
