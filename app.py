import streamlit as st
import os, asyncio, edge_tts, time, requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# --- 1. DATABASE LINK MUSIK (Bebas Hak Cipta) ---
# Sistem akan mendownload musik ini secara otomatis sesuai mood naskah
MUSIC_DATABASE = {
    "Santai": "https://www.chosic.com/wp-content/uploads/2021/07/The-Globe-Trotter.mp3",
    "Ceria": "https://www.chosic.com/wp-content/uploads/2021/04/Happiness.mp3",
    "Sinematik": "https://www.chosic.com/wp-content/uploads/2021/10/Inspirational-Background.mp3",
    "Teknologi": "https://www.chosic.com/wp-content/uploads/2021/07/Technology-Glitch.mp3",
    "Enerjik": "https://www.chosic.com/wp-content/uploads/2022/01/Energetic-Pop.mp3"
}

# --- 2. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Zar AI Video Automator", page_icon="🎬", layout="wide")
st.title("🎬 AI Video Automator Pro")
st.markdown("Sistem automasi video dengan **Auto-Mood Music Detection**.")

# --- 3. SIDEBAR PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.subheader("🎙️ Pengaturan Suara")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    suara = st.radio("Jenis Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Formal", "Gaul/Slang"])
    
    st.subheader("📝 Instruksi Tambahan")
    custom_instruksi = st.text_area("Instruksi khusus:", placeholder="Misal: Gunakan logat Sunda, atau jangan terlalu cepat...")

# --- 4. FUNGSI PENDUKUNG ---
async def generate_vo(text, lang, gender):
    """Menghasilkan suara AI (Voice Over)"""
    voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    if lang == "English":
        voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("temp_vo.mp3")

def download_music(url, output_path):
    """Mengunduh musik latar dari internet"""
    r = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(r.content)

def tentukan_mood(naskah_ai):
    """Gemini menentukan mood musik berdasarkan naskah"""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt_mood = f"Pilih satu kata mood (Santai, Ceria, Sinematik, Teknologi, atau Enerjik) yang paling cocok untuk naskah ini: '{naskah_ai}'. Cukup jawab satu kata saja."
    response = model.generate_content(prompt_mood)
    return response.text.strip()

# --- 5. AREA UTAMA ---
uploaded_file = st.file_uploader("📤 Upload Video (MP4/MOV)", type=["mp4", "mov"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("Pratinjau Video Asli")
        st.video("input_video.mp4")
    
    if st.button("🚀 MULAI PROSES AUTOMASI"):
        if not api_key:
            st.error("❌ Mohon masukkan Gemini API Key di sidebar!")
        else:
            with st.status("Sedang memproses video...", expanded=True) as status:
                try:
                    # A. Analisis Video dengan Gemini
                    genai.configure(api_key=api_key)
                    st.write("🔍 Gemini sedang menganalisis visual video...")
                    video_ai = genai.upload_file(path="input_video.mp4")
                    while video_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        video_ai = genai.get_file(video_ai.name)
                    
                    clip_v = VideoFileClip("input_video.mp4")
                    durasi = clip_v.duration
                    limit_kata = int(durasi * 1.8)

                    # B. Buat Naskah
                    st.write("✍️ Menyusun naskah narasi...")
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt_naskah = f"Buat naskah {bahasa} gaya {gaya}. Durasi {durasi:.1f}s. Maks {limit_kata} kata. Instruksi khusus: {custom_instruksi}. HANYA tulis narasi."
                    res = model.generate_content([prompt_naskah, video_ai])
                    naskah = res.text
                    
                    with col2:
                        st.success(f"Naskah AI ({bahasa}):")
                        st.write(naskah)

                    # C. Tentukan & Download Musik
                    st.write("🎵 Memilih musik latar yang pas...")
                    mood = tentukan_mood(naskah)
                    url_musik = MUSIC_DATABASE.get(mood, MUSIC_DATABASE["Santai"])
                    download_music(url_musik, "bgm.mp3")
                    st.write(f"✅ Mood terpilih: **{mood}**")

                    # D. Generate Voice Over
                    st.write("🎙️ Membuat suara narasi...")
                    asyncio.run(generate_vo(naskah.replace(". ", "... "), bahasa, suara))

                    # E. Mixing Audio (Narasi + Musik)
                    st.write("🎚️ Menggabungkan audio dan video...")
                    audio_vo = AudioFileClip("temp_vo.mp3").volumex(1.6) # Suara AI lebih keras
                    bgm = AudioFileClip("bgm.mp3").volumex(0.12).set_duration(clip_v.duration) # Musik pelan (12%)
                    
                    final_audio = CompositeAudioClip([audio_vo, bgm])
                    final_video = clip_v.set_audio(final_audio)
                    
                    # F. Render Final
                    output_file = "hasil_final_zar_ai.mp4"
                    final_video.write_videofile(output_file, codec="libx264", audio_codec="aac")
                    
                    status.update(label="✅ Video Berhasil Dibuat!", state="complete")
                    
                    st.divider()
                    st.balloons()
                    st.subheader("🎬 Hasil Video Akhir")
                    st.video(output_file)
                    with open(output_file, "rb") as f:
                        st.download_button("📥 Download Video Sekarang", f, file_name=output_file)
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan teknis: {e}")
else:
    st.info("Menunggu video diunggah untuk memulai automasi.")

# --- 6. FOOTER ---
st.markdown("---")
st.caption("Dikembangkan untuk automasi konten multimedia cerdas.")
