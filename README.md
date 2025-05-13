# Wordle Solver: Technical Documentation

This document provides a comprehensive technical overview of the Wordle Solver program, designed to automatically solve Wordle-like puzzles by interacting with the Wordle API at [https://wordle.votee.dev:8000](https://wordle.votee.dev:8000).

## 1. Introduction

The Wordle Solver is a Python application that intelligently guesses words in a Wordle game. It employs a constraint-based filtering approach combined with an optional AI-powered suggestion engine (OpenAI's GPT-4o) to efficiently arrive at the correct solution. The program supports various game modes, word sizes, and offers reproducibility through seeding.

## 2. Features

-   **Automated Puzzle Solving**: Interacts with a Wordle API to make guesses and process feedback.
-   **Multiple Game Modes**:
    -   `random`: Solves a puzzle with a randomly selected word from the API.
    -   `daily`: Solves the API's daily puzzle.
    -   `word`: Solves a puzzle for a user-specified target word.
-   **Constraint-Based Logic**: Dynamically builds and applies constraints based on API feedback (correct letters, present letters, absent letters) to narrow down possible solutions.
-   **Intelligent Guess Selection**:
    -   Starts with common, effective opening words.
    -   Filters a dictionary of words against current constraints.
    -   Employs strategies when the dictionary yields no or few candidates.
-   **OpenAI GPT-4o Integration**: Optionally uses AI to suggest words when the dictionary-based approach struggles, significantly enhancing performance on difficult or uncommon words.
-   **Customizable Word Size**: Supports puzzles of different word lengths (default is 5).
-   **Reproducibility**: Allows seeding for consistent game outcomes in `random` mode, aiding testing and analysis.
-   **Statistics**: Tracks and displays win rates and average guesses over multiple games.
-   **Flexible Configuration**: Supports API key management via environment variables or command-line arguments.
-   **Fallback Mechanisms**: Includes a basic internal word list if NLTK is unavailable and handles API errors gracefully.

## 3. System Architecture and Code Structure

The project consists primarily of the `wordle_solver.py` script, which is the core engine.

### 3.1. `wordle_solver.py`

This script contains the main logic for the Wordle solving process.

#### 3.1.1. `WordleSolver` Class

This is the central class orchestrating the game.

**Key Instance Variables:**

-   `word_size`: Length of the target word.
-   `mode`: Current game mode ("random", "daily", "word").
-   `target_word`: The specific word to guess in "word" mode.
-   `seed`: Seed for random number generation (for API and internal choices).
-   `api_base_url`: Base URL for the Wordle API.
-   `openai_api_url`: URL for the OpenAI API.
-   `openai_api_key`: API key for OpenAI.
-   `use_ai`: Boolean indicating if AI assistance is enabled.
-   `words`: List of potential words (dictionary).
-   **Constraint Tracking Data Structures:**
    -   `correct_positions` (dict): `{position_index: letter}` for letters in the correct spot.
    -   `present_letters` (set): Set of letters known to be in the word but whose correct position is not yet known or they are in a wrong guessed spot.
    -   `absent_letters` (set): Set of letters confirmed not to be in the word.
    -   `position_constraints` (dict): `{position_index: set(letters_not_in_this_position)}` for letters known not to be at a specific spot (typically used for "present" letters).

**Key Methods:**

-   `__init__(...)`: Initializes game parameters, loads the dictionary, configures API keys, and sets up the initial seed.
-   `load_dictionary()`: Loads words, preferring NLTK's corpus and falling back to `get_basic_word_list()`.
-   `get_basic_word_list()`: Provides a hardcoded list of common English words as a fallback.
-   `make_guess(guess: str)`: Sends a guess to the Wordle API and returns the feedback.
-   `update_constraints(result: List[Dict])`: Parses API feedback and updates `correct_positions`, `present_letters`, `absent_letters`, and `position_constraints`.
-   `filter_candidates()`: Filters `self.words` against all current constraints to produce a list of valid candidate words.
-   `get_ai_suggestions(num_suggestions: int)`: Constructs a prompt based on current constraints and queries the OpenAI API for word suggestions.
-   `choose_next_guess(candidates: List[str])`: Selects the best word for the next guess from the filtered candidates, potentially using AI suggestions if candidates are scarce.
-   `solve(max_guesses: int)`: Manages the main game loop, making guesses, updating constraints, and determining game outcome.
-   `print_stats(found: bool, num_guesses: int)`: Prints statistics for a single game.

#### 3.1.2. `main()` function

-   Parses command-line arguments using `argparse`.
-   Initializes and runs one or more `WordleSolver` games based on arguments.
-   Collects and prints overall statistics for multiple games.

### 3.2. `requirements.txt`

Specifies project dependencies:
-   `requests`: For making HTTP requests to the Wordle and OpenAI APIs.
-   `nltk`: (Natural Language Toolkit) For accessing a comprehensive list of English words.
-   `openai`: Python client library for the OpenAI API.

## 4. Setup and Installation

### 4.1. Prerequisites

-   Python 3.6+
-   Git (for cloning the repository)

### 4.2. Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    This will install `requests`, `nltk`, and `openai`. The first time NLTK is used, it might attempt to download the 'words' corpus if not already present (handled quietly by `nltk.download('words', quiet=True)` in the script).

### 4.3. API Key Configuration

AI-powered suggestions require an OpenAI API key.

-   **Environment Variable (Recommended):**
    Set the `OPENAI_API_KEY` environment variable:
    ```bash
    export OPENAI_API_KEY="your_openai_api_key"
    ```
-   **Command-Line Argument:**
    Pass the key using the `--openai-api-key` argument when running `wordle_solver.py`:
    ```bash
    python wordle_solver.py --openai-api-key "your_openai_api_key"
    ```
    The command-line argument takes precedence if both are set.
-   If no key is provided and AI is not disabled (`--no-ai`), AI features are turned off, and a warning is displayed.

## 5. Usage

### 5.1. Running the Solver (`wordle_solver.py`)

**Basic Usage (Random 5-letter word):**
```bash
python wordle_solver.py
```

**Command-Line Options:**

The script accepts several arguments to customize its behavior:

-   `--mode {random|daily|word}`: Game mode (default: `random`).
-   `--word TARGET_WORD`: Specifies the target word when `--mode word` is used. Required for word mode.
-   `--size N`: Sets the word length (default: 5).
-   `--seed N`: Provides a seed for random number generation. Ensures reproducibility in `random` mode for both API word selection and solver's internal choices. If not provided in `random` mode, an internal seed is generated for the current game session.
-   `--games N`: Number of games to play for statistical analysis (default: 1).
-   `--no-ai`: Disables OpenAI integration, relying solely on the dictionary.
-   `--openai-api-key YOUR_KEY`: Directly provides the OpenAI API key, overriding the environment variable.

**Examples:**

-   Solve the daily puzzle:
    ```bash
    python wordle_solver.py --mode daily
    ```
-   Solve for a specific 6-letter word "player" without AI:
    ```bash
    python wordle_solver.py --mode word --word player --size 6 --no-ai
    ```
-   Play 5 random games with a specific seed:
    ```bash
    python wordle_solver.py --games 5 --seed 42
    ```

## 6. Detailed Algorithm and Logic

The `WordleSolver` employs a systematic approach to deduce the target word.

### 6.1. Initialization (`__init__`)

1.  **Parameter Setup**: Stores `word_size`, `mode`, `target_word`, etc.
2.  **Seed Management**:
    -   If a `seed` is provided via CLI, it's used directly.
    -   If `mode` is "random" and no CLI `seed` is given, a random seed is generated internally for the current game session. This ensures that all API calls for `/random` within this single game instance use the same seed, guaranteeing a consistent target word for that game.
    -   Python's `random` module is then seeded with this definitive game seed, ensuring deterministic internal choices (e.g., first guess selection, tie-breaking).
3.  **API Configuration**: Sets up API URLs and resolves the OpenAI API key (CLI > environment variable). Determines `self.use_ai`.
4.  **Dictionary Loading (`load_dictionary`)**:
    -   Attempts to import `nltk` and download/load the 'words' corpus. Filters for words of `self.word_size` that are purely alphabetical.
    -   If NLTK fails (e.g., import error, download issue), it calls `get_basic_word_list()` which returns a predefined list of common English words, filtered by `self.word_size`.
    -   The loaded list is stored in `self.words`.
5.  **Constraint Initialization**:
    -   `correct_positions` (dict): `{}`
    -   `present_letters` (set): `set()`
    -   `absent_letters` (set): `set()`
    -   `position_constraints` (dict): `{i: set() for i in range(word_size)}`

### 6.2. Guessing Loop (`solve` method)

The `solve` method iterates up to `max_guesses`.

1.  **First Guess Selection**:
    -   If `word_size` is 5, a good starting word (e.g., "stare", "crane") is chosen randomly from a predefined list.
    -   For other word sizes, a random word is chosen from `self.words`.
    (This choice is deterministic if Python's `random` module has been seeded).

2.  **API Interaction (`make_guess`)**:
    -   Constructs the appropriate API URL based on `self.mode`:
        -   `/random?guess=WORD&size=SIZE[&seed=SEED]`
        -   `/daily?guess=WORD&size=SIZE`
        -   `/word/TARGET?guess=WORD`
    -   Sends a GET request to the Wordle API.
    -   Handles potential HTTP errors from the API.
    -   Parses the JSON response, which is a list of dictionaries, each representing a letter in the guess: `[{"slot": 0, "guess": "s", "result": "absent"}, ...]`.

3.  **Constraint Updating (`update_constraints`)**:
    Iterates through the API feedback for each letter of the guess:
    -   If `result` is "correct":
        -   `self.correct_positions[slot] = letter`
        -   `self.present_letters.add(letter)`
    -   If `result` is "present":
        -   `self.present_letters.add(letter)`
        -   `self.position_constraints[slot].add(letter)` (letter is in word, but not at this slot)
    -   If `result` is "absent":
        -   If `letter` is *not* in `self.present_letters` (i.e., it's not a duplicate of a letter already known to be present elsewhere):
            -   `self.absent_letters.add(letter)`
        -   Else (letter *is* in `self.present_letters` but marked "absent" for *this specific slot*):
            -   `self.position_constraints[slot].add(letter)` (this instance of the letter is not at this slot)

4.  **Candidate Filtering (`filter_candidates`)**:
    Iterates through `self.words` (the full dictionary) and retains only those words that satisfy *all* current constraints:
    -   Must match all letters in `self.correct_positions`.
    -   Must contain all letters in `self.present_letters`.
    -   Must *not* contain any letter from `self.absent_letters` (unless that letter is also in `self.present_letters`, handling cases of duplicate letters where one is correctly placed/present and another instance is absent).
    -   Must *not* have a letter at a position `pos` if that letter is in `self.position_constraints[pos]`.
    The result is a new list of candidate words.

5.  **Next Guess Selection (`choose_next_guess`)**:
    -   **AI Intervention (Primary)**: If `len(candidates) <= 1` (meaning dictionary approach yields few or no options) and AI is enabled, `get_ai_suggestions()` is called.
        -   AI-suggested words are validated against current constraints. Valid suggestions are added to the `candidates` list if not already present.
    -   **No Candidates**: If `candidates` is still empty after potential AI input:
        -   Another attempt with `get_ai_suggestions()` is made. If successful, the first AI suggestion is returned.
        -   If AI fails or is disabled, it tries to pick a word from `self.words` that introduces the most new, unconfirmed letters (letters not in `present_letters` or `absent_letters`).
        -   If all else fails, a random word from `self.words` is chosen as a last resort.
    -   **One Candidate**: If `len(candidates) == 1`, this word is chosen.
    -   **Multiple Candidates**: If `len(candidates) > 1`, one is chosen randomly from the candidates. (This is an area for future improvement, e.g., picking a word that maximizes information gain).

6.  **Game Completion**:
    -   If all letters in a guess are "correct", the game is won.
    -   If `max_guesses` is reached without a win, the game is lost.
    -   Statistics (`guesses_made`) are updated.

## 7. AI Integration (OpenAI GPT-4o)

When `use_ai` is true and an API key is available, the solver can leverage GPT-4o.

### 7.1. Triggering Condition

AI is primarily consulted via `get_ai_suggestions()` within `choose_next_guess()` when the standard dictionary filtering results in one or zero candidates. It's also consulted as a fallback if no candidates are found at all.

### 7.2. Prompt Engineering (`get_ai_suggestions`)

A detailed prompt is constructed to provide the AI with the current state of knowledge:

1.  **Base Instruction**: "I'm playing a Wordle game with a {self.word_size}-letter word. Please help me find the most likely word based on these constraints:"
2.  **Correct Positions**: If any, e.g., "Correct positions: _ L E _ _"
3.  **Present Letters**: If any, e.g., "Letters that are in the word but in wrong positions: A, P"
4.  **Absent Letters**: If any, e.g., "Letters that are NOT in the word: S, T, O, R"
5.  **Position Constraints**: If any, detailing letters that cannot be at specific positions, e.g.:
    "Position constraints:
    Position 1: Cannot contain A
    Position 3: Cannot contain P"
6.  **Request for Output**: "Please give me the {num_suggestions} most likely {self.word_size}-letter words that match these constraints, one per line. Only include valid English words."

### 7.3. OpenAI API Call

-   **Endpoint**: `self.openai_api_url` (defaults to `https://api.openai.com/v1/chat/completions`).
-   **Model**: `gpt-4o`.
-   **Messages**:
    -   System Role: "You are a helpful assistant that provides word suggestions for Wordle."
    -   User Role: The dynamically generated prompt.
-   **Parameters**: `temperature` (0.7 for some creativity), `max_tokens`.
-   **Authentication**: `Authorization: Bearer {self.openai_api_key}`.

### 7.4. Response Processing

1.  The AI's response (expected to be a list of words, one per line) is parsed.
2.  Each suggested word is cleaned (stripped, lowercased, checked for alpha characters and correct length).
3.  These raw suggestions are then *further validated* by `choose_next_guess` against the solver's strict current constraints (`correct_positions`, `present_letters`, `position_constraints`) before being added to the pool of `candidates`. This ensures AI suggestions adhere to known facts.

## 8. Error Handling and Fallbacks

-   **NLTK Unavailability**: If `nltk` or its 'words' corpus cannot be loaded, `load_dictionary()` catches the exception and calls `get_basic_word_list()`, ensuring the solver has a functional, albeit smaller, word list. A message is printed to the console.
-   **Wordle API Errors**: `make_guess()` checks for non-200 HTTP status codes. If an error occurs, it prints the status and error text, and returns `None`. The main `solve()` loop will then skip updating constraints for that failed guess and proceed.
-   **OpenAI API Errors**: `get_ai_suggestions()` uses a try-except block. If the API call fails (e.g., network issue, invalid key, non-200 status), it prints an error and returns an empty list, allowing the solver to proceed without AI help for that turn.
-   **No Candidate Words**: `choose_next_guess()` has multiple fallbacks:
    1.  Try AI.
    2.  If AI fails or is disabled, try to pick a word from the original dictionary that reveals the most new information.
    3.  As a last resort, pick a completely random word from the original dictionary. This ensures the game can always proceed with a guess.

## 9. Potential Future Enhancements

-   **Advanced Guessing Strategy**: Implement a more sophisticated algorithm for `choose_next_guess` when multiple candidates exist, such as selecting the word that is statistically likely to reduce the number of possible candidates the most (e.g., based on letter frequency in remaining candidates).
-   **Improved Dictionary Management**: Allow users to provide custom dictionary files.
-   **Graphical User Interface (GUI)**: Develop a GUI for a more interactive user experience.
-   **Extended API Support**: Adapt the solver for different Wordle-like game APIs or variants.
-   **Performance Optimization**: For very large dictionaries or extremely complex constraint sets, further optimization of the filtering logic could be explored.
-   **Interactive Mode**: Allow a human to play, with the solver providing suggestions. 