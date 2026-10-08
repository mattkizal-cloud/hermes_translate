import streamlit as st
import os
import time
import deepl
from elevenlabs.client import ElevenLabs
import pygame
import subprocess
import atexit
import sys
from google_auth_oauthlib.flow import Flow

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Hermes Voice Translator AI", layout="wide", page_icon="🌐")

# --- GOOGLE AUTH AYARLARI ---
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
REDIRECT_URI = "http://localhost:8501"

# Session State Başlatma
if 'connected' not in st.session_state: 
    st.session_state.connected = False

# --- GİRİŞ MANTIĞI (KİLİT MEKANİZMASI) ---
query_params = st.query_params
if "code" in query_params and not st.session_state.connected:
    try:
        flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
        st.session_state.user_info = user_info
        st.session_state.connected = True
        st.rerun()
    except Exception as e:
        st.error(f"Giriş hatası: {e}")

if not st.session_state.connected:
    st.title("🌐 IQ Coders: Hermes AI")
    st.info("Sistemi başlatmak için Google hesabınızla giriş yapmanız gerekiyor.")
    
    try:
        flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f'''
            <a href="{auth_url}" target="_self" style="
                text-decoration:none; 
                background-color: #4285F4; 
                color: white; 
                padding: 12px 24px; 
                border-radius: 5px; 
                font-weight: bold; 
                display: inline-block;
                transition: 0.3s;">
                Google ile Giriş Yap
            </a>
        ''', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Yapılandırma dosyası (client_secret.json) bulunamadı: {e}")
    
    st.stop() # Giriş yapılana kadar aşağıdaki kodların çalışmasını durdurur.

# --- GİRİŞ YAPILDIKTAN SONRA ÇALIŞACAK ANA PROGRAM ---

# API ANAHTARLARI
DEEPL_KEY = "edb5f427-77f9-4ec1-886b-a48e92090259:fx"
ELEVEN_KEY = "sk_8540f4634a0a7af6a1d6786e645f76021639eea44cc6df3b"

# --- OTOMATİK BAŞLATMA MANTIĞI ---
if 'sub_process' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    write_tr_path = os.path.join(current_dir, "write_tr.py")
    
    if os.path.exists(write_tr_path):
        proc = subprocess.Popen([sys.executable, write_tr_path])
        st.session_state['sub_process'] = proc
        st.toast(f"Hoş geldin {st.session_state.user_info['name']}! Ses Motoru Aktif.", icon="👋")
    else:
        st.error("Hata: 'write_tr.py' dosyası bulunamadı!")

# --- ARAYÜZ ÜST KISIM ---
st.sidebar.image(st.session_state.user_info.get('picture', ""), width=70)
st.sidebar.write(f"**Kullanıcı:** {st.session_state.user_info['name']}")
if st.sidebar.button("🔴 Güvenli Çıkış"):
    st.session_state.connected = False
    st.rerun()

st.title("🌐 IQ Coders: Hermes Voice Translator AI")
st.caption("Uluslararası 22 Dil Destekli Canlı Çeviri Sistemi")

# --- DİL SÖZLÜĞÜ ---
languages = {
    "English": {"google": "en-US", "deepl": "EN-US"},
    "German": {"google": "de-DE", "deepl": "DE"},
    "Spanish": {"google": "es-ES", "deepl": "ES"},
    "Polish": {"google": "pl-PL", "deepl": "PL"},
    "Portuguese": {"google": "pt-PT", "deepl": "PT-PT"},
    "Filipino": {"google": "fil-PH", "deepl": "EN-US"},
    "Italian": {"google": "it-IT", "deepl": "IT"},
    "Hindi": {"google": "hi-IN", "deepl": "EN-US"},
    "Czech": {"google": "cs-CZ", "deepl": "CS"},
    "French": {"google": "fr-FR", "deepl": "FR"},
    "Arabic": {"google": "ar-SA", "deepl": "EN-US"},
    "Romanian": {"google": "ro-RO", "deepl": "RO"},
    "Hungarian": {"google": "hu-HU", "deepl": "HU"},
    "Turkish": {"google": "tr-TR", "deepl": "TR"},
    "Croatian": {"google": "hr-HR", "deepl": "EN-US"},
    "Korean": {"google": "ko-KR", "deepl": "KO"},
    "Slovak": {"google": "sk-SK", "deepl": "SK"},
    "Ukrainian": {"google": "uk-UA", "deepl": "UK"},
    "Swedish": {"google": "sv-SE", "deepl": "SV"},
    "Tamil": {"google": "ta-IN", "deepl": "EN-US"},
    "Norwegian": {"google": "no-NO", "deepl": "NB"},
    "Danish": {"google": "da-DK", "deepl": "DA"}
}

# --- ARAYÜZ SEÇİM ALANI ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    src_lang_name = st.selectbox("🎙️ Konuşacağınız Dil:", list(languages.keys()), index=13)
    src_code = languages[src_lang_name]["google"]
    with open("lang_config.txt", "w", encoding="utf-8") as f:
        f.write(src_code)

with c2:
    trg_lang_name = st.selectbox("🎯 Çeviri ve Seslendirme Dili:", list(languages.keys()), index=0)
    trg_code = languages[trg_lang_name]["deepl"]
    with open("target_lang_config.txt", "w", encoding="utf-8") as f:
        f.write(trg_code)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader(f"📥 Gelen ({src_lang_name})")
    tr_placeholder = st.empty()

with col2:
    st.subheader(f"📤 Seslendirilen ({trg_lang_name})")
    en_placeholder = st.empty()

# --- SES ÇALMA FONKSİYONU ---
def play_audio(file_path):
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    except Exception as e:
        print(f"Ses çalma hatası: {e}")

# --- DOSYA TEMİZLEME ---
def dosyalari_bosalt():
    for d in ['write_tr.txt', 'deepl_en.txt']:
        if os.path.exists(d):
            with open(d, "w", encoding="utf-8") as f: f.write("")
atexit.register(dosyalari_bosalt)

# --- ANA İŞLEME DÖNGÜSÜ ---
input_file = 'write_tr.txt'

if "last_mtime" not in st.session_state:
    st.session_state.last_mtime = 0

if os.path.exists(input_file):
    current_mtime = os.path.getmtime(input_file)
    
    if current_mtime != st.session_state.last_mtime:
        with open(input_file, "r", encoding="utf-8") as f:
            captured_text = f.read().strip()
        
        if captured_text:
            tr_placeholder.chat_message("user").write(captured_text)
            
            try:
                # 1. DeepL Çeviri
                translator = deepl.Translator(DEEPL_KEY)
                result = translator.translate_text(captured_text, target_lang=trg_code)
                translated_text = result.text
                
                en_placeholder.chat_message("assistant").write(translated_text)
                
                # 2. ElevenLabs Seslendirme
                client = ElevenLabs(api_key=ELEVEN_KEY)
                audio_gen = client.text_to_speech.convert(
                    voice_id="UgBBYS2sOqTuMpoF3BR0",
                    model_id="eleven_multilingual_v2",
                    text=translated_text
                )
                
                temp_filename = f"voice_{int(time.time())}.mp3"
                with open(temp_filename, "wb") as f_audio:
                    for chunk in audio_gen:
                        if chunk: f_audio.write(chunk)
                
                play_audio(temp_filename)
                
                if os.path.exists(temp_filename):
                    try: os.remove(temp_filename)
                    except: pass
                        
            except Exception as e:
                st.error(f"Sistem Hatası: {e}")

        st.session_state.last_mtime = current_mtime

# Canlı izleme hızı (0.4 saniye bekle ve yeniden çalıştır)
time.sleep(0.4)
st.rerun()