import streamlit as st
import google.generativeai as genai
import time
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Pastikan API Key aman di Secrets
try:
    GOOGLE_API_KEY = st.secrets["AIzaSyBsw8yR1XfHSG0uzoRIe8-7dW61ubMCuQU"]
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    st.error("API Key belum diset di Streamlit Secrets!")

async def generate_voice(text, voice_name, output_path):
    communicate = edge_tts.Communicate(text, voice_name, rate="+0%")
    await communicate.save(output_path)

st.set_page_config(page_title="AI Video Automator", layout="wide")
st.title("🎬 AI Video Automator")

# --- 1. UPLOAD VIDEO ---
uploaded_file = st.file_uploader("Pilih file video (MP4/MOV)", type=['mp4', 'mov'])
video_path = "temp_video.mp4"

if uploaded_file:
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # PERBAIKAN ROTASI DI SINI
    video_clip = VideoFileClip(video_path)
    
    # Cek jika video memiliki rotasi portrait (90 atau 270 derajat)
    if video_clip.rotation in [90, 270]:
        # Tukar lebar dan tinggi agar tetap portrait
        video_clip = video_clip.resize(video_clip.size[::-1])
        video_clip.rotation = 0
    elif video_clip.rotation == 180:
        video_clip = video_clip.rotate(180)
        video_clip.rotation = 0
        
    st.video(uploaded_file)

    # --- 2. PENGATURAN ---
    col1, col2 = st.columns(2)
    with col1:
        bahasa = st.selectbox("Bahasa:", ["Indonesia", "Sunda", "Jawa", "Inggris"])
        jenis_suara = st.radio("Jenis Suara:", ["Pria", "Wanita"])
        voice_map = {"Pria": "id-ID-ArdiNeural", "Wanita": "id-ID-GadisNeural"}
    
    with col2:
        gaya = st.selectbox("Gaya Bicara:", ["Santai", "Dramatis", "Formal", "Energetik"])
        kategori = st.selectbox("Tujuan Video:", ["Review Produk", "Motivasi", "Vlog", "Sinematik"])

    create_btn = st.button("🚀 GENERATE VIDEO")

    if create_btn:
        durasi_video = video_clip.duration
        
        try:
            with st.spinner("🤖 AI sedang memproses..."):
                video_ai = genai.upload_file(path=video_path)
                while video_ai.state.name == "PROCESSING":
                    time.sleep(2)
                    video_ai = genai.get_file(video_ai.name)

                model = genai.GenerativeModel("gemini-3-flash-preview")
                prompt = f"Buat narasi {kategori} dalam {bahasa} gaya {gaya}. Durasi {durasi_video} detik."
                
                response = model.generate_content([video_ai, prompt])
                naskah = response.text.replace('"', '').strip()
                
                st.write("**Naskah AI:**", naskah)
                
                # Suara
                asyncio.run(generate_voice(naskah, voice_map[jenis_suara], "vo.mp3"))
                audio_clip = AudioFileClip("vo.mp3")
                
                # Gabungkan Audio & Video
                audio_final = CompositeAudioClip([audio_clip.set_start(0)]).set_duration(durasi_video)
                final_video = video_clip.set_audio(audio_final)
                
                # PENTING: Gunakan preset 'medium' agar metadata tersimpan dengan baik
                final_video.write_videofile("final_output.mp4", codec="libx264", audio_codec="aac", fps=24)

                st.success("✅ Video Selesai!")
                st.video("final_output.mp4")
                
                with open("final_output.mp4", "rb") as file:
                    st.download_button("📥 Download Video Hasil", file, "hasil_video.mp4")
        
        except Exception as e:
            st.error(f"Error: {e}")
