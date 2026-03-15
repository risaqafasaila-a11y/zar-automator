import streamlit as st
import os, asyncio, edge_tts, time
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Zar's Video Automator", page_icon="🎥", layout="centered")

st.title("🎥 Zar's Video Automator")
st.markdown("Ubah video unboxing menjadi konten viral dalam hitungan detik.")

# --- SIDEBAR PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Gemini API Key", type="password")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    platform = st.selectbox("Platform", ["YouTube", "TikTok", "Instagram", "Facebook"])
    tujuan = st.selectbox("Tujuan Konten", ["Review Produk", "Bercerita Trending Topic", "Storytelling Santai"])
    suara = st.radio("Pilihan Suara", ["Pria", "Wanita"])
    gaya = st.select_slider("Gaya Bicara", options=["Santai", "Seru & Enerjik", "Gaul/Slang"])

# --- FUNGSI UTAMA ---
async def generate_vo(text, lang, gender):
    if lang == "Indonesia":
        voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    else:
        voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save("temp_vo.mp3")

# --- AREA UPLOAD ---
uploaded_file = st.file_uploader("Upload Video Anda (MP4)", type=["mp4", "mov"])

if uploaded_file is not None:
    # Simpan file sementara
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    st.video("input_video.mp4")
    
    if st.button("🚀 Mulai Proses Video"):
        if not api_key:
            st.error("Masukkan API Key terlebih dahulu!")
        else:
            with st.status("Sedang memproses..."):
                # 1. Analisis Gemini
                genai.configure(api_key=api_key)
                clip = VideoFileClip("input_video.mp4")
                durasi = clip.duration
                limit_kata = int(durasi * 1.8)
                clip.close()

                st.write("> Gemini sedang menganalisis video...")
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # Logika CTA & Brand
                cta = "subscribe dan like" if platform == "YouTube" else "follow dan like"
                brand = "Zar's Diecast Garage" if tujuan != "Review Produk" else "Rekomendasi Barang Berguna"
                
                prompt = f"Tonton video ini. Buat naskah {bahasa} gaya {gaya}. Tujuan: {tujuan}. Durasi {durasi:.1f}s. Maks {limit_kata} kata. Sebut {brand} dan CTA: {cta}. HANYA teks narasi."
                
                # Proses Video (Memerlukan instalasi manual library di server)
                video_ai = genai.upload_file(path="input_video.mp4")
                while video_ai.state.name == "PROCESSING":
                    time.sleep(2)
                    video_ai = genai.get_file(video_ai.name)
                
                res = model.generate_content([prompt, video_ai])
                naskah = res.text
                
                st.write("> Menghasilkan Voice Over...")
                asyncio.run(generate_vo(naskah.replace(". ", "... "), bahasa, suara))
                
                st.write("> Merender Video Akhir...")
                v_clip = VideoFileClip("input_video.mp4")
                a_clip = AudioFileClip("temp_vo.mp3")
                final = v_clip.set_audio(a_clip.subclip(0, v_clip.duration) if a_clip.duration > v_clip.duration else a_clip)
                final.write_videofile("output_web.mp4", codec="libx264", audio_codec="aac")
                
            st.success("Selesai!")
            st.video("output_web.mp4")
            with open("output_web.mp4", "rb") as f:
                st.download_button("⬇️ Download Video Hasil", f, file_name=f"konten_{platform}.mp4")
