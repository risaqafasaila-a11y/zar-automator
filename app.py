import streamlit as st
import os, asyncio, edge_tts, time, requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# --- DATABASE MUSIK ---
MUSIC_DATABASE = {
    "Santai": "https://www.chosic.com/wp-content/uploads/2021/07/The-Globe-Trotter.mp3",
    "Ceria": "https://www.chosic.com/wp-content/uploads/2021/04/Happiness.mp3",
    "Sinematik": "https://www.chosic.com/wp-content/uploads/2021/10/Inspirational-Background.mp3",
    "Teknologi": "https://www.chosic.com/wp-content/uploads/2021/07/Technology-Glitch.mp3",
    "Enerjik": "https://www.chosic.com/wp-content/uploads/2022/01/Energetic-Pop.mp3"
}

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Zar AI Video Automator", page_icon="🎬")
st.title("🎬 Zar AI Video Automator Pro")
st.markdown("Sistem Automasi Video dengan **Auto-Backsound**")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key", type="password")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    suara = st.radio("Jenis Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Gaul/Slang"])
    custom_instruksi = st.text_area("Instruksi Tambahan:", placeholder="Contoh: Gunakan bahasa Sunda...")

# --- FUNGSI HELPER ---
async def generate_vo(text, lang, gender):
    voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    if lang == "English":
        voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("temp_vo.mp3")

def download_music(url, output_path):
    r = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(r.content)

def tentukan_mood(naskah_ai):
    model = genai.GenerativeModel('gemini-3-flash-preview')
    prompt = f"Pilih satu kata mood (Santai, Ceria, Sinematik, Teknologi, atau Enerjik) untuk naskah: '{naskah_ai}'. Cukup jawab satu kata."
    res = model.generate_content(prompt)
    return res.text.strip()

# --- MAIN APP ---
uploaded_file = st.file_uploader("📤 Upload Video (MP4/MOV)", type=["mp4", "mov"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    st.video("input_video.mp4")
    
    if st.button("🚀 MULAI PROSES"):
        if not api_key:
            st.error("❌ Masukkan API Key di sidebar!")
        else:
            with st.status("Sedang memproses...", expanded=True) as status:
                try:
                    genai.configure(api_key=api_key)
                    
                    # 1. Analisis & Naskah
                    st.write("🔍 Menganalisis video...")
                    video_ai = genai.upload_file(path="input_video.mp4")
                    while video_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        video_ai = genai.get_file(video_ai.name)
                    
                    clip_v = VideoFileClip("input_video.mp4")
                    model = genai.GenerativeModel('gemini-1.5-flash-latest')
                    prompt_naskah = f"Buat naskah {bahasa} gaya {gaya}. Durasi {clip_v.duration:.1f}s. Instruksi: {custom_instruksi}. HANYA tulis narasi."
                    res = model.generate_content([prompt_naskah, video_ai])
                    naskah = res.text
                    st.write(f"✍️ Naskah: {naskah}")

                    # 2. Mood & Music
                    mood = tentukan_mood(naskah)
                    url_m = MUSIC_DATABASE.get(mood, MUSIC_DATABASE["Santai"])
                    download_music(url_m, "bgm.mp3")
                    st.write(f"🎵 Musik terpilih: {mood}")

                    # 3. Voice Over
                    asyncio.run(generate_vo(naskah, bahasa, suara))

                    # 4. Mixing
                    st.write("🎚️ Merender hasil akhir...")
                    audio_vo = AudioFileClip("temp_vo.mp3").volumex(1.5)
                    bgm = AudioFileClip("bgm.mp3").volumex(0.12).set_duration(clip_v.duration)
                    
                    final_audio = CompositeAudioClip([audio_vo, bgm])
                    final_video = clip_v.set_audio(final_audio)
                    final_video.write_videofile("hasil.mp4", codec="libx264", audio_codec="aac")
                    
                    status.update(label="✅ Selesai!", state="complete")
                    st.video("hasil.mp4")
                    with open("hasil.mp4", "rb") as f:
                        st.download_button("📥 Download Video", f, file_name="konten_ai.mp4")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
