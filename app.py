import streamlit as st
import os, asyncio, edge_tts, time
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Zar's Video Automator", page_icon="🎥")

st.title("🎥 Zar's Video Automator")
st.markdown("Automasi konten untuk **Zar's Diecast Garage**")

# --- SIDEBAR PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Gemini API Key", type="password", help="Dapatkan API Key di Google AI Studio")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    platform = st.selectbox("Platform", ["YouTube", "TikTok", "Instagram", "Facebook"])
    tujuan = st.selectbox("Tujuan Konten", ["Review Produk", "Bercerita Trending Topic", "Storytelling Santai"])
    suara = st.radio("Pilihan Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Gaul/Slang"])

# --- FUNGSI VOICE OVER ---
async def generate_vo(text, lang, gender):
    if lang == "Indonesia":
        voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    else:
        voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save("temp_vo.mp3")

# --- AREA UTAMA: UPLOAD VIDEO ---
st.subheader("📁 1. Upload Video")
uploaded_file = st.file_uploader("Pilih file video (MP4/MOV)", type=["mp4", "mov"])

if uploaded_file:
    # Simpan file sementara
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    
    # Tampilkan Preview Video
    st.video("input_video.mp4")
    
    st.subheader("🚀 2. Eksekusi")
    if st.button("Mulai Proses Video"):
        if not api_key:
            st.error("❌ Silakan masukkan Gemini API Key di sidebar sebelah kiri!")
        else:
            with st.status("Sedang bekerja...", expanded=True) as status:
                try:
                    # Konfigurasi Gemini
                    genai.configure(api_key=api_key)
                    
                    st.write("Analisis video oleh Gemini...")
                    video_ai = genai.upload_file(path="input_video.mp4")
                    while video_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        video_ai = genai.get_file(video_ai.name)
                    
                    # Hitung durasi
                    clip_temp = VideoFileClip("input_video.mp4")
                    durasi = clip_temp.duration
                    limit_kata = int(durasi * 1.8)
                    clip_temp.close()

                    # Buat Naskah
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    cta = "subscribe dan like" if platform == "YouTube" else "follow dan like"
                    prompt = (
    f"Tonton video ini dan buatkan naskah voice over dalam {bahasa} dengan gaya {gaya}. "
    f"Tujuan konten adalah {tujuan}. "
    f"Durasi video {durasi:.1f} detik, jadi naskah tidak boleh lebih dari {limit_kata} kata. "
    f"Fokuslah hanya pada pembahasan apa yang terlihat di video secara alami. "
    f"TIDAK PERLU menyebutkan nama brand atau kalimat penutup promosi otomatis. "
    f"HANYA berikan teks narasi yang akan dibaca langsung."
)
                    
                    prompt = f"Buat naskah {bahasa} gaya {gaya}. Tujuan: {tujuan}. Durasi video {durasi:.1f} detik. Maksimal {limit_kata} kata. Sebutkan brand {brand} dan akhiri dengan CTA: {cta}. HANYA tulis narasi saja."
                    
                    res = model.generate_content([prompt, video_ai])
                    naskah = res.text
                    
                    st.write("Menghasilkan suara AI...")
                    asyncio.run(generate_vo(naskah.replace(". ", "... "), bahasa, suara))
                    
                    st.write("Menggabungkan video dan audio...")
                    v_clip = VideoFileClip("input_video.mp4")
                    a_clip = AudioFileClip("temp_vo.mp3")
                    final_audio = a_clip.subclip(0, v_clip.duration) if a_clip.duration > v_clip.duration else a_clip
                    final_video = v_clip.set_audio(final_audio)
                    
                    output_name = f"hasil_{platform.lower()}.mp4"
                    final_video.write_videofile(output_name, codec="libx264", audio_codec="aac")
                    
                    status.update(label="✅ Selesai!", state="complete", expanded=False)
                    
                    st.success("Video Anda sudah siap!")
                    st.video(output_name)
                    with open(output_name, "rb") as f:
                        st.download_button("⬇️ Download Video Hasil", f, file_name=output_name)
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("💡 Silakan upload video terlebih dahulu untuk memunculkan tombol proses.")
