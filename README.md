# Digital Content to Sign Language Converter

## Project Demo
Before diving into the details of the process, take a moment to watch a demo video showcasing our project in action.
***ADD THE VIDEO FILE HERE

## Project Overview
The Digital Content to Sign Language Converter is a comprehensive tool that converts various forms of Digital media (YouTube videos, local videos, audio files, and text) into sign language videos. This project leverages several libraries and APIs to process and translate spoken or written content into Indian Sign Language (ISL) syntax, creating videos that can aid in communication for the deaf and hard-of-hearing community.

## Project Objective
The primary objective of this project is to bridge the communication gap for individuals who rely on sign language. By converting various media formats into sign language videos, we aim to provide an accessible and efficient means of understanding content that is traditionally available only in spoken or written form.

## Features
- **YouTube Video Processing:** Download and convert YouTube videos into sign language videos.
- **Local File Processing:** Convert local video or audio files into sign language videos.
- **Text Input Processing:** Translate text into sign language videos.
- **Sign Language Translation:** Convert English sentences into ISL syntax.
- **Video Compilation:** Combine video clips and GIFs to form coherent sign language videos.

## Technology/Libraries Used 🐍
- **Python:** Core programming language used for development.
- **Streamlit:** Framework for creating the web interface.
- **Google Cloud Speech-to-Text API:** For transcribing audio to text.
- **yt-dlp:** For downloading YouTube videos.
- **MoviePy:** For video processing and editing.
- **Pydub:** For audio processing.
- **nltk:** For natural language processing tasks.
- **num2words:** For converting numbers to words.
- **pytube:** For downloading YouTube videos.
- **pandas:** For data manipulation and handling.
- **Stanford Parser:** For syntactic parsing of sentences.

## Methodology 📝
### YouTube Video Processing 📽️
1. **Download Audio:** Using `yt-dlp`, download the audio from the provided YouTube URL.
2. **Convert to Mono:** Ensure the audio is in mono format using `pydub`.
3. **Transcribe Audio:** Use Google Cloud Speech-to-Text API to transcribe the audio into text.
4. **Translate to ISL:** Convert the transcribed text to ISL syntax using `nltk` and Stanford Parser.
5. **Compile Video:** Use `MoviePy` to compile the translated text into a sign language video.

### Local File Processing 🎤
1. **Extract Audio:** Extract audio from the uploaded video or audio file using `ffmpeg`.
2. **Transcribe Audio:** Transcribe the extracted audio using Google Cloud Speech-to-Text API.
3. **Translate to ISL:** Convert the transcribed text to ISL syntax.
4. **Compile Video:** Compile the translated text into a sign language video.

### Text Input Processing ✏️
1. **Translate to ISL:** Directly convert the input text to ISL syntax.
2. **Compile Video:** Compile the translated text into a sign language video using appropriate video clips and GIFs.

## Flow Diagram
![Flow Diagram](https://github.com/SaiNivedh26/Hackathon-June-2024/assets/155757417/408864b4-5c0a-4213-bb49-85422cca4c5d) <!-- Ensure you have a flow diagram image file in your repository -->

## How We Built It 🛠️👷‍♂️
1. **Setting Up Environment:**
   - Install necessary libraries and tools.
   - Set up Google Cloud credentials and APIs.

2. **Developing the Backend:**
   - Implement the `VideoProcessor` class to handle downloading, audio processing, and transcription.
   - Develop functions for text processing and translation to ISL.

3. **Creating the Frontend:**
   - Use Streamlit to create an intuitive web interface for users to input YouTube URLs, upload files, or enter text.
   - Integrate backend processing with the frontend to provide real-time feedback and results.

4. **Testing and Optimization:**
   - Test the application with various inputs to ensure accuracy and robustness.
   - Optimize the processing pipeline for efficiency and speed.

     
## How to Run 💻
1. **Clone the Repository:**
   ```
   git clone https://github.com/SaiNivedh26/Hackathon-June-2024
   cd Hackathon-June-2024
   ```

2. **Run the app.py file in the terminal:**
   ```
   streamlit run Hackathon-June-2024/app.py
   ```
