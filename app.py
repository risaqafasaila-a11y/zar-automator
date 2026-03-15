import os
import subprocess
import sys

# --- TRIK PAKSA INSTALASI ---
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ImportError:
    install('moviepy')
    from moviepy.editor import VideoFileClip, AudioFileClip

try:
    import google.generativeai as genai
except ImportError:
    install('google-generativeai')
    import google.generativeai as genai

try:
    import edge_tts
except ImportError:
    install('edge-tts')
    import edge_tts

import streamlit as st
import asyncio
import time

# --- LANJUTAN KODE STREAMLIT ---
st.set_page_config(page_title="Zar's Video Automator", page_icon="🎥")

st.title("🎥 Zar's Video Automator")
st.markdown("Automasi konten untuk Zar's Diecast Garage")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Gemini API Key", type="password")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    platform = st.selectbox("Platform", ["YouTube", "TikTok", "Instagram", "Facebook"])
    tujuan = st.selectbox("Tujuan Konten", ["Review Produk", "Bercerita Trending Topic", "Storytelling Santai"])
    suara = st.radio("Pilihan Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Gaul/Slang"])

# Fungsi VO
async def generate_vo(text, lang, gender):
    if lang == "Indonesia":
        voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    else:
        voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save("temp_vo.mp3")

uploaded_file = st.file_uploader("Upload Video (MP4)", type=["mp4", "mov"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    st.video("input_video.mp4")
    
    if st.button("🚀 Mulai Proses"):
        if not api_key:
            st.error("Isi API Key dulu di sidebar!")
        else:
            with st.spinner("Sedang memproses video..."):
                genai.configure(api_key=api_key)
                # Logika Brand & CTA
                cta = "subscribe dan like" if platform == "YouTube" else "follow dan like"
                brand = "Zar's Diecast Garage" if tujuan != "Review Produk" else "Rekomendasi Barang Berguna"
                
                # Proses Gemini
                video_ai = genai.upload_file(path="input_video.mp4")
                while video_ai.state.name == "PROCESSING":
                    time.sleep(2)
                    video_ai = genai.get_file(video_ai.name)
                
                clip = VideoFileClip("input_video.mp4")
                durasi = clip.duration
                model = genai.GenerativeModel('gemini-3-flash-preview')
                prompt = f"Buat naskah {bahasa} gaya {gaya}. Tujuan: {tujuan}. Durasi {durasi:.1f}s. Sebut {brand} dan CTA: {cta}."
                
                res = model.generate_content([prompt, video_ai])
                naskah = res.text
                
                # Generate VO
                asyncio.run(generate_vo(naskah.replace(". ", "... "), bahasa, suara))
                
                # Render
                v_clip = VideoFileClip("input_video.mp4")
                a_clip = AudioFileClip("temp_vo.mp3")
                final = v_clip.set_audio(a_clip.subclip(0, v_clip.duration) if a_clip.duration > v_clip.duration else a_clip)
                final.write_videofile("output.mp4", codec="libx264", audio_codec="aac")
                
                st.success("Video Berhasil Dibuat!")
                st.video("output.mp4")
                with open("output.mp4", "rb") as f:
                    st.download_button("⬇️ Download Video", f, file_name="konten_zar.mp4")
