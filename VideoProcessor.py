import os
import subprocess
from google.cloud import speech_v1
from google.cloud import speech
from google.oauth2 import service_account
from google.cloud import storage
from pydub import AudioSegment
import soundfile as sf
import yt_dlp as youtube_dl

class VideoProcessor:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file("C:\\Users\\baran\\Downloads\\google_credentials.json")
        self.client = speech_v1.SpeechClient(credentials=credentials)
        self.storage_client = storage.Client(credentials=credentials)
        self.bucket_name = "sign-language-1"

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
            'ffmpeg_location': "C:\\Users\\baran\\Downloads\\ffmpeg-7.0.1-full_build\\ffmpeg-7.0.1-full_build\\bin\\ffmpeg.exe",
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
        ffmpeg_path = "C:\\Users\\baran\\Downloads\\ffmpeg-7.0.1-full_build\\ffmpeg-7.0.1-full_build\\bin\\ffmpeg.exe"
        command = [
            ffmpeg_path,
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