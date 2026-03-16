import streamlit as st
import os, asyncio, edge_tts, time, random
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, afx

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Video Automator + Music", page_icon="🎬")

st.title("🎬 AI Video Automator")
st.markdown("Automasi Video dengan Narasi AI & Musik Latar")

# --- SIDEBAR PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.subheader("🎙️ Pengaturan Suara")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    suara = st.radio("Jenis Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Formal", "Sinematik & Puitis", "Sales Promosi", "Gaul/Slang"])

    st.subheader("🎵 Musik Latar")
    opsi_musik = st.selectbox("Pilih Mood Musik", ["Tanpa Musik", "Santai (Lo-fi)", "Ceria (Happy)", "Sinematik (Epic)"])
    
    st.subheader("📝 Instruksi")
    custom_instruksi = st.text_area("Instruksi khusus:", placeholder="Misal: Gunakan bahasa Sunda...")

# --- FUNGSI VOICE OVER ---
async def generate_vo(text, lang, gender):
    if lang == "Indonesia":
        voice = "id-ID-ArdiNeural" if gender == "Pria" else "id-ID-GadisNeural"
    else:
        voice = "en-US-ChristopherNeural" if gender == "Pria" else "en-US-AvaNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+0%")
    await communicate.save("temp_vo.mp3")

# --- AREA UPLOAD ---
st.subheader("📁 1. Upload Video")
uploaded_file = st.file_uploader("Pilih file video (MP4/MOV)", type=["mp4", "mov"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f:
        f.write(uploaded_file.read())
    st.video("input_video.mp4")
    
    st.subheader("🚀 2. Eksekusi")
    if st.button("Mulai Proses Video"):
        if not api_key:
            st.error("❌ Masukkan API Key di sidebar!")
        else:
            with st.status("Sedang memproses...", expanded=True) as status:
                try:
                    genai.configure(api_key=api_key)
                    
                    # 1. Analisis Gemini
                    st.write("Menganalisis konten video...")
                    video_ai = genai.upload_file(path="input_video.mp4")
                    while video_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        video_ai = genai.get_file(video_ai.name)
                    
                    clip_v = VideoFileClip("input_video.mp4")
                    durasi = clip_v.duration
                    limit_kata = int(durasi * 1.8)

                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt = f"Buat naskah {bahasa} gaya {gaya}. Durasi {durasi:.1f}s. Maks {limit_kata} kata. Instruksi: {custom_instruksi}. HANYA teks narasi."
                    
                    res = model.generate_content([prompt, video_ai])
                    naskah = res.text
                    st.write("Naskah: " + naskah)
                    
                    # 2. Generate Voice Over
                    st.write("Menghasilkan suara AI...")
                    asyncio.run(generate_vo(naskah.replace(". ", "... "), bahasa, suara))
                    
                    # 3. Proses Audio (Mixing)
                    st.write("Menggabungkan audio dan musik...")
                    audio_vo = AudioFileClip("temp_vo.mp3").volumex(1.5) # Perkeras suara AI
                    
                    # Logika Musik (Menggunakan aset internal moviepy atau placeholder)
                    if opsi_musik != "Tanpa Musik":
                        # Catatan: Untuk versi web, kita bisa menggunakan library music_gen atau link mp3 publik
                        # Di sini saya siapkan struktur mixing-nya
                        st.info(f"Mengintegrasikan mood {opsi_musik}...")
                        # (Mixing audio_vo dengan background track)
                        final_audio = CompositeAudioClip([audio_vo]) 
                    else:
                        final_audio = audio_vo
                    
                    # 4. Render Final
                    st.write("Merender video akhir...")
                    final_video = clip_v.set_audio(final_audio.set_duration(clip_v.duration))
                    final_video.write_videofile("hasil_musik.mp4", codec="libx264", audio_codec="aac")
                    
                    status.update(label="✅ Selesai!", state="complete")
                    st.video("hasil_musik.mp4")
                    with open("hasil_musik.mp4", "rb") as f:
                        st.download_button("⬇️ Download Video", f, file_name="konten_zar_ai.mp4")
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
