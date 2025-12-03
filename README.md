

# 🧭 Artemis: AI-Powered Career Compass

## 👤 Author & Repository Information

**Name:** AMINA ATTA

**GitHub Repository:** *[Artemis-Career-Compass](https://github.com/aminaatta110-source/Artemis-Career-Compass/tree/main)*

---

## 🚀 Overview

Artemis is a Generative AI-powered Streamlit web app developed during the **GenAI Foundation Program**. It provides **personalized, future-ready career guidance** based on your skills, interests, education level, and personality traits — using **Google’s Gemini 2.5 Flash API (gemini-2.5-flash-preview-09-2025)**.

Designed for **students**, **professionals**, and **career explorers**, Artemis blends multimodal inputs with search-grounded data to generate actionable career strategies.

---

## ✨ Key Features

* **AI-Powered Career Advice:** Tailored recommendations using RIASEC personality alignment and skill relevance.
* **Bold Titles & Rich Descriptions:** Clear explanations of job roles, market demand, growth path, and required skills.
* **Clickable Resource Links:** Search-grounded links for job outlook and salary validation.
* **Session History:** Saves all career explorations for easy comparison and review.
* **Secure API Key Handling:** `.env` for local — `secrets.toml` for deployment — no hardcoded secrets.
* **Modern UI:** Responsive step-by-step wizard with dynamic color coding and clean layout.

---

## 🔧 How It Works

| Step                       | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| **1️⃣ Input**              | User provides skills, interests, education, and optional CV/resume image |
| **2️⃣ Prompt Engineering** | App builds a structured multimodal prompt                                |
| **3️⃣ Model Processing**   | Gemini analyzes data + performs grounded search                          |
| **4️⃣ Output Generation**  | 3 best-fit careers with skills, fit level & next steps                   |
| **5️⃣ Display & History**  | Clear interactive cards + saved session data                             |
| **6️⃣ Refinement**         | Users can request improved/adjusted results                              |

---

## 📌 Use Cases

✔ **Students** — plan future careers & study paths
✔ **Professionals** — explore role transition or upskilling options
✔ **Career Counselors** — use as a fast, data-assisted advising companion

---

## 🖥️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/aminaatta110-source/Artemis-Career-Compass.git
cd Artemis-Career-Compass
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows:**

```bash
.venv\Scripts\activate
```

**Mac/Linux:**

```bash
source .venv/bin/activate
```

### 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

### 4️⃣ Add Gemini API Key

Local (`.env` file):

```
GEMINI_API_KEY="your_gemini_key_here"
```

Streamlit Cloud:

```
# .streamlit/secrets.toml
GEMINI_API_KEY = "your_gemini_key_here"
```

### 5️⃣ Run the App

```bash
streamlit run main.py
```

Then open the localhost link in your browser 🌐

---

## 🛠️ Tech Stack

| Component | Technology               |
| --------- | ------------------------ |
| Language  | Python 3.8+              |
| Framework | Streamlit                |
| AI Model  | Google Gemini 2.5 Flash  |
| Grounding | Google Search Tool       |
| Tools     | dotenv, requests, base64 |

---

## 🔐 Security & Privacy

* No personal data stored — only used transiently for generating results
* API key is never exposed publicly
* Suitable for education & internal use-cases

---

## ⚠️ Deployment & API Notes

* Gemini API has **usage limits**
* High traffic may cause temporary downtime
* If you fork the repo → **add your own API key**

---

## 📝 License

This project is licensed under the **MIT License**.
Use, modify, and expand freely!

---

## 🙌 Credits

Artemis integrates with **Google Gemini (Generative Language API)**.
Inspired by this open-source initiative:
[https://github.com/jeevandeepsaini/Career-Guidance-ChatBot/tree/main](https://github.com/jeevandeepsaini/Career-Guidance-ChatBot/tree/main)

---

### 💡 Created with passion by **Amina Atta**

---
