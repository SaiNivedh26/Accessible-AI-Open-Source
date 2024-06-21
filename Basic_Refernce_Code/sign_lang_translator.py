# sign_language_translator.py

import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import re

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

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
            # Add more mappings here
        }
        
        self.gesture_categories = {
            "GREETING": ["hello", "hi", "hey"],
            "QUESTION": ["what", "when", "where", "who", "why", "how"],
            # Add more categories here
        }

    def preprocess_text(self, text: str) -> str:
        """Preprocess the input text."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def categorize_word(self, word: str) -> str:
        """Categorize a word based on predefined categories."""
        for category, words in self.gesture_categories.items():
            if word in words:
                return category
        return "GENERAL"

    def translate_to_signs(self, text: str) -> list:
        """Translate text to a list of sign language gestures."""
        preprocessed_text = self.preprocess_text(text)
        words = word_tokenize(preprocessed_text)
        tagged_words = pos_tag(words)
        
        signs = []
        i = 0
        while i < len(words):
            # Check for multi-word phrases
            for j in range(len(words), i, -1):
                phrase = " ".join(words[i:j])
                if phrase in self.sign_dictionary:
                    signs.append(self.sign_dictionary[phrase])
                    i = j
                    break
            else:
                # If no phrase match, process single word
                word, pos = tagged_words[i]
                category = self.categorize_word(word)
                
                if category != "GENERAL":
                    signs.append(f"{category}_{word}")
                elif pos.startswith('NN'):  # Noun
                    signs.append(f"noun_{word}")
                elif pos.startswith('VB'):  # Verb
                    signs.append(f"verb_{word}")
                elif pos.startswith('JJ'):  # Adjective
                    signs.append(f"adj_{word}")
                else:
                    signs.append(f"general_{word}")
                
                i += 1
        
        return signs

# Usage
if __name__ == "__main__":
    translator = SignLanguageTranslator()
    text = "Hello, how are you? What is your name?"
    signs = translator.translate_to_signs(text)
    print(f"Translated signs: {signs}")
