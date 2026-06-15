# Coursera Transcript Scraper & PDF Generator

This project automates the process of collecting transcripts from Coursera courses and compiling them into a clean, searchable PDF. It handles course navigation, transcript extraction, checkpointing, and PDF generation automatically.

I originally built it for personal use because manually copying and pasting transcripts from individual lectures into AI tools for summaries and notes became repetitive and time-consuming. The scraper can process an entire course and generate a single PDF containing all available lecture transcripts and reading materials, making it much easier to review course content or use it as input for note-taking and AI-assisted study workflows.

## Prerequisites

1. **Python 3.x**: Ensure you have Python installed.
2. **Google Chrome**: Google Chrome must be installed on your system, as this script uses Selenium to drive it.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/rajdhakad9826/coursera-scraper.git
   cd coursera-scraper
   ```
2. **(Recommended) Create a virtual environment:**

   ```bash
   # Linux/macOS
   python3 -m venv coursera-env

   # Windows
   python -m venv coursera-env
   ```

3. **Activate the virtual environment:**

   **Linux/macOS**
   ```bash
   source coursera-env/bin/activate
   ```
   **Windows (Command Prompt)**
   ```cmd
   coursera-env\Scripts\activate
   ```
   **Windows (PowerShell)**
   ```powershell
   .\coursera-env\Scripts\Activate.ps1
   ```

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script:

```bash
python coursera_transcript_scraper.py
```

The script will prompt you for the URL of the course you want to scrape (e.g., `https://www.coursera.org/learn/machine-learning`).

## Login

The script will open a browser window and navigate to the Coursera login page. You will need to manually log in using your credentials. This ensures a reliable login process, especially when dealing with 2FA, CAPTCHAs, or other security checks.

After you have successfully logged in, return to the terminal and press ENTER. The scraper will then automatically continue and handle everything else.
### How it works

1. **Login**: The script opens a browser for you to manually log into your Coursera account.
2. **Navigation**: It automatically navigates through the course modules to collect all lecture links.
3. **Scraping**: It visits each lecture page and extracts the transcript text.
4. **PDF Generation**: It compiles all extracted transcripts into a formatted PDF file (default: `coursera_transcripts.pdf`).

## Supported Content Types

- Video lectures transcripts
- Reading materials
- Ungraded Labs

### Resuming Progress

The script saves a checkpoint file (`coursera_transcripts_checkpoint.json`) after scraping each lecture. If the script is interrupted, running it again for the same course will automatically resume from the last saved checkpoint, skipping already scraped lectures.


## Output

- `coursera_transcripts.pdf`: The final compiled PDF containing all scraped transcripts.
- `coursera_transcripts_checkpoint.json`: A temporary JSON file used for resuming progress.

## Disclaimer

This script is for personal use and educational purposes only. Please respect Coursera's terms of service and content copyrights.

This tool is designed to help learners access transcripts for note-taking and revision, not for content redistribution.