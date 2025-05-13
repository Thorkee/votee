#!/usr/bin/env python3
import requests
import random
import string
import json
import time
import os
from typing import List, Dict, Set, Tuple
import argparse

# API URL
API_BASE_URL = "https://wordle.votee.dev:8000"

# OpenAI API URL
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# OpenAI API Key - Load from environment variable
OPENAI_API_KEY_FROM_ENV = os.environ.get("OPENAI_API_KEY")

class WordleSolver:
    def __init__(self, word_size: int = 5, mode: str = "random", target_word: str = None, seed: int = None, 
                 cli_openai_api_key: str = None, no_ai_flag: bool = False,
                 api_base_url=API_BASE_URL, openai_api_url=OPENAI_API_URL):
        self.word_size = word_size
        self.mode = mode
        self.target_word = target_word
        # self.seed = seed # Original assignment of CLI seed

        # Determine the definitive seed for this game session
        current_game_seed = seed # Start with the seed passed from CLI
        if self.mode == "random" and current_game_seed is None:
            # If in random mode and no seed was provided via CLI, generate one for this game session.
            # This ensures API calls for this game are consistent and solver choices are deterministic for this game.
            current_game_seed = random.randint(0, 2**32 - 1) # A common range for seeds
            print(f"Random mode: No CLI seed provided. Generated internal seed for this game: {current_game_seed}")
        
        self.seed = current_game_seed # This self.seed will be used by make_guess and for Python's RNG seeding

        if self.seed is not None:
            # Seed Python's random number generator for deterministic internal choices (e.g., first guess, tie-breaking)
            # If CLI seed was given, this uses it. If internal seed was generated for random mode, this uses it.
            print(f"Initializing Python's random module with seed: {self.seed}")
            random.seed(self.seed)
        # If self.seed is None (e.g., daily/word mode without CLI seed), Python's RNG remains unseeded by us here (default behavior).
        
        self.guesses_made = 0
        # self.use_ai = use_ai # This will be determined below

        self.api_base_url = api_base_url
        self.openai_api_url = openai_api_url
        
        # Load a dictionary of common English words
        # self.load_dictionary() # This seems to be called later or was from a different version. Ensure it's called if needed.
                                # Current version from read_file has it here.
        self.load_dictionary()


        # Track letter constraints
        self.correct_positions = {}  # {position: letter}
        self.present_letters = set()  # letters in the word but wrong position
        self.absent_letters = set()  # letters not in the word
        self.position_constraints = {}  # {position: set(letters_not_in_this_position)}
        
        # Initialize position constraints
        for i in range(self.word_size):
            self.position_constraints[i] = set()
        
        # Handle OpenAI API key and AI usage
        self.openai_api_key = None
        if cli_openai_api_key:
            self.openai_api_key = cli_openai_api_key
            print("Using OpenAI API key from command-line argument.")
        elif OPENAI_API_KEY_FROM_ENV:
            self.openai_api_key = OPENAI_API_KEY_FROM_ENV
            print("Using OpenAI API key from environment variable.")

        if no_ai_flag:
            self.use_ai = False
            print("AI assistance explicitly disabled via --no-ai flag.")
        elif self.openai_api_key:
            self.use_ai = True
            print("OpenAI API key found. AI assistance is enabled.")
        else:
            self.use_ai = False
            print("Warning: OpenAI API key not provided via command-line or environment variable. AI assistance will be disabled.")
            print("To enable AI, set the OPENAI_API_KEY environment variable or use the --openai-api-key argument.")
    
    def load_dictionary(self):
        """Load a list of common English words of the specified length."""
        try:
            import nltk
            nltk.download('words', quiet=True)
            from nltk.corpus import words as nltk_words
            all_words = set(word.lower() for word in nltk_words.words())
            self.words = [word for word in all_words if len(word) == self.word_size and word.isalpha()]
        except:
            # If NLTK is not available, use a basic word list
            print("NLTK not available. Using a simplified word list.")
            self.words = self.get_basic_word_list()
        
        print(f"Loaded {len(self.words)} words of length {self.word_size}")
    
    def get_basic_word_list(self) -> List[str]:
        """Return a basic list of common words if NLTK is not available."""
        # Some common 5-letter English words
        basic_words = [
            "about", "above", "abuse", "actor", "adapt", "adult", "after", "again", "agent", "agree",
            "ahead", "alarm", "album", "alert", "alike", "alive", "allow", "alone", "along", "alter",
            "among", "anger", "angle", "angry", "anime", "ankle", "apart", "apple", "apply", "arena",
            "argue", "arise", "armor", "array", "arrow", "asset", "avoid", "award", "aware", "awful",
            "baker", "basic", "basis", "beach", "beard", "beast", "begin", "being", "below", "bench",
            "birth", "black", "blade", "blame", "blank", "blast", "bleed", "blend", "bless", "blind",
            "block", "blood", "bloom", "blues", "bluff", "board", "boast", "bonus", "boost", "booth",
            "bound", "brace", "brain", "brand", "brave", "bread", "break", "breed", "brief", "bring",
            "broad", "brown", "brush", "build", "built", "buyer", "cable", "carry", "catch", "cause",
            "chain", "chair", "chalk", "charm", "chart", "chase", "cheap", "check", "chess", "chest",
            "chief", "child", "chill", "china", "chips", "choke", "chord", "civic", "civil", "claim",
            "class", "clean", "clear", "clerk", "click", "cliff", "climb", "clock", "close", "cloth",
            "cloud", "coach", "coast", "color", "comic", "coral", "count", "court", "cover", "crack",
            "craft", "crash", "cream", "creek", "crest", "crime", "cross", "crowd", "crown", "curve",
            "cycle", "daily", "dance", "dated", "dealt", "death", "debut", "delay", "depth", "devil",
            "diary", "digit", "dirty", "ditch", "diver", "donor", "doubt", "dough", "draft", "drain",
            "drama", "dream", "dress", "drift", "drill", "drink", "drive", "drone", "drunk", "earth",
            "enjoy", "enter", "entry", "equal", "error", "essay", "event", "every", "exact", "exist",
            "extra", "faith", "false", "fault", "favor", "feast", "field", "fifth", "fight", "final",
            "first", "flame", "flash", "fleet", "flesh", "float", "flood", "floor", "flora", "flour",
            "fluid", "focus", "force", "forth", "found", "frame", "frank", "fraud", "fresh", "front",
            "frost", "fruit", "fully", "funny", "ghost", "giant", "given", "glass", "globe", "glory",
            "grade", "grain", "grand", "grant", "grape", "grass", "grave", "great", "green", "grief",
            "gross", "group", "guard", "guest", "guide", "guild", "happy", "harsh", "heart", "heavy",
            "hence", "horse", "hotel", "house", "human", "ideal", "image", "index", "inner", "input",
            "issue", "japan", "joint", "jones", "judge", "juice", "knife", "knock", "known", "label",
            "large", "laser", "later", "laugh", "layer", "learn", "lease", "least", "leave", "legal",
            "level", "light", "limit", "links", "liver", "lives", "local", "logic", "loose", "lower",
            "lucky", "lunch", "lying", "magic", "major", "maker", "march", "match", "maybe", "mayor",
            "meant", "medal", "metal", "might", "minor", "minus", "mixed", "model", "money", "month",
            "moral", "motor", "mount", "mouse", "mouth", "movie", "music", "naval", "needs", "never",
            "newly", "night", "noise", "north", "noted", "novel", "nurse", "occur", "ocean", "offer",
            "often", "order", "other", "outer", "owner", "panel", "panic", "paper", "party", "patch",
            "peace", "phase", "phone", "photo", "piano", "piece", "pilot", "pitch", "place", "plain",
            "plane", "plant", "plate", "point", "poker", "pound", "power", "press", "price", "pride",
            "prime", "print", "prior", "prize", "proof", "proud", "prove", "queen", "quick", "quiet",
            "quite", "radio", "raise", "range", "rapid", "ratio", "reach", "ready", "refer", "right",
            "rival", "river", "robin", "roger", "roman", "rough", "round", "route", "royal", "rural",
            "scale", "scene", "scope", "score", "sense", "serve", "seven", "shade", "shake", "shall",
            "shape", "share", "sharp", "sheep", "sheet", "shelf", "shell", "shift", "shine", "shirt",
            "shock", "shoot", "shore", "short", "shown", "sight", "since", "sixth", "sixty", "skill",
            "sleep", "slide", "small", "smart", "smile", "smith", "smoke", "solid", "solve", "sorry",
            "sound", "south", "space", "spare", "speak", "speed", "spend", "spent", "split", "spoke",
            "sport", "squad", "stack", "staff", "stage", "stake", "stand", "stare", "start", "state",
            "steam", "steel", "stick", "still", "stock", "stone", "stood", "store", "storm", "story",
            "strip", "stuck", "study", "stuff", "style", "sugar", "suite", "super", "sweet", "swing",
            "sworn", "table", "taken", "tales", "taste", "taxes", "teach", "teeth", "texas", "thank",
            "theft", "their", "theme", "there", "these", "thick", "thing", "think", "third", "those",
            "three", "throw", "tight", "times", "tired", "title", "today", "token", "tooth", "topic",
            "total", "touch", "tough", "tower", "track", "trade", "train", "treat", "trend", "trial",
            "tribe", "trick", "tried", "tries", "truck", "truly", "trust", "truth", "twice", "twist",
            "uncle", "under", "union", "unity", "until", "upper", "upset", "urban", "usage", "usual",
            "valid", "value", "video", "virus", "visit", "vital", "voice", "voter", "waste", "watch",
            "water", "weigh", "weird", "wheel", "where", "which", "while", "white", "whole", "whose",
            "woman", "women", "world", "worry", "worse", "worst", "worth", "would", "wound", "write",
            "wrong", "wrote", "yield", "young", "youth"
        ]
        return [word for word in basic_words if len(word) == self.word_size]
    
    def get_ai_suggestions(self, num_suggestions: int = 5) -> List[str]:
        if not self.use_ai or not self.openai_api_key: # Ensure this check is robust
            # print("AI assistance is disabled or API key is missing. Skipping OpenAI query.") # Can be verbose
            return []
        
        try:
            # Construct the prompt with all our current constraints
            prompt = f"I'm playing a Wordle game with a {self.word_size}-letter word. Please help me find the most likely word based on these constraints:\n\n"
            
            # Add correct positions
            if self.correct_positions:
                word_template = ['_'] * self.word_size
                for pos, letter in self.correct_positions.items():
                    word_template[pos] = letter
                prompt += f"Correct positions: {''.join(word_template)}\n"
            
            # Add present letters
            if self.present_letters:
                prompt += f"Letters that are in the word but in wrong positions: {', '.join(sorted(self.present_letters))}\n"
            
            # Add absent letters
            if self.absent_letters:
                prompt += f"Letters that are NOT in the word: {', '.join(sorted(self.absent_letters))}\n"
            
            # Add position constraints
            if any(self.position_constraints.values()):
                prompt += "Position constraints:\n"
                for pos, letters in self.position_constraints.items():
                    if letters:
                        prompt += f"Position {pos+1}: Cannot contain {', '.join(sorted(letters))}\n"
            
            prompt += f"\nPlease give me the {num_suggestions} most likely {self.word_size}-letter words that match these constraints, one per line. Only include valid English words."
            
            # Call OpenAI API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides word suggestions for Wordle."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 200
            }
            
            response = requests.post(
                self.openai_api_url,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Extract words from the response
                words = []
                for line in content.split('\n'):
                    # Clean the line and extract the word
                    clean_line = line.strip().lower()
                    # Remove any numbering or bullet points
                    if clean_line and (clean_line[0].isdigit() or clean_line[0] in ['•', '-', '*']):
                        clean_line = ''.join(clean_line.split(' ')[1:])
                    
                    # Only add words of the correct length
                    if clean_line and len(clean_line) == self.word_size and clean_line.isalpha():
                        words.append(clean_line)
                
                print(f"AI suggested words: {', '.join(words)}")
                return words
            else:
                print(f"Error calling OpenAI API: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"Error when calling OpenAI API: {str(e)}")
            return []
    
    def make_guess(self, guess: str) -> List[Dict]:
        """Make a guess and get the result from the API."""
        if self.mode == "random":
            url = f"{API_BASE_URL}/random"
            params = {"guess": guess, "size": self.word_size}
            if self.seed is not None:
                params["seed"] = self.seed
        elif self.mode == "daily":
            url = f"{API_BASE_URL}/daily"
            params = {"guess": guess, "size": self.word_size}
        elif self.mode == "word":
            url = f"{API_BASE_URL}/word/{self.target_word}"
            params = {"guess": guess}
        else:
            raise ValueError(f"Invalid mode: {self.mode}")
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        
        result = response.json()
        return result
    
    def update_constraints(self, result: List[Dict]):
        """Update constraints based on the guess result."""
        for item in result:
            slot = item["slot"]
            letter = item["guess"]
            result_kind = item["result"]
            
            if result_kind == "correct":
                self.correct_positions[slot] = letter
                self.present_letters.add(letter)
            elif result_kind == "present":
                self.present_letters.add(letter)
                self.position_constraints[slot].add(letter)
            elif result_kind == "absent":
                # Only add to absent_letters if the letter is not also present somewhere else
                if letter not in self.present_letters:
                    self.absent_letters.add(letter)
                else:
                    # If the letter is present elsewhere but absent here, it just can't be in this position
                    self.position_constraints[slot].add(letter)
    
    def filter_candidates(self) -> List[str]:
        """Filter the word list based on current constraints."""
        candidates = []
        
        for word in self.words:
            valid = True
            
            # Check if all correct positions match
            for pos, letter in self.correct_positions.items():
                if word[pos] != letter:
                    valid = False
                    break
            
            if not valid:
                continue
            
            # Check if all present letters are in the word
            for letter in self.present_letters:
                if letter not in word:
                    valid = False
                    break
            
            if not valid:
                continue
            
            # Check if any absent letters are in the word (except for duplicates)
            for letter in self.absent_letters:
                if letter in word and letter not in self.present_letters:
                    valid = False
                    break
            
            if not valid:
                continue
            
            # Check position constraints
            for pos, letters in self.position_constraints.items():
                if word[pos] in letters:
                    valid = False
                    break
            
            if valid:
                candidates.append(word)
        
        return candidates
    
    def choose_next_guess(self, candidates: List[str]) -> str:
        """Choose the next word to guess based on the current candidates."""
        if len(candidates) <= 1:
            # If we have 0 or 1 candidates from our dictionary approach
            # Try using AI to suggest words
            ai_suggestions = self.get_ai_suggestions(num_suggestions=5)
            
            # Add valid AI suggestions that meet our constraints to candidates
            for word in ai_suggestions:
                # Verify each AI-suggested word meets our constraints
                valid = True
                
                # Check if all correct positions match
                for pos, letter in self.correct_positions.items():
                    if word[pos] != letter:
                        valid = False
                        break
                
                if not valid:
                    continue
                
                # Check if all present letters are in the word
                for letter in self.present_letters:
                    if letter not in word:
                        valid = False
                        break
                
                if not valid:
                    continue
                
                # Check position constraints
                for pos, letters in self.position_constraints.items():
                    if word[pos] in letters:
                        valid = False
                        break
                
                if valid and word not in candidates:
                    candidates.append(word)
            
        if not candidates:
            # If still no candidates, fall back to choosing a word with different letters
            unused_letters = set(string.ascii_lowercase) - self.present_letters - self.absent_letters
            
            # See if AI can suggest words that use the unused letters
            ai_suggestions = self.get_ai_suggestions(num_suggestions=5)
            if ai_suggestions:
                return ai_suggestions[0]
            
            # Find words that use the most unused letters
            best_words = []
            best_score = 0
            
            for word in self.words:
                # Skip words that have letters already marked as absent
                if any(letter in self.absent_letters and letter not in self.present_letters for letter in word):
                    continue
                
                # Count unique unused letters in the word
                unique_letters = set(word)
                unused_count = len(unique_letters.intersection(unused_letters))
                
                if unused_count > best_score:
                    best_score = unused_count
                    best_words = [word]
                elif unused_count == best_score:
                    best_words.append(word)
            
            if best_words:
                return random.choice(best_words)
            else:
                # If still no good candidates, just pick a random word
                return random.choice(self.words)
        elif len(candidates) == 1:
            # Only one candidate left - must be the answer
            return candidates[0]
        else:
            # Multiple candidates - choose one that will give the most information
            # For simplicity, just pick a random one
            return random.choice(candidates)
    
    def solve(self, max_guesses: int = 6) -> Tuple[bool, int, List[str]]:
        """
        Solve the Wordle puzzle.
        
        Returns:
            Tuple of (success, num_guesses, guesses_list)
        """
        guesses = []
        found = False
        
        # Start with a random good first word
        first_words = ["stare", "slate", "crane", "roate", "raise", "adieu"]
        if self.word_size == 5:
            current_guess = random.choice(first_words)
        else:
            # Choose a random word with a good distribution of common letters
            current_guess = random.choice(self.words)
        
        for i in range(max_guesses):
            print(f"Guess {i+1}: {current_guess}")
            guesses.append(current_guess)
            self.guesses_made += 1
            
            # Make the guess and get result
            result = self.make_guess(current_guess)
            if not result:
                print("Failed to get result from API, skipping this guess")
                continue
            
            # Check if all correct
            all_correct = all(item["result"] == "correct" for item in result)
            if all_correct:
                print(f"Found the word: {current_guess} in {i+1} guesses!")
                found = True
                break
            
            # Print the feedback for visualization
            feedback = ""
            for item in result:
                if item["result"] == "correct":
                    feedback += "🟩"  # Green for correct
                elif item["result"] == "present":
                    feedback += "🟨"  # Yellow for present
                else:
                    feedback += "⬛"  # Black for absent
            print(feedback)
            
            # Update constraints based on result
            self.update_constraints(result)
            
            # Filter candidates based on updated constraints
            candidates = self.filter_candidates()
            print(f"Remaining candidates: {len(candidates)}")
            
            # Choose next guess
            current_guess = self.choose_next_guess(candidates)
        
        if not found:
            print(f"Failed to find the word within {max_guesses} guesses.")
        
        return found, self.guesses_made, guesses
    
    def print_stats(self, found: bool, num_guesses: int):
        """Print statistics about the solve attempt."""
        if found:
            print(f"Successfully solved in {num_guesses} guesses!")
        else:
            print(f"Failed to solve within the allowed number of guesses.")


def main():
    parser = argparse.ArgumentParser(description="Solve Wordle puzzles")
    parser.add_argument("--mode", choices=["random", "daily", "word"], default="random", 
                        help="Mode to play Wordle (random, daily, or word)")
    parser.add_argument("--word", help="Target word (for 'word' mode)")
    parser.add_argument("--size", type=int, default=5, help="Word size (default: 5)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for 'random' mode (default: None)")
    parser.add_argument("--games", type=int, default=1, help="Number of games to play (default: 1)")
    parser.add_argument("--no-ai", action="store_true", help="Disable OpenAI API for word suggestions")
    parser.add_argument("--openai-api-key", type=str, default=None, help="OpenAI API Key (overrides environment variable OPENAI_API_KEY)")
    
    args = parser.parse_args()
    
    if args.mode == "word" and not args.word:
        parser.error("--word is required when mode is 'word'")
    
    total_guesses = 0
    wins = 0
    
    for game in range(args.games):
        print(f"\nGame {game+1}/{args.games}")
        solver = WordleSolver(
            word_size=args.size,
            mode=args.mode,
            target_word=args.word,
            seed=args.seed,
            cli_openai_api_key=args.openai_api_key,
            no_ai_flag=args.no_ai
        )
        
        found, num_guesses, guesses = solver.solve(max_guesses=6)
        if found:
            wins += 1
            total_guesses += num_guesses
    
    if wins > 0:
        avg_guesses = total_guesses / wins
        print(f"\nOverall Statistics:")
        print(f"Won {wins}/{args.games} games ({wins/args.games*100:.1f}%)")
        print(f"Average guesses per win: {avg_guesses:.2f}")


if __name__ == "__main__":
    main() 