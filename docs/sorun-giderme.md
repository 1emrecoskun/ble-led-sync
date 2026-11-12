# Sorun giderme

## "Device not found"

Şerit aynı anda tek Bluetooth bağlantısı kabul eder. Sırayla kontrol et:

1. Şerit açık ve menzilde mi?
2. Telefon uygulaması (LED LAMP, HappyLighting, …) **kapalı** mı? Arka planda
   durması da bağlantıyı tutar.
3. Bluetooth açık mı: `rfkill list bluetooth` çıktısında `Soft blocked: yes`
   olmamalı, `bluetoothctl show` çıktısında `Powered: yes` yazmalı.
4. `⋯ → Ayarlar` içindeki cihaz adı, şeridin yayınladığı adla aynı mı?
   (Varsayılan `LEDBLE-…`; adını değiştirdiysen buraya yaz.)

Uygulama birkaç saniyede bir kendiliğinden yeniden dener.

## Ekran modu çalışmıyor

Ekran yakalama X11 ister. Wayland'de uygulama sessizce eski bir kareye düşmek
yerine ekran modunu başlatmayı reddeder; ses modunu kullan veya giriş ekranında
"Xorg" oturumunu seç.

## Tepsi simgesi yok

Tepsi için bir StatusNotifierItem sunucusu gerekir. GNOME'da bu, *AppIndicator
and KStatusNotifierItem Support* eklentisidir; KDE ve çoğu panelde yerleşiktir.
Sunucu yoksa uygulama arka planda çalışmaya devam eder.

## Başlattım ama hiçbir şey görünmüyor

Bu normal: açılışta ve `--background` ile pencere göstermeden başlar, tarar ve
LED'i çalıştırır. Pencereyi görmek için uygulama menüsünden **BLE LED Sync**'i
aç; ikinci kez açmak yeni kopya başlatmaz, çalışanı öne getirir.

## Tamamen nasıl kapatırım?

Pencereyi aç, sonra `⋯ → Tamamen çık`. Pencereyi kapatmak yalnızca gizler.

## Loglar nerede?

`~/.local/state/ble-led-sync/logs/uygulama.log` (dönen log, iki eski kopya
saklanır). `run.sh` ayrıca başlatıcı çıktısını
`~/.local/state/ble-led-sync/baslatma.log` dosyasına yazar.

## Tanılama raporunda ne var?

`⋯ → Tanılama`, `~/.local/state/ble-led-sync/` altına bir metin dosyası yazar.
Bluetooth adresleri maskelenir, ama dosya yolları ve işletim sistemi ayrıntıları
kalır; paylaşmadan önce oku.

## Otomatik açılış

Penceredeki onay kutusu `~/.config/autostart/ble-led-sync.desktop` dosyasını
yazar. Kurulum betiği yeni kurulumda bunu (gizli başlatacak şekilde) açar;
kendin başlatmayı tercih ediyorsan kutuyu kapat.
