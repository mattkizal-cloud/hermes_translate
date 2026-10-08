import speech_recognition as sr
import os
import sys
import unicodedata
import threading
import queue

# UTF-8 ve CMD Ayarları
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

def karakter_duzelt(metin):
    metin = unicodedata.normalize('NFC', metin)
    degisim = {"İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç"}
    for buyuk, kucuk in degisim.items():
        metin = metin.replace(buyuk, kucuk)
    return metin.lower()

ses_kuyrugu = queue.Queue()

def tanima_motoru():
    r = sr.Recognizer()
    while True:
        audio = ses_kuyrugu.get()
        if audio is None: break
        
        # --- DİNAMİK DİL OKUMA ---
        try:
            if os.path.exists("lang_config.txt"):
                with open("lang_config.txt", "r", encoding="utf-8") as f_lang:
                    current_lang = f_lang.read().strip()
            else:
                current_lang = "tr-TR"
        except:
            current_lang = "tr-TR"

        try:
            ham_metin = r.recognize_google(audio, language=current_lang)
            if ham_metin:
                cikti = karakter_duzelt(ham_metin)
                print(f"({current_lang}) >> {cikti}")
                
                with open("write_tr.txt", "w", encoding="utf-8") as f:
                    f.write(cikti)
                
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Google Servis Hatası: {e}")
        except Exception:
            pass
            
        ses_kuyrugu.task_done()

def asistan_yazici_modu():
    print("\n🚀 IQ CODERS: HERMES SES MOTORU AKTİF")
    
    # --- MİKROFON CİHAZ SEÇİMİ (EKLENDİ) ---
    device_index = None
    if os.path.exists("mic_config.txt"):
        try:
            with open("mic_config.txt", "r") as f:
                content = f.read().strip()
                if content:
                    device_index = int(content)
                    print(f"✅ Seçili Mikrofon ID: {device_index}")
        except Exception as e:
            print(f"⚠️ Mikrofon ayarı okunamadı, varsayılan cihaz kullanılıyor: {e}")

    r = sr.Recognizer()
    r.dynamic_energy_threshold = False  
    r.energy_threshold = 300            
    r.pause_threshold = 0.6             
    r.operation_timeout = None

    isçi = threading.Thread(target=tanima_motoru, daemon=True)
    isçi.start()

    # Belirlenen cihaz_index ile mikrofonu başlat
    try:
        with sr.Microphone(device_index=device_index) as source:
            r.adjust_for_ambient_noise(source, duration=0.8)
            print(f"🎙️ Mikrofon şu an dinlemede... (Dil: lang_config.txt üzerinden takip ediliyor)")

            while True:
                try:
                    audio = r.listen(source, timeout=None, phrase_time_limit=4)
                    ses_kuyrugu.put(audio)
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ KRİTİK HATA: Mikrofon başlatılamadı! Seçilen cihaz bağlı olmayabilir.\nHata: {e}")

if __name__ == "__main__":
    try:
        asistan_yazici_modu()
    except KeyboardInterrupt:
        print("\n🛑 Sistem Kapatıldı.")