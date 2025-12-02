
### `README.md`

````markdown
# 🧭 Artemis: AI-Powered Career Compass

Artemis is a sophisticated, multimodal Streamlit application designed to provide personalized, future-focused career guidance. It leverages the **Gemini 2.5 Flash** model with **Google Search grounding** and psychological profile analysis (**RIASEC**) to offer tailored career pathways, complete with salary ranges, growth insights, and immediate next steps.

---

## ✨ Features

* **Multimodal Input:** Analyze user-provided text background (skills, interests, education) alongside an optional CV/resume image for comprehensive profile assessment.
* **Psychological Filtering (RIASEC):** Careers are filtered and suggested based on the user's selected Holland Code 

[Image of the Holland Code Hexagon]
 for better job-personality alignment.
* **Academic Level Adjustment:** Recommendations are tailored to the user's current stage (e.g., Entry-Level, Advanced Degree, Experienced Professional) to ensure realistic job suggestions.
* **Real-time Grounding:** Uses the Gemini API's integrated Google Search tool to provide up-to-date information on salary ranges and job growth trends.
* **Refinement Loop:** Allows users to refine their analysis based on feedback (e.g., "Exclude technical roles") to generate a single, highly tuned career suggestion.
* **Intuitive Wizard UI:** A four-step navigation process makes input collection clear and user-friendly.

---

## ⚙️ Architecture

Artemis is built as a single-file Streamlit application, utilizing external APIs for its core intelligence.

### System Flow

The process begins with the user providing multimodal input (text and optional image) via the Streamlit UI. This request is sent to the Gemini API, which uses the internal `Google Search` tool for data grounding before returning a structured analysis back to the UI.



### Project Files

| File Name | Purpose |
| :--- | :--- |
| `main.py` | The main Streamlit application script containing all logic and UI. |
| `requirements.txt` | Lists all necessary Python dependencies (for installation). |
| `.env` | Stores the confidential Gemini API Key (for local development). |

---

## 🚀 Installation and Setup

### Prerequisites

* **Python:** Python 3.8+ is required.
* **API Key:** A Gemini API Key.

### Step 1: Install Dependencies

Assuming your project files (`main.py`, `.env`, `requirements.txt`) are in the root folder, run:

```bash
# Install the necessary Python packages
pip install -r requirements.txt
````

### Step 2: Set Up Environment Variables

The `.env` file should be located directly alongside `main.py` and contain your API key:

```env
# .env file
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

> **Note:** If running in a cloud environment (like Google Cloud Canvas), the API key is typically injected at runtime via secrets management, and the local `.env` file may be optional.

### Step 3: Run the Application

Execute the Streamlit app directly from your root project folder:

```bash
streamlit run main.py
```

The application will open in your web browser.

-----

## 📝 Usage

The application follows a simple four-step wizard:

1.  **Start Journey:** Click the main CTA button on the welcome page.
2.  **Step 1 (Foundation):** Input your academic level and provide a detailed text background of your skills and interests.
3.  **Step 2 (Context):** Select a primary **RIASEC Personality Code** and optionally upload an image file of your CV/resume for multimodal analysis.
4.  **Step 3 (Generate):** Review your inputs and click **"START AI ANALYSIS"** to generate the three personalized career paths.
5.  **Step 4 (Analysis):** View the three suggestions. Use the **"Refine Latest Suggestion"** input box to provide feedback and receive a single, highly targeted career path based on your new input.

-----

## 👤 Created By

Amina Atta

```
```
