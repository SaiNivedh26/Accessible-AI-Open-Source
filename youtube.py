import os
from moviepy.editor import VideoFileClip
from pytube import YouTube
from pytube.exceptions import AgeRestrictedError

root_path = 'NLP_dataset'
yt_path = 'yt'

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
