import os
import time
import sys
from elevenlabs.client import ElevenLabs
import pygame

# CMD Ekran Ayarları (Uluslararası karakter desteği için kritik)
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

def play_audio(file_path):
    """Sesi çalar ve bitene kadar bekler."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload() # Dosya kilidini kaldır
    except Exception as e:
        print(f"Oynatma Hatası: {e}")

def text_to_speech_system():
    # --- Warm-up Logic ---
    print("Sistem başlatılıyor... Merhaba, nasılsın?")
    
    # ElevenLabs Yapılandırması
    client = ElevenLabs(
        api_key="sk_8540f4634a0a7af6a1d6786e645f76021639eea44cc6df3b" 
    )
    
    # Bu model belirttiğin tüm dilleri (TR, EN, DE, ES, PL, PT, FR, HI, vb.) destekler
    SELECTED_MODEL = "eleven_multilingual_v2"
    SELECTED_VOICE_ID = "UgBBYS2sOqTuMpoF3BR0" 
    input_file = 'deepl_en.txt'
    temp_audio = "temp_voice.mp3"
    
    last_pos = 0
    if os.path.exists(input_file):
        last_pos = os.path.getsize(input_file)

    print(f"\n🎙️ HERMES SESLENDİRME SİSTEMİ")
    print(f"Desteklenen Diller: İngilizce, Almanca, İspanyolca, Lehçe, Portekizce,")
    print(f"Filipince, İtalyanca, Hintçe, Çekçe, Fransızca, Arapça, Romence,")
    print(f"Macarca, Türkçe, Hırvatça, Korece, Slovakça, Ukraynaca, İsveççe,")
    print(f"Tamilce, Norveççe, Danca.")
    print("-" * 30)

    try:
        while True:
            if os.path.exists(input_file):
                current_size = os.path.getsize(input_file)
                
                if current_size > last_pos:
                    with open(input_file, "r", encoding="utf-8") as f:
                        f.seek(last_pos)
                        new_content = f.read().strip()
                        
                        if new_content:
                            lines = [l.strip() for l in new_content.split('\n') if l.strip()]
                            for line in lines:
                                if not line.startswith(('-', '=')):
                                    print(f"➤ Okunuyor: {line}")
                                    
                                    try:
                                        # ElevenLabs API Çağrısı
                                        audio_gen = client.text_to_speech.convert(
                                            voice_id=SELECTED_VOICE_ID,
                                            model_id=SELECTED_MODEL,
                                            text=line,
                                            voice_settings={
                                                "stability": 0.45, 
                                                "similarity_boost": 0.8,
                                                "style": 0.0,
                                                "use_speaker_boost": True
                                            }
                                        )
                                        
                                        # Ses verisini MP3 olarak kaydet
                                        with open(temp_audio, "wb") as f_audio:
                                            for chunk in audio_gen:
                                                if chunk:
                                                    f_audio.write(chunk)
                                        
                                        # Seslendir
                                        play_audio(temp_audio)
                                        
                                        # Geçici dosyayı sil (Bir sonraki ses için temizlik)
                                        if os.path.exists(temp_audio):
                                            os.remove(temp_audio)
                                            
                                    except Exception as e:
                                        print(f"⚠️ ElevenLabs Hatası: {e}")

                    last_pos = current_size
            
            # Dosyayı kontrol etme sıklığı
            time.sleep(0.3)

    except KeyboardInterrupt:
        print("\n🛑 Seslendirme sistemi durduruldu.")

if __name__ == "__main__":
    text_to_speech_system()