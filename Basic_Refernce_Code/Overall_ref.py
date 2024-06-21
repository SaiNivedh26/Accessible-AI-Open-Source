import os
import subprocess
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
import io
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import re
import bpy
import math

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

class VideoProcessor:
    def __init__(self):
        self.client = speech_v1.SpeechClient()

    def extract_audio(self, video_path: str, audio_path: str):
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
        audio_path = "temp_audio.wav"
        
        try:
            self.extract_audio(video_path, audio_path)
            transcript = self.transcribe_audio(audio_path)
            return transcript
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

class SignLanguageTranslator:
    def __init__(self):
        self.sign_dictionary = {
            "hello": "greeting_hello",
            "how are you": "question_how_are_you",
            "what": "question_what",
            "when": "question_when",
            "where": "question_where",
            "who": "question_who",
            "why": "question_why",
        }
        
        self.gesture_categories = {
            "GREETING": ["hello", "hi", "hey"],
            "QUESTION": ["what", "when", "where", "who", "why", "how"],
        }

    def preprocess_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def categorize_word(self, word: str) -> str:
        for category, words in self.gesture_categories.items():
            if word in words:
                return category
        return "GENERAL"

    def translate_to_signs(self, text: str) -> list:
        preprocessed_text = self.preprocess_text(text)
        words = word_tokenize(preprocessed_text)
        tagged_words = pos_tag(words)
        
        signs = []
        i = 0
        while i < len(words):
            for j in range(len(words), i, -1):
                phrase = " ".join(words[i:j])
                if phrase in self.sign_dictionary:
                    signs.append(self.sign_dictionary[phrase])
                    i = j
                    break
            else:
                word, pos = tagged_words[i]
                category = self.categorize_word(word)
                
                if category != "GENERAL":
                    signs.append(f"{category}_{word}")
                elif pos.startswith('NN'):
                    signs.append(f"noun_{word}")
                elif pos.startswith('VB'):
                    signs.append(f"verb_{word}")
                elif pos.startswith('JJ'):
                    signs.append(f"adj_{word}")
                else:
                    signs.append(f"general_{word}")
                
                i += 1
        
        return signs

class SignLanguageAnimator:
    def __init__(self):
        self.hand = None
        self.create_hand()

    def create_hand(self):
        bpy.ops.mesh.primitive_cube_add(size=1)
        self.hand = bpy.context.active_object
        self.hand.name = "Hand"
        
        for i in range(5):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5)
            finger = bpy.context.active_object
            finger.name = f"Finger_{i}"
            finger.parent = self.hand
            finger.location = (0.2 * (i - 2), 0.5, 0.2)

    def animate_sign(self, sign: str, frame_start: int):
        if sign.startswith("greeting_"):
            self.animate_greeting(frame_start)
        elif sign.startswith("question_"):
            self.animate_question(frame_start)
        else:
            self.animate_general(sign, frame_start)

    def animate_greeting(self, frame_start: int):
        self.hand.location = (0, 0, 0)
        self.hand.keyframe_insert(data_path="location", frame=frame_start)
        
        self.hand.location = (0, 0, 1)
        self.hand.keyframe_insert(data_path="location", frame=frame_start + 15)
        
        self.hand.location = (0, 0, 0)
        self.hand.keyframe_insert(data_path="location", frame=frame_start + 30)

    def animate_question(self, frame_start: int):
        self.hand.rotation_euler = (0, 0, 0)
        self.hand.keyframe_insert(data_path="rotation_euler", frame=frame_start)
        
        self.hand.rotation_euler = (0, 0, math.radians(45))
        self.hand.keyframe_insert(data_path="rotation_euler", frame=frame_start + 15)
        
        self.hand.rotation_euler = (0, 0, 0)
        self.hand.keyframe_insert(data_path="rotation_euler", frame=frame_start + 30)

    def animate_general(self, sign: str, frame_start: int):
        self.hand.scale = (1, 1, 1)
        self.hand.keyframe_insert(data_path="scale", frame=frame_start)
        
        self.hand.scale = (1.2, 1.2, 1.2)
        self.hand.keyframe_insert(data_path="scale", frame=frame_start + 15)
        
        self.hand.scale = (1, 1, 1)
        self.hand.keyframe_insert(data_path="scale", frame=frame_start + 30)

    def create_animation(self, signs: list):
        for i, sign in enumerate(signs):
            self.animate_sign(sign, i * 30)

def main(video_path: str):
    # Process video
    processor = VideoProcessor()
    transcript = processor.process_video(video_path)
    print(f"Transcript: {transcript}")

    # Translate to sign language
    translator = SignLanguageTranslator()
    signs = translator.translate_to_signs(transcript)
    print(f"Signs: {signs}")

    # Create animation in Blender
    animator = SignLanguageAnimator()
    animator.create_animation(signs)

    print("Animation created in Blender.")

# Usage
if __name__ == "__main__":
    video_path = "path/to/your/video.mp4"
    main(video_path)
