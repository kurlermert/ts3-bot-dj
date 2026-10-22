# -*- coding: utf-8 -*-
"""TS3 Bot DJ koprusu.

Chrome eklentisinden gelen istegi alir, TS3 ClientQuery (127.0.0.1:25639)
uzerinden muzik botuna PM olarak "!play <link>" gonderir.
Sadece Python stdlib kullanir.
"""
import configparser
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
LOG_PATH = os.path.join(HERE, "bridge.log")

DEFAULT_CONFIG = {
    "port": 8765,
    "bot_name": "MuzikBot",       # nick icinde gecmesi yeterli (buyuk/kucuk harf duyarsiz)
    "play_command": "!play",
    "stop_command": "!stop",
    "clientquery_host": "127.0.0.1",
    "clientquery_port": 25639,
    "api_key": "",                # bos ise %APPDATA%\TS3Client\clientquery.ini'den okunur
    "dedupe_seconds": 8,
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            log("config.json okunamadi: %s" % e)
    else:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_api_key(cfg):
    if cfg.get("api_key"):
        return cfg["api_key"]
    ini = os.path.join(os.environ.get("APPDATA", ""), "TS3Client", "clientquery.ini")
    cp = configparser.ConfigParser()
    cp.read(ini, encoding="utf-8")
    return cp.get("General", "api_key", fallback="")


# ---------------------------------------------------------------- ClientQuery

def ts_escape(s):
    rep = [("\\", "\\\\"), ("/", "\\/"), (" ", "\\s"), ("|", "\\p"),
           ("\a", "\\a"), ("\b", "\\b"), ("\f", "\\f"), ("\n", "\\n"),
           ("\r", "\\r"), ("\t", "\\t"), ("\v", "\\v")]
    for a, b in rep:
        s = s.replace(a, b)
    return s


def ts_unescape(s):
    rep = {"\\\\": "\\", "\\/": "/", "\\s": " ", "\\p": "|", "\\n": "\n",
           "\\r": "\r", "\\t": "\t"}
    return re.sub(r"\\[\\/spnrt]", lambda m: rep[m.group(0)], s)


def parse_items(body):
    items = []
    for chunk in body.split("|"):
        d = {}
        for tok in chunk.split(" "):
            if "=" in tok:
                k, v = tok.split("=", 1)
                d[k] = ts_unescape(v)
            elif tok:
                d[tok] = ""
        items.append(d)
    return items


class ClientQuery:
    def __init__(self, host, port, api_key):
        self.sock = socket.create_connection((host, port), 4)
        self.buf = b""
        self._read_until_banner()
        if api_key:
            self.cmd("auth apikey=%s" % api_key)

    def _read_until_banner(self):
        # Banner: "TS3 Client\n\rWelcome ... \n\rselected schandlerid=1\n\r"
        deadline = time.time() + 3
        while b"schandlerid" not in self.buf and time.time() < deadline:
            self.buf += self.sock.recv(4096)
        self.buf = b""

    def cmd(self, line):
        self.sock.sendall((line + "\n").encode("utf-8"))
        data = b""
        deadline = time.time() + 5
        while time.time() < deadline:
            # Kopuk gelen "notify..." satirlari olabilir; error satirina kadar oku
            if re.search(rb"error id=\d+ msg=[^\n]*\n", data):
                break
            chunk = self.sock.recv(65536)
            if not chunk:
                break
            data += chunk
        text = data.decode("utf-8", "replace").replace("\r", "")
        lines = [l for l in text.split("\n") if l and not l.startswith("notify")]
        err = next((l for l in lines if l.startswith("error ")), "error id=-1 msg=timeout")
        m = re.search(r"id=(\d+) msg=(\S+)", err)
        code, msg = int(m.group(1)), ts_unescape(m.group(2))
        if code != 0:
            raise RuntimeError("TS3 hata %d: %s (%s)" % (code, msg, line.split(" ")[0]))
        body = "\n".join(l for l in lines if not l.startswith("error "))
        return body

    def close(self):
        try:
            self.sock.sendall(b"quit\n")
        except Exception:
            pass
        self.sock.close()


def find_bot(cq, bot_name):
    """Tum sunucu sekmelerinde botu arar; bulunca o sekmeyi 'use' eder."""
    handlers = [d.get("schandlerid") for d in parse_items(cq.cmd("serverconnectionhandlerlist"))]
    needle = bot_name.lower()
    for h in handlers:
        if not h:
            continue
        cq.cmd("use schandlerid=%s" % h)
        try:
            clients = parse_items(cq.cmd("clientlist"))
        except RuntimeError:
            continue  # bagli olmayan sekme
        for c in clients:
            if needle in c.get("client_nickname", "").lower():
                return h, c
    return None, None


def send_to_bot(cfg, text):
    cq = ClientQuery(cfg["clientquery_host"], int(cfg["clientquery_port"]), read_api_key(cfg))
    try:
        h, bot = find_bot(cq, cfg["bot_name"])
        if not bot:
            raise RuntimeError("'%s' adli bot bulunamadi (TS'te bagli mi?)" % cfg["bot_name"])
        cq.cmd("sendtextmessage targetmode=1 target=%s msg=%s" % (bot["clid"], ts_escape(text)))
        return bot["client_nickname"]
    finally:
        cq.close()


def ts_status(cfg):
    try:
        cq = ClientQuery(cfg["clientquery_host"], int(cfg["clientquery_port"]), read_api_key(cfg))
    except Exception as e:
        return {"ts": False, "bot": None, "error": "TS3 ClientQuery'ye baglanilamadi: %s" % e}
    try:
        _, bot = find_bot(cq, cfg["bot_name"])
        return {"ts": True, "bot": bot.get("client_nickname") if bot else None,
                "error": None if bot else "Bot bulunamadi: %s" % cfg["bot_name"]}
    except Exception as e:
        return {"ts": True, "bot": None, "error": str(e)}
    finally:
        cq.close()


# ---------------------------------------------------------------- YouTube

YT_ID = re.compile(r"^[\w-]{11}$")


def normalize_youtube(url):
    """music.youtube / youtu.be / playlist parametreli linkleri sade watch linkine cevirir."""
    try:
        u = urllib.parse.urlparse(url)
    except Exception:
        return None
    host = (u.hostname or "").lower()
    vid = None
    if host.endswith("youtu.be"):
        vid = u.path.strip("/").split("/")[0]
    elif "youtube.com" in host:
        q = urllib.parse.parse_qs(u.query)
        if "v" in q:
            vid = q["v"][0]
        else:
            m = re.match(r"^/(?:shorts|live|embed)/([\w-]{11})", u.path)
            vid = m.group(1) if m else None
    if vid and YT_ID.match(vid):
        return "https://www.youtube.com/watch?v=" + vid
    return None


def youtube_search(query):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Cookie": "CONSENT=YES+1",
    })
    html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "replace")
    # Reklam/shorts yerine ilk normal video sonucunu al
    m = re.search(r'"videoRenderer":\{"videoId":"([\w-]{11})"', html) or \
        re.search(r'"videoId":"([\w-]{11})"', html)
    if not m:
        raise RuntimeError("YouTube'da bulunamadi: %s" % query)
    return "https://www.youtube.com/watch?v=" + m.group(1)


# ---------------------------------------------------------------- HTTP

CFG = load_config()
_last = {"key": None, "t": 0}
_lock = threading.Lock()


def handle_play(data):
    url = data.get("url") or ""
    query = (data.get("query") or "").strip()
    link = normalize_youtube(url) if url else None
    if not link:
        if not query:
            raise RuntimeError("Calinan sarki algilanamadi")
        link = youtube_search(query)
    with _lock:
        now = time.time()
        if _last["key"] == link and now - _last["t"] < float(CFG["dedupe_seconds"]) and not data.get("force"):
            return {"ok": True, "link": link, "skipped": True}
        _last.update(key=link, t=now)
    bot = send_to_bot(CFG, "%s %s" % (CFG["play_command"], link))
    log("PLAY -> %s | %s | %s" % (bot, link, data.get("title") or query))
    return {"ok": True, "link": link, "bot": bot}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path.startswith("/status"):
            st = ts_status(CFG)
            st["bot_name"] = CFG["bot_name"]
            self._send(200, st)
        else:
            self._send(404, {"error": "yok"})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
            if self.path.startswith("/play"):
                self._send(200, handle_play(data))
            elif self.path.startswith("/stop"):
                bot = send_to_bot(CFG, CFG["stop_command"])
                log("STOP -> %s" % bot)
                self._send(200, {"ok": True, "bot": bot})
            else:
                self._send(404, {"error": "yok"})
        except Exception as e:
            log("HATA: %s" % e)
            self._send(200, {"ok": False, "error": str(e)})


def main():
    port = int(CFG["port"])
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        log("Port %d dolu, kopru zaten calisiyor olabilir." % port)
        sys.exit(1)
    log("TS3 Bot DJ koprusu hazir: http://127.0.0.1:%d  (bot: %s)" % (port, CFG["bot_name"]))
    srv.serve_forever()


if __name__ == "__main__":
    main()
