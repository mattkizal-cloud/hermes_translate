import deepl
import os
import time
import sys

# CMD Ekran Ayarları (Türkçe karakter desteği için)
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

def translate_system():
    # --- Warm-up Logic ---
    # Sistem başladığında süreçlerin hazır olduğunu belirten selamlama
    print("Sistem başlatılıyor... Merhaba, nasılsın?")
    
    # DeepL API Anahtarın
    auth_key = "edb5f427-77f9-4ec1-886b-a48e92090259:fx" 
    translator = deepl.Translator(auth_key)

    input_file = 'write_tr.txt'
    output_file = 'deepl_en.txt'
    config_file = 'target_lang_config.txt'

    # Dosyanın son değişim zamanını takip etmek için değişken
    last_mtime = 0

    print(f"\n🚀 DEEPL DİNAMİK ÇEVİRİ MODU AKTİF")
    print(f"Hedef dil '{config_file}' üzerinden takip ediliyor...")
    print("-" * 30)

    try:
        while True:
            if os.path.exists(input_file):
                # Dosyanın son güncellenme vaktini al
                current_mtime = os.path.getmtime(input_file)

                # Eğer dosya vakti değişmişse (yeni veri gelmişse)
                if current_mtime != last_mtime:
                    try:
                        # --- HEDEF DİLİ DOSYADAN OKU ---
                        if os.path.exists(config_file):
                            with open(config_file, "r", encoding="utf-8") as f_lang:
                                current_target = f_lang.read().strip()
                        else:
                            current_target = "EN-US" # Dosya yoksa varsayılan İngilizce

                        # Giriş metnini oku
                        with open(input_file, "r", encoding="utf-8") as f:
                            text_to_translate = f.read().strip()

                        if text_to_translate:
                            # DeepL API ile çeviri (Hedef dil değişken!)
                            # source_lang belirtmiyoruz, DeepL giriş dilini otomatik tanır.
                            result = translator.translate_text(
                                text_to_translate, 
                                target_lang=current_target
                            )
                            translated_text = result.text

                            # Konsola (CMD) yazdır
                            print(f"Girdi: {text_to_translate}")
                            print(f"Çeviri ({current_target}): {translated_text}")
                            print("-" * 20)

                            # Sonucu deepl_en.txt dosyasına ekle (veya üzerine yaz)
                            with open(output_file, "a", encoding="utf-8") as f_out:
                                f_out.write(translated_text + "\n")

                        # İşlenen vaktini güncelle
                        last_mtime = current_mtime 

                    except Exception as e:
                        print(f"Çeviri sırasında hata: {e}")
            
            # Dosya sistemini saniyede 10 kez kontrol eder
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Çeviri sistemi kapatıldı.")

if __name__ == "__main__":
    translate_system()