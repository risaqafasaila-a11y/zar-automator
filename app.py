import streamlit as st
import os, asyncio, edge_tts, time, requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# --- DATABASE MUSIK ---
MUSIC_DATABASE = {
    "Santai": "https://www.chosic.com/wp-content/uploads/2021/07/The-Globe-Trotter.mp3",
    "Ceria": "https://www.chosic.com/wp-content/uploads/2021/04/Happiness.mp3",
    "Sinematik": "https://www.chosic.com/wp-content/uploads/2021/10/Inspirational-Background.mp3",
    "Teknologi": "https://www.chosic.com/wp-content/uploads/2021/07/Technology-Glitch.mp3"
}

st.set_page_config(page_title="Zar AI Video Automator", page_icon="🎬")
st.title("🎬 Zar AI Video Automator + Reziser")

with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.subheader("📺 Format Video")
    # Fitur Baru: Pilih Resolusi
    format_video = st.radio("Pilih Resolusi Akhir:", ["Asli", "Portrait (9:16)", "Landscape (16:9)"])
    
    st.subheader("🎙️ Pengaturan Suara")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    suara = st.radio("Jenis Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Gaul/Slang"])
    custom_instruksi = st.text_area("Instruksi Tambahan:")

# --- FUNGSI HELPER ---
async def generate_vo(text, lang, gender):
    voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    if lang == "English": voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("temp_vo.mp3")

def download_music(url, output_path):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(output_path, 'wb') as f: f.write(r.content)
            return True
    except: return False
    return False

# --- PROSES VIDEO ---
uploaded_file = st.file_uploader("📤 Upload Video", type=["mp4", "mov"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f: f.write(uploaded_file.read())
    
    if st.button("🚀 MULAI PROSES"):
        with st.status("Memproses video...") as status:
            try:
                genai.configure(api_key=api_key)
                video_ai = genai.upload_file(path="input_video.mp4")
                while video_ai.state.name == "PROCESSING":
                    time.sleep(2)
                    video_ai = genai.get_file(video_ai.name)
                
                clip_v = VideoFileClip("input_video.mp4")
                
                # --- LOGIKA RESIZE ---
                if format_video == "Portrait (9:16)":
                    # Resize untuk TikTok/Reels (biasanya 1080x1920)
                    clip_v = clip_v.resize(height=1920)
                    clip_v = clip_v.crop(x_center=clip_v.w/2, y_center=clip_v.h/2, width=1080, height=1920)
                elif format_video == "Landscape (16:9)":
                    # Resize untuk YouTube (biasanya 1920x1080)
                    clip_v = clip_v.resize(width=1920)
                    clip_v = clip_v.crop(x_center=clip_v.w/2, y_center=clip_v.h/2, width=1920, height=1080)

                # Pembuatan Naskah & Musik (Sama seperti sebelumnya)
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                prompt = f"Buat naskah {bahasa} gaya {gaya}. Durasi {clip_v.duration:.1f}s. {custom_instruksi}"
                res = model.generate_content([prompt, video_ai])
                naskah = res.text
                
                asyncio.run(generate_vo(naskah, bahasa, suara))
                
                # Mixing Audio
                audio_vo = AudioFileClip("temp_vo.mp3").volumex(1.5)
                # (Logika download musik tetap sama)
                download_music(MUSIC_DATABASE["Santai"], "bgm.mp3")
                bgm = AudioFileClip("bgm.mp3").volumex(0.12).set_duration(clip_v.duration)
                
                final_audio = CompositeAudioClip([audio_vo, bgm])
                final_video = clip_v.set_audio(final_audio)
                
                final_video.write_videofile("hasil_resolusi.mp4", codec="libx264")
                st.video("hasil_resolusi.mp4")
                
            except Exception as e:
                st.error(f"Error: {e}")
