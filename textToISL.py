import re
from nltk.stem import WordNetLemmatizer
from nltk.parse.stanford import StanfordParser
import nltk
from num2words import num2words
import os
import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips

from youtube import get_yt, cut_vid

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
# Create necessary directories
os.makedirs('NLP_dataset', exist_ok=True)
os.makedirs('yt', exist_ok=True)
os.makedirs('temp_outputs', exist_ok=True)

root_path = 'NLP_dataset'
yt_path = 'yt'

# Load the NLP_videos CSV
NLP_videos = pd.read_csv("NLP_videos.csv")

def get_gif_path(character):
        gif_path = f"alphabet\\{character}_small.gif"
        
        if not os.path.exists(gif_path):
            print(f"Warning: GIF for character '{character}' not found. Skipping.")
            return None
        return gif_path


# Function to convert text to ISL
def text_to_isl(sentence):
    # Remove punctuation
    sentence = re.sub(r'[^\w\s]', '', sentence)
    englishtree = [tree for tree in sp.parse(sentence.split())]
    parsetree = englishtree[0]
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
    final.write_videofile("temp_outputs\\merged.mp4")
    print("Video processing complete.")
