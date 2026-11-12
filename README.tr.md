# BLE LED Sync — Ses ve Ekran Senkronlu LED Şerit Kontrolcüsü

Ucuz bir Bluetooth LE LED şeridi (LEDBLE / Triones ailesi) bilgisayarınızdan
yöneten küçük bir Linux masaüstü uygulaması: ekran rengini takip eder, sistem
sesine tepki verir veya ikisini harmanlar. Bulut, hesap veya ücretli API yok.

"LEDBLE-XXXX", "Triones", "Magic Blue", "Happy Lighting" gibi adlarla satılan
genel BLE RGB şeritler için (GATT karakteristiği
`0000ffe1-0000-1000-8000-00805f9b34fb`).

🌐 Dil: [English](README.md) | **Türkçe**

## Özellikler
- **SES** modu — ses reaktif (FFT bantları → RGB, beat zarfı).
- **EKRAN** modu — ekran rengi (X11 yakalama, merkez kırpma).
- **SES + EKRAN** (hibrit) — ses vuruşuyla parlaklık değişen ekran rengi.
- Türkçe / İngilizce arayüz, uygulama içi dil seçici (ilk açılışta sistem diline göre).
- Sistem tepsisi (Ayatana AppIndicator), yaklaşık 440×392 piksel küçük pencere.
- Oturum açılışında otomatik SES modu (isteğe bağlı, arayüzden kapatılabilir).
- Parlaklık / hassasiyet sürgüleri, kalıcı ayar.
- Kırmızı bağlantı testi (ses olmadan donanım doğrulama).
- Teşhis raporu + dönen log.
- Kopmada geri bağlanma (backoff); asılı bluez bağlantılarını temizleme.

## Protokol
```
Güç aç : 7E FF 04 01 FF FF FF FF EF
RGB    : 7E FF 05 03 R  G  B  FF EF
Char UUID: 0000ffe1-0000-1000-8000-00805f9b34fb
Tarama adı: LEDBLE-XXXXXX  (şeridinizin adını arayüzden girin: ⋯ → Ses çıkışı / ekran ayarları)
```

## Platform desteği
- **Linux** (X11): tam — ses + ekran senkronu, tepsi simgesi, otomatik açılış. Wayland: yalnızca ses (ekran yakalama X11 ister).
- **Windows**: BLE kontrol, kırmızı test ve ekran senkronu çalışır; ses yakalama yok (0.2.0'da yalnız Linux). Tepsi/otomatik açılış henüz yok.
- **macOS**: BLE kontrol, kırmızı test ve ekran senkronu çalışır; ses yakalama yok (BlackHole + henüz yazılmamış bir yakalama arka ucu gerekir). Tepsi/otomatik açılış henüz yok.

Linux dışı destek yenidir ve az test edilmiştir — hata bildirimleri memnuniyetle karşılanır.

## Gereksinimler
- Linux (ekran yakalama için X11 oturumu; ses için PulseAudio/PipeWire monitor kaynağı)
- Windows / macOS: Python 3.11+, Bluetooth adaptörü, ekran yakalama izni
- Python 3.11+
- Sistem: `python3-tk` (arayüz), `python3-gi` + GTK3 (tepsi, isteğe bağlı), `pulseaudio-utils` (Linux ses), `bluez` (Linux Bluetooth)
- Bluetooth adaptörü + LEDBLE/Triones şerit

## Kurulum (Linux Mint / Ubuntu ailesi)
```bash
# arşivi çıkarın, sonra:
bash KUR.sh
```
Kurucu venv, `bleak`, `mss`, `numpy`, sistem paketlerini (`python3-tk`,
`python3-gi`, GTK3, varsa AppIndicator), menü girişini ve otomatik açılışı
kurar. Eksik isteğe bağlı parçalar yalnızca uyarı üretir.

Her platformda (geliştirme kurulumu):
```bash
python3 -m pip install .          # `ble-led-sync` komutunu kurar
ble-led-sync                      # veya: python3 -m led_sync.app
```

Depodan elle çalıştırma:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh               # pencere açar
./run.sh --background  # gizli başlat: LED çalışır, pencere yok
```

## Testler
```bash
python3 -m unittest discover -s tests -v
```
55 birim testi (protokol, renk, beat zarfı, motor, masaüstü entegrasyonu).

## Belgeler
- `docs/protocol-reversing.md` — BLE protokolü, paket yapısı, güvenlik gözlemleri
  (IoT / red-team araştırması için).
- `SECURITY.md` — sorumlu kullanım ve IoT güvenlik notları.
- `CONTRIBUTING.md` — geliştirme kurulumu ve katkı kuralları.

## Sorumluluk Reddi (Disclaimer)
Bu yazılım **olduğu gibi** (as-is) sunulur, hiçbir garanti verilmez. Yazar(lar)
doğrudan veya dolaylı hiçbir zarardan sorumlu değildir. Bu araç **yalnızca
sahip olduğunuz cihazları** kontrol etmek için tasarlanmıştır; başkalarının
cihazlarına yetkisiz erişim veya kullanım yasalara aykırıdır ve tamamen
kullanıcının sorumluluğundadır. Kötü niyetli kullanım durumunda tüm hukuki ve
cezai sorumluluk kullanıcıya aittir.

## Nelerin üzerine kuruldu

Pencere, tepsi simgesi ve ses motoru bu projenin kendi işi. Sıkıcı kısımlar
(tek örnek kilidi, XDG yolları, menü girişi, otomatik açılış, Wayland farkındalı
tepsi tespiti, dönen log) bu uygulamadan çıkarılmış küçük ve bağımlılıksız
[`desktop-lifecycle`](https://github.com/1emrecoskun/desktop-lifecycle)
kütüphanesinden geliyor.

## Gizlilik

- Ses, kendi çıkış cihazınızın monitor kaynağından okunur; mikrofon hiç
  kullanılmaz.
- Ekran modu kendi sanal ekranınızı okur; hiçbir şey saklanmaz, hiçbir yere
  gönderilmez.
- Hesap yok, telemetri yok, analitik yok; şeridinize yerel Bluetooth bağlantısı
  dışında ağ istemcisi yok.
- Tanılama raporu, issue'ya yapıştırmadan önce Bluetooth adreslerini maskeler;
  yine de dosya yolları ve işletim sistemi ayrıntıları içerir. Paylaşmadan önce
  okuyun.

## Kim yaptı
[Emre Coşkun](https://github.com/1emrecoskun) tarafından yazıldı.

## Lisans ve isimler
MIT — bkz. `LICENSE`. Lisans kodu kapsar; proje adını veya simgesini kapsamaz ve
garanti vermez. "LEDBLE" ve "Triones" kendi sahiplerine aittir; bu proje onlarla
bağlantılı değildir.
