import streamlit as st
from VideoProcessor import VideoProcessor
from textToISL import text_to_vid
import os

os.makedirs('temp_outputs', exist_ok=True)

def main():
    st.set_page_config(page_title = "Video to Sign Language Converter", page_icon="🎥")
    st.title("🎥 Video to Sign Language Converter")

    st.sidebar.header("Input Options")
    input_type=st.sidebar.selectbox("Choose input type:", ["YouTube URL", "Local Video/Audio File", "Text Input"])

    st.sidebar.markdown("---")
    st.sidebar.text("Developed by Nooglers")

    if input_type == "YouTube URL":
        st.write("")
        st.write("")
        st.header("Process YouTube URL")
        youtube_url = st.text_input("Enter YouTube URL:")
        if st.button("Process YouTube URL"):
            if youtube_url:
                st.write(f"Processing YouTube video from URL: {youtube_url}")
                progress_bar = st.progress(0)

                processor = VideoProcessor()
                progress_bar.progress(10)
                transcript = processor.process_video(youtube_url)
                progress_bar.progress(60)

                text_to_vid(transcript)
                progress_bar.progress(100)

                st.subheader("Transcript:")
                st.write(transcript)

                st.subheader("Converted Sign Language Video:")
                st.video("temp_outputs\\merged.mp4")
            else:
                st.error("Please enter a valid YouTube URL")

    elif input_type == "Local Video/Audio File":
        st.write("")
        st.write("")
        st.header("Upload Local Video/Audio File")
        uploaded_file = st.file_uploader("Upload a video or audio file", type=["mp4", "mov", "avi", "wav"])

        if uploaded_file is not None:
            file_path = f"temp_outputs\\temp_file.{uploaded_file.name.split('.')[-1]}"

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.video(uploaded_file)

            if st.button("Process Uploaded File"):
                progress_bar = st.progress(0)

                processor = VideoProcessor()
                progress_bar.progress(10)
                transcript = processor.process_video(file_path)
                progress_bar.progress(60)

                text_to_vid(transcript)
                progress_bar.progress(100)

                st.subheader("Transcript:")
                st.write(transcript)

                st.subheader("Converted Sign Language Video:")
                st.video("temp_outputs\\merged.mp4")

    elif input_type == "Text Input":
        st.write("")
        st.write("")
        st.header("Enter Text for Conversion")
        user_text = st.text_area("Enter text:")

        if st.button("Process Text"):
            if user_text:
                st.write("Processing text input")
                progress_bar = st.progress(0)

                text_to_vid(user_text)
                progress_bar.progress(100)

                st.subheader("Converted Sign Language Video:")
                st.video("temp_outputs\\merged.mp4")
                
            else:
                st.error("Please enter some text")

if __name__ == "__main__":
    main()
