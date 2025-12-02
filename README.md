🧭 Artemis: AI-Powered Career Compass

Artemis is a sophisticated, multimodal Streamlit application designed to provide personalized, future-focused career guidance. It leverages the Gemini API with Google Search grounding and psychological profile analysis (RIASEC) to offer three tailored career pathways, complete with salary ranges, growth insights, and immediate next steps.

✨ Features

Multimodal Input: Analyze user-provided text background (skills, interests, education) alongside an optional CV/resume image for comprehensive profile assessment.

Psychological Filtering (RIASEC): Careers are filtered and suggested based on the user's selected Holland Code (Realistic, Investigative, Artistic, Social, Enterprising, Conventional) for better job-personality alignment.

Academic Level Adjustment: Recommendations are tailored to the user's current stage (e.g., Entry-Level, Advanced Degree, Experienced Professional) to ensure realistic job suggestions.

Real-time Grounding: Uses Google Search grounding via the Gemini API to provide up-to-date information on salary ranges and job growth trends.

Refinement Loop: Allows users to refine their analysis based on feedback (e.g., "Exclude technical roles") to generate a single, highly tuned career suggestion.

Intuitive Wizard UI: A step-by-step navigation process makes input collection clear and user-friendly.

⚙️ Architecture

Artemis is built as a single-file Streamlit application, utilizing external APIs for its core intelligence.

Component

Technology / Service

Function

Frontend/UI

Streamlit

Handles all user interaction, layout, and session state management.

Core AI Logic

gemini-2.5-flash-preview-09-2025

Parses multimodal input (text + image), applies persona, and generates structured career analysis.

Data Grounding

Gemini API (tools: {"google_search": {}})

Ensures all career names, salaries, and growth information are sourced from current web data.

Styling

Custom CSS

Provides dynamic color themes based on the selected RIASEC trait and a professional look-and-feel.

🚀 Installation and Setup

Prerequisites

Python: Python 3.8+ is required.

API Key: A Gemini API Key.

Step 1: File Restructure (Local Action)

The project files (main.py, .env, requirements.txt) should be located directly in the root project folder (Artemis-Career-Compass).

Step 2: Install Dependencies (from the root project folder)

Assuming your environment files are now in the root:

# Install the necessary Python packages
pip install streamlit python-dotenv requests


Step 3: Set Up Environment Variables (in the root folder)

The .env file should be located directly alongside main.py in the root project folder and contain your API key:

# .env file
GEMINI_API_KEY="YOUR_API_KEY_HERE"



(Note: If running in an environment like Google Cloud Canvas, the API key is typically injected at runtime and the .env file is optional.)

Step 4: Run the Application (from the root folder)

Execute the Streamlit app directly:

streamlit run main.py




The application will open in your web browser.

📝 Usage

Start Journey: Click the main CTA button on the welcome page.

Step 1 (Foundation): Input your academic level (e.g., Experienced Professional) and provide a detailed text background of your skills and interests.

Step 2 (Context): Select a primary RIASEC Personality Code (e.g., Enterprising) and optionally upload an image file of your CV/resume for multimodal analysis.

Step 3 (Generate): Review your inputs and click "START AI ANALYSIS" to generate the three personalized career paths.

Step 4 (Analysis): View the three suggestions. Use the "Refine Latest Suggestion" input box to provide feedback and receive a single, highly targeted career path based on your new input.

👤 Created By

Amina Atta