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
from moviepy.editor import VideoFileClip, concatenate_videoclips
import pandas as pd
from num2words import num2words
import re
from nltk.stem import WordNetLemmatizer
from nltk.parse.stanford import StanfordParser
from nltk import ParentedTree, Tree
import nltk
from num2words import num2words
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

# Set up Stanford Parser
java_path = "C:\\Program Files\\Java\\jdk-22\\bin\\java.exe"  
os.environ['JAVAHOME'] = java_path

sp = StanfordParser(path_to_jar="C:\\Users\\baran\\Downloads\\stanford-parser-full-2018-02-27\\stanford-parser-full-2018-02-27\\stanford-parser.jar",
                    path_to_models_jar="C:\\Users\\baran\\Downloads\\stanford-parser-full-2018-02-27\\stanford-parser-full-2018-02-27\\stanford-parser-3.9.1-models.jar")


stopwords_set = set(['a', 'an', 'the', 'is', 'to', 'The', 'in', 'of', 'us'])

class VideoProcessor:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file("google_credentials.json")
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
            'ffmpeg_location': 'ffmpeg.exe',
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
            "ffmpeg",
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


def convert_isl(parsetree):
    dict = {}
    parenttree = ParentedTree.convert(parsetree)

    # Initialize dict for tracking visited nodes
    for sub in parenttree.subtrees():
        dict[sub.treeposition()] = 0

    isltree = Tree('ROOT', [])
    i = 0

    for sub in parenttree.subtrees():
        if sub.label() == "NP" and dict.get(sub.treeposition(), 0) == 0 and dict.get(sub.parent().treeposition(), 0) == 0:
            dict[sub.treeposition()] = 1
            isltree.insert(i, sub)
            i += 1

        if sub.label() == "VP" or sub.label() == "PRP":
            for sub2 in sub.subtrees():
                if sub2 and (sub2.label() == "NP" or sub2.label() == 'PRP') and sub2.treeposition() is not None and dict.get(sub2.treeposition(), 0) == 0 and sub2.parent() and sub2.parent().treeposition() is not None and dict.get(sub2.parent().treeposition(), 0) == 0:
                    dict[sub2.treeposition()] = 1
                    isltree.insert(i, sub2)
                    i += 1

    for sub in parenttree.subtrees():
        for sub2 in sub.subtrees():
            if sub2 and len(sub2.leaves()) == 1 and sub2.treeposition() is not None and dict.get(sub2.treeposition(), 0) == 0 and sub2.parent() and sub2.parent().treeposition() is not None and dict.get(sub2.parent().treeposition(), 0) == 0:
                dict[sub2.treeposition()] = 1
                isltree.insert(i, sub2)
                i += 1

    return isltree



def text_to_isl(sentence):
  pattern = r'[^\w\s]'

# Remove the punctuation marks from the sentence
  sentence = re.sub(pattern, '', sentence)
  englishtree=[tree for tree in sp.parse(sentence.split())]
  parsetree=englishtree[0]
  #print(parsetree)
  isl_tree = convert_isl(parsetree)
  words=parsetree.leaves()
  lemmatizer = WordNetLemmatizer()
  ps = PorterStemmer()
  lemmatized_words=[]
  for w in words:
    #w = ps.stem(w)
   lemmatized_words.append(lemmatizer.lemmatize(w))
   islsentence = ""
   for w in lemmatized_words:
    if w not in stopwords_set:
      islsentence+=w
      islsentence+=" "
  #islsentence = clean(words)
  islsentence = islsentence.lower()
  isltree=[tree for tree in sp.parse(islsentence.split())]
  return islsentence

from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

def get_yt(link, path):
    try:
        yt = YouTube(link)
        yt.streams.filter(file_extension="mp4").get_by_resolution("360p").download(path)
    except AgeRestrictedError as e:
        print(f"Video {e.video_id} is age-restricted. Please log in to download.")
        # Handle this exception as per your application's logic

from moviepy.editor import *
import os

def cut_vid(filename,yt_name,start_min,start_sec,end_min,end_sec):
  clip = VideoFileClip(os.path.join(yt_path,yt_name+'.mp4'))
  clip1 = clip.subclip((start_min,start_sec),(end_min,end_sec))
  clip1.write_videofile(os.path.join('NLP_dataset',filename+'.mp4'),codec='libx264')



def create_directories():
    """Creates the necessary directories if they don't exist."""
    if not os.path.exists("NLP_dataset"):
        os.mkdir("NLP_dataset")
        print("Created directory: NLP_dataset")

    if not os.path.exists("yt"):
        os.mkdir("yt")
        print("Created directory: yt")

# Call the function to create the directories
create_directories()

root_path = 'NLP_dataset'
yt_path = 'yt'


NLP_videos = pd.read_csv("NLP_videos.csv")



import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import pandas as pd
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

# Function to download YouTube videos
def get_yt(link, path):
    try:
        yt = YouTube(link)
        yt.streams.filter(file_extension="mp4").get_by_resolution("360p").download(path)
        return True
    except AgeRestrictedError as e:
        print(f"Video {e.video_id} is age-restricted. Please log in to download.")
        return False
    except Exception as e:
        print(f"Failed to download video: {e}")
        return False

# Function to cut the video clip
def cut_vid(filename, yt_name, start_min, start_sec, end_min, end_sec):
    clip = VideoFileClip(os.path.join(yt_path, yt_name + '.mp4'))
    clip1 = clip.subclip((start_min, start_sec), (end_min, end_sec))
    clip1.write_videofile(os.path.join('NLP_dataset', filename + '.mp4'), codec='libx264')


# Create necessary directories
os.makedirs('NLP_dataset', exist_ok=True)
os.makedirs('yt', exist_ok=True)

root_path = 'NLP_dataset'
yt_path = 'yt'

# Load the NLP_videos CSV
NLP_videos = pd.read_csv('NLP_videos.csv')

# Function to get the path of the GIF
def get_gif_path(character):
    gif_path = f"alphabet\\{character}_small.gif"
    if not os.path.exists(gif_path):
        raise FileNotFoundError(f"GIF for character {character} not found.")
    return gif_path


# Function to convert text to ISL
def text_to_isl(sentence):
    # Remove punctuation
    sentence = re.sub(r'[^\w\s]', '', sentence)
    englishtree = [tree for tree in sp.parse(sentence.split())]
    parsetree = englishtree[0]
    isl_tree = convert_isl(parsetree)
    words = parsetree.leaves()
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = [lemmatizer.lemmatize(w) for w in words]
    islsentence = " ".join(w.lower() for w in lemmatized_words if w not in stopwords_set)
    return islsentence


def text_to_vid(input_text, chunk_size=500):
    def process_chunk(chunk):
        videos = []
        clips = []
        sentence = text_to_isl(chunk)
        words = sentence.split()
        for word in words:
            if (NLP_videos['Name'].eq(word)).any():
                idx = NLP_videos.index[NLP_videos['Name'] == word].tolist()[0]
                yt_link = NLP_videos['Link'].iloc[idx]
                yt_name = NLP_videos['yt_name'].iloc[idx]
                if get_yt(yt_link, yt_path):
                    cut_vid(word, yt_name, NLP_videos['start_min'].iloc[idx], NLP_videos['start_sec'].iloc[idx], NLP_videos['end_min'].iloc[idx], NLP_videos['end_sec'].iloc[idx])
                    videos.append(os.path.join(root_path, word + '.mp4'))
            else:
                # If word not in dataset, spell it out
                for char in word:
                    if char.isalpha():
                        gif_path = get_gif_path(char.lower())
                        if gif_path:  # Only add if gif_path is not None
                            videos.append(gif_path)
                    elif char.isdigit():
                        # Handle numbers by spelling them out
                        number_name = num2words(int(char)).lower()
                        for letter in number_name:
                            if letter.isalpha():
                                gif_path = get_gif_path(letter)
                                if gif_path:  # Only add if gif_path is not None
                                    videos.append(gif_path)

        for video in videos:
            if video.endswith('.mp4'):
                clip = VideoFileClip(video)
            else:
                clip = VideoFileClip(video).set_duration(0.5)  # Set GIF duration
            clips.append(clip)

        return clips

    # Split the input text into chunks
    chunks = [input_text[i:i+chunk_size] for i in range(0, len(input_text), chunk_size)]

    all_clips = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        chunk_clips = process_chunk(chunk)
        all_clips.extend(chunk_clips)

    print("Merging all clips...")
    final = concatenate_videoclips([clip for clip in all_clips if clip is not None], method="compose")
    final.write_videofile("merged.mp4")
    print("Video processing complete.")


def main():
    st.title("Video to Sign Language Converter")

    # Sidebar to choose input type
    input_type = st.sidebar.selectbox("Choose input type:", ["YouTube URL", "Local Video/Audio File", "Text Input"])

    if input_type == "YouTube URL":
        youtube_url = st.text_input("Enter YouTube URL:")
        if st.button("Process YouTube URL"):
            st.write(f"Processing YouTube video from URL: {youtube_url}")
            progress_bar = st.progress(0)

            # Process video and get transcript
            processor = VideoProcessor()
            progress_bar.progress(10)
            transcript = processor.process_video(youtube_url)
            progress_bar.progress(60)

            # Convert transcript to ISL
            isl_text = text_to_isl(transcript)
            progress_bar.progress(100)

            st.subheader("Transcript:")
            st.write(transcript)

            st.subheader("Converted Sign Language Text:")
            st.write(isl_text)

    elif input_type == "Local Video/Audio File":
        uploaded_file = st.file_uploader("Upload a video or audio file", type=["mp4", "mov", "avi", "wav"])
        if uploaded_file is not None:
            file_path = f"temp_file.{uploaded_file.name.split('.')[-1]}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.video(uploaded_file)

            progress_bar = st.progress(0)

            # Process video or audio and get transcript
            processor = VideoProcessor()
            progress_bar.progress(10)
            transcript = processor.process_video(file_path)
            progress_bar.progress(60)

            # Convert transcript to ISL
            isl_text = text_to_isl(transcript)
            progress_bar.progress(100)

            st.subheader("Transcript:")
            st.write(transcript)

            st.subheader("Converted Sign Language Text:")
            st.write(isl_text)

    elif input_type == "Text Input":
        user_text = st.text_area("Enter text:")
        if st.button("Process Text"):
            if user_text:
                st.write("Processing text input")
                progress_bar = st.progress(0)
                
                # Convert text to ISL
                text_to_vid(user_text)
                progress_bar.progress(100)

                st.subheader("Converted Sign Language Video:")
                st.video("merged.mp4")  

            else:
                st.write("Please enter some text")

    st.sidebar.text("Developed by Nooglers")

if __name__ == "__main__":
    main()
