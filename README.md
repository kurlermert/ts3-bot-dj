<p align="center"><img src="extension/icon128.png" width="96" alt="TS3 Bot DJ"></p>

<h1 align="center">TS3 Bot DJ</h1>

<p align="center">
YouTube, YouTube Music veya Yandex Music'te dinlediğin şarkıyı tek tıkla TeamSpeak 3'teki müzik botuna çaldır.
</p>

<p align="center">
<img src="https://img.shields.io/badge/TeamSpeak-3-2580c3?logo=teamspeak&logoColor=white">
<img src="https://img.shields.io/badge/Chrome-MV3-4285F4?logo=googlechrome&logoColor=white">
<img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white">
<img src="https://img.shields.io/badge/bağımlılık-yok-success">
<img src="https://img.shields.io/badge/lisans-MIT-lightgrey">
</p>

---

Tarayıcıda müzik açarsın, eklenti o an çalan şarkıyı algılar ve TS3'teki müzik botuna **özel mesajla `!play <link>`** gönderir. Kanaldaki herkes aynı şarkıyı dinler.

## Özellikler

- ▶ **Tek tıkla gönder**: popup'tan veya **Alt+Shift+P** kısayoluyla
- 🔁 **Otomatik mod**: şarkı değişip 3 sn çaldığında kendiliğinden gönderir
- 🎵 **YouTube / YouTube Music**: linki doğrudan gönderir (playlist parametresini atar, bot tüm listeyi yüklemez)
- 🟡 **Yandex Music**: sanatçı + şarkı adıyla YouTube'da arar, bulduğu videoyu gönderir
- 🚫 YouTube reklamlarını göndermez, aynı şarkıyı art arda iki kez yollamaz
- ■ **Durdur** butonu (`!stop`)
- 🧩 Python tarafı sadece standart kütüphane kullanır, `pip install` yok

## Nasıl çalışır

```
 Tarayıcı eklentisi ──HTTP──▶ Yerel köprü (bridge.py) ──ClientQuery──▶ TS3 istemcin ──PM──▶ Müzik botu
  (çalan şarkıyı bulur)         127.0.0.1:8765              127.0.0.1:25639               "!play <link>"
```

Tarayıcı eklentileri doğrudan TCP bağlantısı açamadığı için arada küçük bir köprü var. Köprü, TS3 istemcisinin yerleşik **ClientQuery** eklentisi üzerinden, senin hesabınla bota PM atar. Sunucuda hiçbir şey kurmana gerek yok.

## Gereksinimler

- Windows + **TeamSpeak 3 istemcisi** (ClientQuery eklentisi açık, varsayılan olarak açıktır)
- **Python 3.8+**
- Chromium tabanlı tarayıcı: Chrome, Edge, Yandex Browser, Brave, Opera...
- `!play <youtube-link>` komutunu anlayan bir müzik botu (TS3AudioBot, SinusBot vb.)

## Kurulum

### 1. Köprüyü başlat

```bash
git clone https://github.com/kurlermert/ts3-bot-dj.git
```

`bridge\install_startup.bat` dosyasını çalıştır. Köprü arka planda başlar ve Windows açılışına eklenir.
Sadece denemek istersen `bridge\start_bridge_konsol.bat` ile konsolda da açabilirsin.

Kontrol: <http://127.0.0.1:8765/status> adresinde `"bot": "MuzikBot"` görmelisin.

### 2. Eklentiyi yükle

1. Tarayıcıda eklentiler sayfasını aç: `chrome://extensions` (Yandex'te `browser://extensions`)
2. Sağ üstten **Geliştirici modu**nu aç
3. **Paketlenmemiş öğe yükle** → `extension` klasörünü seç
4. Eklentiyi araç çubuğuna sabitle

> Eklentiyi kurmadan önce açık olan müzik sekmesini bir kere yenile.

## Ayarlar

İlk çalıştırmada `bridge\config.json` oluşur (örnek: [`config.example.json`](bridge/config.example.json)):

| Ayar | Varsayılan | Açıklama |
|---|---|---|
| `bot_name` | `MuzikBot` | Botun nick'i. İçinde geçmesi yeterli, büyük/küçük harf fark etmez |
| `play_command` | `!play` | Bota gönderilecek çalma komutu |
| `stop_command` | `!stop` | Durdur komutu |
| `api_key` | *(boş)* | Boşsa `%APPDATA%\TS3Client\clientquery.ini` içinden otomatik okunur |
| `port` | `8765` | Köprünün dinlediği port (değiştirirsen eklentide de değiştir) |
| `dedupe_seconds` | `8` | Aynı link bu süre içinde tekrar gönderilmez |

Ayarı değiştirdikten sonra köprüyü yeniden başlat.

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| Popup'ta "Köprü çalışmıyor" | `bridge\start_bridge_konsol.bat` ile başlat, hatayı konsolda gör |
| "TS kapalı" | TS3 istemcisi açık değil ya da ClientQuery eklentisi kapalı (*Araçlar → Seçenekler → Eklentiler*) |
| "Bot bulunamadı" | Bot sunucuda değil veya `bot_name` yanlış |
| Yandex'te yanlış şarkı | YouTube aramasının ilk sonucu gönderilir, nadiren cover/remix denk gelebilir |

Gönderilen her şarkı `bridge\bridge.log` dosyasına yazılır.

## Lisans

[MIT](LICENSE)
