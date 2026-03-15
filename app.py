import streamlit as st
import os, asyncio, edge_tts, time
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="AI Video Automator", page_icon="🎬")

st.title("🎬 AI Video Automator")
st.markdown("Buat naskah dan voice over otomatis berdasarkan visual video.")

# --- SIDEBAR PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.subheader("🎙️ Pengaturan Suara")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    suara = st.radio("Jenis Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Formal", "Gaul/Slang"])
    
    st.subheader("📝 Instruksi Tambahan")
    custom_instruksi = st.text_area("Tambahkan instruksi khusus (opsional):", 
                                    placeholder="Contoh: Jangan pakai kata 'Guys', atau sebutkan nama produknya...")

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
                    # 1. Konfigurasi Gemini
                    genai.configure(api_key=api_key)
                    
                    st.write("Menganalisis konten video...")
                    video_ai = genai.upload_file(path="input_video.mp4")
                    while video_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        video_ai = genai.get_file(video_ai.name)
                    
                    # 2. Hitung Durasi
                    clip_temp = VideoFileClip("input_video.mp4")
                    durasi = clip_temp.duration
                    limit_kata = int(durasi * 1.8) # Estimasi kecepatan bicara manusia
                    clip_temp.close()

                    # 3. Buat Prompt (Bersih dari Brand Otomatis)
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    
                    prompt = (
                        f"Tonton video ini. Buat naskah voice over dalam {bahasa} dengan gaya {gaya}. "
                        f"Durasi video adalah {durasi:.1f} detik, jadi naskah maksimal {limit_kata} kata. "
                        f"Ceritakan apa yang terjadi di video secara mengalir. "
                        f"Instruksi tambahan: {custom_instruksi if custom_instruksi else 'Langsung ke inti konten.'} "
                        f"HANYA berikan teks narasi yang akan dibaca narator."
                    )
                    
                    res = model.generate_content([prompt, video_ai])
                    naskah = res.text
                    
                    st.write("Naskah dihasilkan: " + naskah)
                    
                    # 4. Generate Voice Over
                    st.write("Menghasilkan suara AI...")
                    asyncio.run(generate_vo(naskah.replace(". ", "... "), bahasa, suara))
                    
                    # 5. Gabungkan Audio & Video (Render)
                    st.write("Merender video akhir...")
                    v_clip = VideoFileClip("input_video.mp4")
                    a_clip = AudioFileClip("temp_vo.mp3")
                    
                    # Pastikan audio tidak lebih panjang dari video
                    final_audio = a_clip.subclip(0, v_clip.duration) if a_clip.duration > v_clip.duration else a_clip
                    final_video = v_clip.set_audio(final_audio)
                    
                    final_video.write_videofile("hasil_akhir.mp4", codec="libx264", audio_codec="aac")
                    
                    status.update(label="✅ Selesai!", state="complete", expanded=False)
                    
                    st.success("Video siap didownload!")
                    st.video("hasil_akhir.mp4")
                    with open("hasil_akhir.mp4", "rb") as f:
                        st.download_button("⬇️ Download Video Hasil", f, file_name="konten_ai.mp4")
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("💡 Silakan upload video untuk memulai.")
