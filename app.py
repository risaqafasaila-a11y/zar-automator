import streamlit as st
import os, asyncio, edge_tts, time, requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# --- DATABASE MUSIK PUBLIK (Bebas Hak Cipta) ---
# Mas Fazar bisa menambah link MP3 publik lainnya di sini
MUSIC_BANK = {
    "Santai": "https://www.chosic.com/wp-content/uploads/2021/07/The-Globe-Trotter.mp3",
    "Ceria": "https://www.chosic.com/wp-content/uploads/2021/04/Happiness.mp3",
    "Sinematik": "https://www.chosic.com/wp-content/uploads/2021/10/Inspirational-Background.mp3",
    "Teknologi/Modern": "https://www.chosic.com/wp-content/uploads/2021/07/Technology-Glitch.mp3",
    "Sedih/Emosional": "https://www.chosic.com/wp-content/uploads/2021/05/Lonely-Day.mp3"
}

def download_music(url, output_path):
    r = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(r.content)

# --- FUNGSI PILIH MOOD OLEH GEMINI ---
def tentukan_mood(naskah_ai):
    prompt_mood = f"Berdasarkan naskah ini: '{naskah_ai}', pilih satu mood musik yang paling cocok: Santai, Ceria, Sinematik, Teknologi, atau Sedih. Cukup jawab satu kata saja."
    model = genai.GenerativeModel('gemini-3-flash-preview')
    response = model.generate_content(prompt_mood)
    return response.text.strip()

# (Bagian Sidebar & Setup tetap sama)
# ... [Kode Sidebar Mas Fazar sebelumnya] ...

# --- PROSES EKSEKUSI ---
if st.button("Mulai Proses Video"):
    with st.status("AI sedang bekerja...") as status:
        # 1. Gemini buat naskah & tentukan mood
        # ... (Proses Gemini seperti biasa) ...
        naskah = res.text
        mood_terpilih = tentukan_mood(naskah)
        st.write(f"🎭 Mood Terdeteksi: {mood_terpilih}")

        # 2. Download Musik Otomatis
        url_musik = MUSIC_BANK.get(mood_terpilih, MUSIC_BANK["Santai"])
        st.write("🎵 Mengambil musik latar yang sesuai...")
        download_music(url_musik, "bgm.mp3")

        # 3. Mixing Audio
        audio_vo = AudioFileClip("temp_vo.mp3").volumex(1.6)
        bgm = AudioFileClip("bgm.mp3").volumex(0.12).set_duration(clip_v.duration)
        
        final_audio = CompositeAudioClip([audio_vo, bgm])
        
        # 4. Render Final
        final_video = clip_v.set_audio(final_audio)
        final_video.write_videofile("hasil_otomatis.mp4", codec="libx264")
        
        st.video("hasil_otomatis.mp4")
