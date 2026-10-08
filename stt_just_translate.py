import streamlit as st
import os
import time
import deepl
import subprocess
import atexit
import sys

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Hermes Voice Translator AI", layout="wide", page_icon="🌐")

# API ANAHTARI
DEEPL_KEY = "edb5f427-77f9-4ec1-886b-a48e92090259:fx"

# --- OTOMATİK BAŞLATMA MANTIĞI ---
if 'sub_process' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    write_tr_path = os.path.join(current_dir, "write_tr.py")
    
    proc = subprocess.Popen([sys.executable, write_tr_path])
    st.session_state['sub_process'] = proc
    st.toast("Hermes Ses Motoru Aktif!", icon="🎙️")
    st.toast("Sistem hazır... Birikimli metin çeviri modu aktif.", icon="📝")

st.title("🌐 IQ Coders: Hermes Voice Translator AI")
st.caption("Uluslararası 22 Dil Destekli Canlı ve Birikimli Çeviri Sistemi")

# --- DİL SÖZLÜĞÜ (22 DİL) ---
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
    trg_lang_name = st.selectbox("🎯 Çeviri Dili:", list(languages.keys()), index=0)
    trg_code = languages[trg_lang_name]["deepl"]
    with open("target_lang_config.txt", "w", encoding="utf-8") as f:
        f.write(trg_code)

st.divider()

# Oturum geçmişi için listeler
if "source_history" not in st.session_state:
    st.session_state.source_history = []

if "target_history" not in st.session_state:
    st.session_state.target_history = []

# Arayüz Sütunları
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"📥 Gelen ({src_lang_name})")
    source_box = st.container()

with col2:
    st.subheader(f"📤 Çevrilen ({trg_lang_name})")
    target_box = st.container()

# --- DOSYA TEMİZLEME (KAPANIŞTA) ---
def dosyalari_bosalt():
    for d in ['write_tr.txt', 'translate.txt']:
        if os.path.exists(d):
            with open(d, "w", encoding="utf-8") as f: f.write("")
atexit.register(dosyalari_bosalt)

# --- ANA İŞLEME DÖNGÜSÜ ---
input_file = 'write_tr.txt'
output_translate_file = 'translate.txt'

if "last_mtime" not in st.session_state:
    st.session_state.last_mtime = 0

if os.path.exists(input_file):
    current_mtime = os.path.getmtime(input_file)
    
    if current_mtime != st.session_state.last_mtime:
        with open(input_file, "r", encoding="utf-8") as f:
            captured_text = f.read().strip()
        
        # Eğer gelen metin daha önce listeye eklenen son metinle aynı değilse işleme al (tekrarı önler)
        if captured_text and (not st.session_state.source_history or captured_text != st.session_state.source_history[-1]):
            st.session_state.source_history.append(captured_text)
            
            try:
                # DeepL Çeviri
                translator = deepl.Translator(DEEPL_KEY)
                result = translator.translate_text(captured_text, target_lang=trg_code)
                translated_text = result.text
                
                st.session_state.target_history.append(translated_text)
                
                # Çevrilen Metni translate.txt dosyasına ALT ALTA ekleme
                with open(output_translate_file, "a", encoding="utf-8") as f_trans:
                    f_trans.write(translated_text + "\n")
                        
            except Exception as e:
                st.error(f"Sistem Hatası: {e}")

        st.session_state.last_mtime = current_mtime

# Geçmiş tüm mesajları arayüzde alt alta listele
with source_box:
    for text in st.session_state.source_history:
        st.chat_message("user").write(text)

with target_box:
    for text in st.session_state.target_history:
        st.chat_message("assistant").write(text)

# Canlı izleme hızı
time.sleep(0.4)
st.rerun()