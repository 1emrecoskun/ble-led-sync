"""Minimal i18n for BLE LED Sync. Supported: 'en', 'tr'."""
import locale
import os

SUPPORTED = ('en', 'tr')
DEFAULT = 'en'

TRANSLATIONS = {
    'en': {
        'status_starting': 'Starting…',
        'mode_audio': 'Audio',
        'mode_screen': 'Screen',
        'mode_hybrid': 'Audio + Screen',
        'label_brightness': 'Brightness',
        'label_sensitivity': 'Sensitivity',
        'btn_start': 'Start',
        'btn_stop': 'Stop',
        'btn_hide': 'Hide',
        'chk_autostart': 'Start in Audio mode on login',
        'menu_settings': 'Audio output / screen settings',
        'menu_test_red': 'Red connection test',
        'menu_diagnose': 'Create diagnostic report',
        'menu_logs': 'Open log folder',
        'menu_quit': 'Quit completely',
        'status_stopped': 'Stopped • LED may keep its last color',
        'status_connecting': '{mode} • connecting…',
        'status_test_red': 'Red test • check the actual LED color',
        'warn_screen_wayland': 'Screen capture in this version works on X11 only. Audio mode is available.',
        'msg_tray_unavailable': 'No tray here; the app runs in the background. Quit from … → Quit.',
        'autostart_title': 'Autostart',
        'hybrid_hint': 'Hybrid: screen color + bass/energy pulse',
        'advanced_title': 'Extra settings',
        'advanced_audio': 'Audio output (not microphone)',
        'advanced_auto_output': 'Automatic — follow the default output',
        'advanced_device': 'Device name:',
        'advanced_device_hint': 'Must match the name advertised by the strip (for example LEDBLE-XXXXXX).',
        'advanced_crop': 'Use the screen center',
        'advanced_monitor': 'Screen no:',
        'advanced_apply': 'Apply',
        'diag_report': 'Report',
        'diag_report_note': 'Review the contents before sharing it publicly.',
    },
    'tr': {
        'status_starting': 'Başlatılıyor…',
        'mode_audio': 'SES',
        'mode_screen': 'EKRAN',
        'mode_hybrid': 'SES + EKRAN',
        'label_brightness': 'Parlaklık',
        'label_sensitivity': 'Hassasiyet',
        'btn_start': 'Başlat',
        'btn_stop': 'Durdur',
        'btn_hide': 'Gizle',
        'chk_autostart': 'Oturum açılınca SES modunda otomatik çalış',
        'menu_settings': 'Ses çıkışı / ekran ayarları',
        'menu_test_red': 'Kırmızı bağlantı testi',
        'menu_diagnose': 'Teşhis raporu oluştur',
        'menu_logs': 'Log klasörünü aç',
        'menu_quit': 'Tamamen çık',
        'status_stopped': 'Durduruldu • LED son renginde kalabilir',
        'status_connecting': '{mode} • bağlanıyor…',
        'status_test_red': 'Kırmızı test • gerçek LED rengini kontrol edin',
        'warn_screen_wayland': 'Bu sürümde ekran yakalama yalnız X11 oturumunda çalışır. SES modu kullanılabilir.',
        'msg_tray_unavailable': 'Tepsi yok; uygulama arka planda çalışıyor. Çıkmak için … → Tamamen çık.',
        'autostart_title': 'Otomatik açılış',
        'hybrid_hint': 'Hibrit: ekran rengi + bas/enerji vuruşu',
        'advanced_title': 'Ek ayarlar',
        'advanced_audio': 'Ses çıkışı (mikrofon değil)',
        'advanced_auto_output': 'Otomatik — varsayılan çıkışı takip et',
        'advanced_device': 'Cihaz adı:',
        'advanced_device_hint': 'Şeridin yayınladığı adla aynı olmalı (örnek: LEDBLE-XXXXXX).',
        'advanced_crop': 'Ekran merkezini kullan',
        'advanced_monitor': 'Ekran no:',
        'advanced_apply': 'Uygula',
        'diag_report': 'Rapor',
        'diag_report_note': 'Paylaşmadan önce içeriğini kontrol edin.',
    },
}


def detect_language():
    """Detect preferred language from the environment."""
    for var in ('LC_ALL', 'LC_MESSAGES', 'LANG', 'LANGUAGE'):
        val = os.environ.get(var, '')
        if val:
            code = val.split('.')[0].split('_')[0].split(':')[0].lower()
            if code in SUPPORTED:
                return code
    try:
        code = locale.getlocale()[0]
        if code:
            code = code.split('_')[0].lower()
            if code in SUPPORTED:
                return code
    except Exception:
        pass
    return DEFAULT


def t(key, lang='en'):
    lang = lang if lang in SUPPORTED else DEFAULT
    return TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT]).get(key, key)
