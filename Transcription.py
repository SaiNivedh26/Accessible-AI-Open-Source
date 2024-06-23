# Get your credential details as JSON file corresponding to your Project from Google Cloud Platform ( make sure Speech to text API enabled )
# Get your Bucket Storage details corresponding to your Project from Google cloud Platform

import streamlit as st
import os
import subprocess
from google.cloud import speech_v1
import io
import yt_dlp as youtube_dl
from google.cloud import speech
from google.oauth2 import service_account
from google.cloud import storage
import soundfile as sf
from pydub import AudioSegment

class VideoProcessor:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file("C:\\Users\\saini\\Downloads\\google_credentials.json")
        self.client = speech_v1.SpeechClient(credentials=credentials)
        self.storage_client = storage.Client(credentials=credentials)
        self.bucket_name = "sign-language-1"
        self.ffmpeg_path = 'C:\\ffmpeg-2024-06-21-git-d45e20c37b-full_build\\ffmpeg-2024-06-21-git-d45e20c37b-full_build\\bin\\ffmpeg.exe'

    def download_youtube_audio(self, youtube_url: str, audio_path: str):
        """Download audio from YouTube video."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': audio_path.replace('.wav', ''),
            'ffmpeg_location': self.ffmpeg_path,
            'postprocessor_args': [
                '-ac', '1'  # This argument tells FFmpeg to output mono audio
            ],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        print(f"Audio downloaded successfully: {audio_path}")

    def upload_to_gcs(self, file_path, destination_blob_name):
        """Uploads a file to Google Cloud Storage."""
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(file_path)
        return f"gs://{self.bucket_name}/{destination_blob_name}"

    def get_sample_rate(self, audio_path):
        audio = AudioSegment.from_wav(audio_path)
        return audio.frame_rate

    def convert_to_mono(self, input_path, output_path):
        """Convert stereo audio to mono."""
        data, samplerate = sf.read(input_path)
        if len(data.shape) > 1:  # Check if audio is stereo
            mono_data = data.mean(axis=1)  # Convert to mono by averaging channels
        else:
            mono_data = data
        sf.write(output_path, mono_data, samplerate)
        print(f"Converted audio to mono: {output_path}")

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file using Google's Speech-to-Text API (long-running operation)."""
        gcs_uri = self.upload_to_gcs(audio_path, os.path.basename(audio_path))

        audio = speech.RecognitionAudio(uri=gcs_uri)
        
        # Get the correct sample rate from the audio file
        sample_rate = self.get_sample_rate(audio_path)
        
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,  # Use the detected sample rate
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        operation = self.client.long_running_recognize(config=config, audio=audio)
        print("Waiting for operation to complete...")
        response = operation.result(timeout=300)  # Increased timeout to 5 minutes

        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "

        return transcript.strip()

    def process_video(self, video_input: str) -> str:
        """Process video file or YouTube URL and return transcript."""
        audio_path = "temp_audio.wav"
        mono_audio_path = "temp_audio_mono.wav"
        
        try:
            if video_input.startswith('http'):  # Assume it's a YouTube URL
                self.download_youtube_audio(video_input, audio_path)
            else:  # Assume it's a local file path
                self.extract_audio(video_input, audio_path)
            
            # Convert to mono
            self.convert_to_mono(audio_path, mono_audio_path)
            
            transcript = self.transcribe_audio(mono_audio_path)
            return transcript
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)  # Clean up temporary audio file
            if os.path.exists(mono_audio_path):
                os.remove(mono_audio_path)  # Clean up temporary mono audio file

    def extract_audio(self, video_path: str, audio_path: str):
        """Extract audio from local video file using FFmpeg."""
        command = [
            self.ffmpeg_path,
            "-i", video_path,
            "-ab", "160k",
            "-ac", "1",  # Ensure mono audio
            "-ar", "48000",
            "-vn", audio_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Audio extracted successfully: {audio_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            raise

# Streamlit app
def main():
    st.title("YouTube Video Transcription")

    # Input for YouTube URL
    youtube_url = st.text_input("Enter YouTube Video URL:")

    if st.button("Transcribe"):
        if youtube_url:
            with st.spinner("Transcribing... This may take a few minutes."):
                processor = VideoProcessor()
                try:
                    transcript = processor.process_video(youtube_url)
                    st.success("Transcription complete!")
                    st.subheader("Transcript:")
                    st.write(transcript)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please enter a YouTube URL.")

if __name__ == "__main__":
    main()
