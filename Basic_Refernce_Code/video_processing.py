import os
import subprocess
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
import io

class VideoProcessor:
    def __init__(self):
        # Ensure you have set the GOOGLE_APPLICATION_CREDENTIALS environment variable
        self.client = speech_v1.SpeechClient()

    def extract_audio(self, video_path: str, audio_path: str):
        """Extract audio from video file using FFmpeg."""
        command = [
            "ffmpeg",
            "-i", video_path,
            "-ab", "160k",
            "-ac", "2",
            "-ar", "44100",
            "-vn", audio_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Audio extracted successfully: {audio_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            raise

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file using Google's Speech-to-Text API."""
        with io.open(audio_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )

        response = self.client.recognize(config=config, audio=audio)

        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "

        return transcript.strip()

    def process_video(self, video_path: str) -> str:
        """Process video file and return transcript."""
        audio_path = "temp_audio.wav"
        
        try:
            self.extract_audio(video_path, audio_path)
            transcript = self.transcribe_audio(audio_path)
            return transcript
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)  # Clean up temporary audio file

# Usage
if __name__ == "__main__":
    processor = VideoProcessor()
    video_path = "path/to/your/video.mp4"
    try:
        transcript = processor.process_video(video_path)
        print(f"Transcript: {transcript}")
    except Exception as e:
        print(f"An error occurred: {e}")
