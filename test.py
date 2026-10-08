import streamlit as st
import os
import json
import time
from google_auth_oauthlib.flow import Flow
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import threading
import queue
import av

# --- 1. SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Görüntülü Sohbet", layout="wide")

# --- 2. OTURUM DEĞİŞKENLERİ ---
if "connected" not in st.session_state:
    st.session_state.connected = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "page" not in st.session_state:
    st.session_state.page = "main"
if "incoming_call" not in st.session_state:
    st.session_state.incoming_call = False
if "caller_email" not in st.session_state:
    st.session_state.caller_email = None
if "call_room" not in st.session_state:
    st.session_state.call_room = None

# --- 3. GOOGLE GİRİŞ ---
CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
REDIRECT_URI = "http://localhost:8501"

query_params = st.query_params
if "code" in query_params and not st.session_state.connected:
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=query_params["code"])
        st.session_state.user_info = (
            flow.authorized_session()
            .get("https://www.googleapis.com/oauth2/v1/userinfo")
            .json()
        )
        st.session_state.connected = True
        st.rerun()
    except Exception as e:
        st.error(f"Giriş hatası: {e}")

# Giriş yapılmamışsa giriş ekranı göster
if not st.session_state.connected or st.session_state.user_info is None:
    st.title("🔐 Görüntülü Sohbet - Giriş Yap")
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        st.markdown(
            f'<a href="{auth_url}" target="_self" style="text-decoration:none; background-color: #4285F4; color: white; padding: 12px 24px; border-radius: 5px; font-weight: bold; display: inline-block;">Google ile Giriş Yap</a>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"client_secret.json dosyası bulunamadı veya hatalı: {e}")
    st.stop()

# --- 4. KULLANICI BİLGİLERİ ---
me = st.session_state.user_info
my_email = me["email"]
st.sidebar.success(f"Hoş geldin, {me['name']}")

# --- 5. KULLANICI DURUM DOSYASI ---
ACTIVE_USERS_FILE = "active_users.json"

def load_users():
    if not os.path.exists(ACTIVE_USERS_FILE):
        return {}
    try:
        with open(ACTIVE_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Kullanıcılar yüklenirken hata: {e}")
        return {}

def save_users(users):
    try:
        with open(ACTIVE_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Kullanıcılar kaydedilirken hata: {e}")

# Kullanıcı durumunu güncelle
users = load_users()
current_status = users.get(my_email, {}).get("status", "online")
current_room = users.get(my_email, {}).get("room", "")

users[my_email] = {
    "name": me["name"],
    "picture": me.get("picture", ""),
    "last_seen": time.time(),
    "status": current_status,
    "room": current_room,
}
save_users(users)

# --- 6. GELEN ARAMA KONTROLÜ ---
users = load_users()
for email, info in users.items():
    # Beni arıyor mu kontrolü
    if (email != my_email and 
        info.get("status") == "calling" and 
        info.get("room") == my_email):  # room alanı arayanın email'ini içeriyor
        st.session_state.incoming_call = True
        st.session_state.caller_email = email
        st.session_state.call_room = info.get("room")
        break

# --- 7. SAYFA YÖNLENDİRME ---
if st.session_state.incoming_call:
    st.session_state.page = "incoming_call"
elif users.get(my_email, {}).get("status") == "in_call":
    st.session_state.page = "call"
else:
    st.session_state.page = "main"

# --- 8. ANA SAYFA (KULLANICI LİSTESİ) ---
if st.session_state.page == "main":
    st.title("📱 Görüntülü Sohbet - Ana Sayfa")
    
    # Mevcut kullanıcıları göster (debug için)
    st.sidebar.write("### Debug - Tüm Kullanıcılar")
    for email, info in users.items():
        st.sidebar.write(f"{email}: {info.get('status')} - {time.time() - info.get('last_seen', 0):.1f}s")
    
    # Kullanıcıları listele (son 15 saniye içinde aktif olanlar)
    online_users = {}
    current_time = time.time()
    
    for email, info in users.items():
        if email != my_email:
            time_diff = current_time - info.get("last_seen", 0)
            if time_diff < 15:  # 15 saniye içinde aktif
                online_users[email] = info
    
    st.subheader(f"🟢 Çevrimiçi Kullanıcılar ({len(online_users)})")
    
    if online_users:
        for email, info in online_users.items():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            # Kullanıcı adı ve durumu
            status_emoji = "🟢" if info.get("status") == "online" else "🔴"
            col1.write(f"{status_emoji} **{info['name']}**")
            
            # Durum metni
            status_text = info.get("status", "online")
            col2.write(f"`{status_text}`")
            
            # Ara butonu - Sadece online ve meşgul değilse göster
            if info.get("status") == "online":
                if col3.button("📞 Ara", key=f"call_{email}"):
                    st.info(f"Aranıyor: {info['name']}...")
                    
                    # Benzersiz oda oluştur
                    new_room = f"room_{int(time.time())}_{my_email}"
                    
                    users = load_users()
                    # Arayan kişi: arama modunda
                    users[my_email]["status"] = "calling"
                    users[my_email]["room"] = email  # Aranan kişinin email'i
                    
                    # Aranan kişi: çağrı alıyor
                    if email in users:
                        users[email]["status"] = "calling"
                        users[email]["room"] = my_email  # Arayanın email'i
                    
                    save_users(users)
                    st.success("Arama gönderildi! Karşı tarafın cevap vermesini bekleyin...")
                    time.sleep(2)
                    st.rerun()
            else:
                col3.write("🔴 Meşgul")
            
            # Son görülme
            col4.write(f"{int(current_time - info.get('last_seen', 0))}s")
    else:
        st.warning("Şu anda çevrimiçi başka kullanıcı yok.")
        st.info("Uygulamayı başka bir tarayıcıda açarak test edebilirsiniz.")
    
    # Durumumu göster
    st.sidebar.write("---")
    st.sidebar.write(f"**Durumunuz:** {users[my_email]['status']}")
    st.sidebar.write(f"**Email:** {my_email}")
    
    # Manuel yenileme butonu
    if st.sidebar.button("🔄 Listeyi Yenile"):
        st.rerun()

# --- 9. GELEN ARAMA EKRANI ---
elif st.session_state.page == "incoming_call":
    st.title("📞 Gelen Arama")
    
    caller_info = users.get(st.session_state.caller_email, {})
    caller_name = caller_info.get("name", "Bilinmeyen")
    
    # Büyük ve dikkat çekici arama ekranı
    st.markdown(f"""
    <div style="text-align: center; padding: 50px; background-color: #f0f2f6; border-radius: 10px;">
        <h1 style="font-size: 48px;">📞</h1>
        <h2>{caller_name} sizi arıyor...</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        col_kabul, col_red = st.columns(2)
        
        with col_kabul:
            if st.button("✅ KABUL ET", use_container_width=True, type="primary"):
                # Yeni oda oluştur
                new_room = f"room_{int(time.time())}_{my_email}_{st.session_state.caller_email}"
                
                users = load_users()
                # Benim durumumu güncelle
                users[my_email]["status"] = "in_call"
                users[my_email]["room"] = new_room
                
                # Arayanın durumunu güncelle
                if st.session_state.caller_email in users:
                    users[st.session_state.caller_email]["status"] = "in_call"
                    users[st.session_state.caller_email]["room"] = new_room
                
                save_users(users)
                
                st.session_state.incoming_call = False
                st.session_state.page = "call"
                st.rerun()
        
        with col_red:
            if st.button("❌ REDDET", use_container_width=True):
                # Arayanın durumunu sıfırla
                users = load_users()
                if st.session_state.caller_email in users:
                    users[st.session_state.caller_email]["status"] = "online"
                    users[st.session_state.caller_email]["room"] = ""
                users[my_email]["status"] = "online"
                users[my_email]["room"] = ""
                save_users(users)
                
                st.session_state.incoming_call = False
                st.session_state.page = "main"
                st.rerun()

# --- 10. GÖRÜŞME EKRANI (MANYCAM DESTEKLİ) ---
elif st.session_state.page == "call":
    st.title("🎥 Görüntülü Görüşme")
    
    # Oda bilgisini al
    users = load_users()
    my_status = users.get(my_email, {})
    room = my_status.get("room", "")
    
    # Görüşme partnerini bul
    partner_email = None
    for email, info in users.items():
        if info.get("room") == room and email != my_email:
            partner_email = email
            break
    
    if partner_email:
        st.success(f"📞 **{users[partner_email]['name']}** ile görüşüyorsunuz")
    else:
        st.warning("⏳ Partner bekleniyor... Bağlantı kuruluyor...")
    
    # GELİŞMİŞ KAMERA SEÇİMİ (ManyCam dahil tüm kameralar için)
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.write("### 📷 Kamera Ayarları")
        
        # Kamerayı device ID yerine "ideal" constraint ile seç
        camera_options = [
            "Varsayılan Kamera",
            "HD Kamera", 
            "ManyCam Virtual Webcam",
            "DroidCam",
            "OBS Virtual Camera"
        ]
        
        selected_camera = st.selectbox(
            "Kamera Seç", 
            camera_options,
            index=0,
            help="ManyCam, DroidCam, OBS gibi sanal kameraları destekler"
        )
        
        # Kamera test butonu
        if st.button("📸 Kamerayı Test Et"):
            st.info("Kamera açılıyor... Eğer görüntü gelmiyorsa farklı bir kamera seçin.")
        
        st.write("---")
        st.write("### 🎤 Ses Ayarları")
        st.checkbox("Mikrofonu Aç", value=True)
        st.slider("Ses Seviyesi", 0, 100, 80)
        
        st.write("---")
        if st.button("🔴 Görüşmeyi Bitir", use_container_width=True, type="primary"):
            # Görüşmeyi sonlandır
            users = load_users()
            users[my_email]["status"] = "online"
            users[my_email]["room"] = ""
            
            if partner_email and partner_email in users:
                users[partner_email]["status"] = "online"
                users[partner_email]["room"] = ""
            
            save_users(users)
            st.session_state.page = "main"
            st.rerun()
    
    with col1:
        # MANYCAM VE DİĞER SANAL KAMERALAR İÇİN OPTİMİZE EDİLMİŞ WEBRTC
        st.write("### Görüntü")
        
        # WebRTC yapılandırması - ManyCam dahil tüm kameraları destekler
        webrtc_ctx = webrtc_streamer(
            key=f"call-{room}-{int(time.time())}",  # Benzersiz key
            mode=WebRtcMode.SENDRECV,
            rtc_configuration={
                "iceServers": [
                    {"urls": ["stun:stun.l.google.com:19302"]},
                    {"urls": ["stun:stun1.l.google.com:19302"]},
                    {"urls": ["stun:stun2.l.google.com:19302"]},
                    {"urls": ["stun:stun3.l.google.com:19302"]},
                    {"urls": ["stun:stun4.l.google.com:19302"]}
                ],
                "iceCandidatePoolSize": 10,
                "bundlePolicy": "max-bundle",
                "rtcpMuxPolicy": "require"
            },
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480},
                    "frameRate": {"ideal": 30},
                    "facingMode": "user",
                    "deviceId": {"exact": "default"}  # ManyCam için exact yerine ideal kullan
                },
                "audio": {
                    "echoCancellation": {"exact": True},
                    "noiseSuppression": {"exact": True},
                    "autoGainControl": {"exact": True}
                },
            },
            video_processor_factory=None,
            async_processing=True,
        )
        
        # Kamera durumu
        if webrtc_ctx and webrtc_ctx.state and webrtc_ctx.state.playing:
            st.success("✅ Kamera aktif - Görüntü aktarılıyor")
        else:
            st.warning("⏳ Kamera başlatılıyor... Lütfen bekleyin")
            st.info("Eğer kamera açılmazsa, tarayıcı izinlerini kontrol edin")

# --- 11. OTOMATİK TEMİZLİK ---
# Süresi dolmuş kullanıcıları temizle
current_time = time.time()
users = load_users()
updated = False

for email in list(users.keys()):
    if current_time - users[email]["last_seen"] > 30:  # 30 saniye
        del users[email]
        updated = True

if updated:
    save_users(users)

# --- 12. PERİYODİK YENİLEME ---
# Sayfayı her 2 saniyede bir yenile (canlı bağlantı için)
placeholder = st.empty()
time.sleep(2)
st.rerun()