import streamlit as st
import os, asyncio, edge_tts, time, requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip

# --- KONFIGURASI ---
MUSIC_DATABASE = {
    "Santai": "https://www.chosic.com/wp-content/uploads/2021/07/The-Globe-Trotter.mp3",
    "Ceria": "https://www.chosic.com/wp-content/uploads/2021/04/Happiness.mp3",
    "Sinematik": "https://www.chosic.com/wp-content/uploads/2021/10/Inspirational-Background.mp3",
    "Teknologi": "https://www.chosic.com/wp-content/uploads/2021/07/Technology-Glitch.mp3"
}

st.set_page_config(page_title="Zar AI Video Automator", page_icon="🎬")
st.title("🎬 Zar AI Video Automator + Subtitle")

with st.sidebar:
    st.header("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key", type="password")
    bahasa = st.selectbox("Bahasa", ["Indonesia", "English"])
    suara = st.radio("Jenis Suara", ["Pria", "Wanita"])
    gaya = st.selectbox("Gaya Bicara", ["Santai", "Seru & Enerjik", "Gaul/Slang"])
    show_subtitle = st.checkbox("Tampilkan Subtitle", value=True)
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

# --- MAIN APP ---
uploaded_file = st.file_uploader("📤 Upload Video", type=["mp4", "mov"])

if uploaded_file:
    with open("input_video.mp4", "wb") as f: f.write(uploaded_file.read())
    st.video("input_video.mp4")
    
    if st.button("🚀 MULAI PROSES"):
        if not api_key: st.error("AIzaSyBsw8yR1XfHSG0uzoRIe8-7dW61ubMCuQU")
        else:
            with st.status("Sedang memproses...", expanded=True) as status:
                try:
                    genai.configure(api_key=api_key)
                    st.write("🔍 Menganalisis video...")
                    video_ai = genai.upload_file(path="input_video.mp4")
                    while video_ai.state.name == "PROCESSING":
                        time.sleep(2)
                        video_ai = genai.get_file(video_ai.name)
                    
                    clip_v = VideoFileClip("input_video.mp4")
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt_naskah = f"Buat naskah {bahasa} gaya {gaya}. Durasi {clip_v.duration:.1f}s. {custom_instruksi}. HANYA tulis narasi."
                    res = model.generate_content([prompt_naskah, video_ai])
                    naskah = res.text
                    
                    # 1. Generate Voice Over
                    st.write("🎙️ Menghasilkan suara...")
                    asyncio.run(generate_vo(naskah, bahasa, suara))
                    audio_vo = AudioFileClip("temp_vo.mp3").volumex(1.8)

                    # 2. Proses Musik
                    st.write("🎵 Menyiapkan musik...")
                    res_mood = model.generate_content(f"Pilih satu kata mood (Santai, Ceria, Sinematik, atau Teknologi) untuk naskah ini: {naskah}")
                    mood = res_mood.text.strip()
                    url_m = MUSIC_DATABASE.get(mood, MUSIC_DATABASE["Santai"])
                    download_music(url_m, "bgm.mp3")
                    
                    if os.path.exists("bgm.mp3"):
                        bgm = AudioFileClip("bgm.mp3").volumex(0.12).set_duration(clip_v.duration)
                        final_audio = CompositeAudioClip([audio_vo, bgm])
                    else:
                        final_audio = audio_vo

                    # 3. Proses Subtitle (JIKA DICENTANG)
                    st.write("📝 Menambahkan subtitle...")
                    video_final = clip_v.set_audio(final_audio.set_duration(clip_v.duration))
                    
                    if show_subtitle:
                        # Membuat teks subtitle sederhana (satu blok teks untuk seluruh video)
                        txt_clip = TextClip(naskah, fontsize=24, color='white', font='Arial-Bold', 
                                            method='caption', size=(clip_v.w*0.8, None), 
                                            bg_color='black').set_duration(clip_v.duration).set_position(('center', 'bottom'))
                        video_final = CompositeVideoClip([video_final, txt_clip])

                    # 4. Render
                    st.write("🎚️ Merender hasil akhir...")
                    video_final.write_videofile("hasil_sub.mp4", codec="libx264", audio_codec="aac")
                    
                    status.update(label="✅ Selesai!", state="complete")
                    st.video("hasil_sub.mp4")
                    with open("hasil_sub.mp4", "rb") as f:
                        st.download_button("📥 Download", f, file_name="video_subtitle.mp4")
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
