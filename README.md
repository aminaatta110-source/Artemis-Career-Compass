

# 🧭 Artemis: AI-Powered Career Compass

**Artemis** is a sophisticated, multimodal **Streamlit application** designed to provide personalized, future-focused career guidance. It leverages the **Gemini API with Google Search grounding**, psychological profiling (RIASEC), and refinement logic to deliver **three tailored career pathways**—each with salary insights, growth trends, and actionable next steps.

---

## ✨ Features

### 🔍 Multimodal Profiling

Analyze user-provided **text background** (skills, interests, education) plus an **optional CV/resume image** for a deeper profile.

### 🧠 RIASEC Personality Filtering

Career options are aligned with the user’s selected **Holland Code**:
Realistic • Investigative • Artistic • Social • Enterprising • Conventional.

### 🎓 Academic Level Adjustment

The system customizes recommendations based on whether the user is:

* Entry-Level
* Undergraduate
* Graduate
* Advanced Degree
* Experienced Professional

### 🌐 Real-Time Data Grounding

Uses **Gemini API + Google Search** to provide **fresh salary ranges, descriptions, and job outlook**.

### 🔄 Refinement Loop

Users can refine the generated analysis (e.g., “exclude technical roles”) to produce a **single, deeply tailored** career pathway.

### 🧭 Wizard-Style User Interface

A clean, intuitive, step-by-step experience using **Streamlit session state**.

---

## ⚙️ Architecture

Artemis is built as a **single-file Streamlit project**, using external APIs for intelligence.

| Component          | Technology / Service          | Purpose                                  |
| ------------------ | ----------------------------- | ---------------------------------------- |
| **Frontend/UI**    | Streamlit                     | Layout, navigation, wizard flow          |
| **Core AI Logic**  | Gemini 2.5 Flash              | Career generation + multimodal reasoning |
| **Data Grounding** | Gemini API with Google Search | Salary + job outlook                     |
| **Styling**        | Custom CSS                    | Dynamic colors based on RIASEC trait     |

---

## 🚀 Installation & Setup

### **Prerequisites**

* Python **3.8+**
* A **Gemini API Key**

---

### **Step 1: Project Structure (Root Folder)**

Your project should look like this:

```
Artemis-Career-Compass/
│── main.py
│── .env
│── requirements.txt
```

---

### **Step 2: Install Dependencies**

```bash
pip install streamlit python-dotenv requests
```

---

### **Step 3: Environment Variables**

In your **.env** file located in the root:

```
GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

*(If deployed on systems like Google Cloud Canvas, the key may auto-inject.)*

---

### **Step 4: Run the Application**

Run this from the project root:

```bash
streamlit run main.py
```

The app will automatically open in your web browser.

---

## 📝 Usage Guide

### **1. Start Journey**

Click the CTA button on the home screen.

### **2. Step 1 (Foundation)**

Provide:

* Academic level
* Detailed background (skills, interests, education)

### **3. Step 2 (Context)**

Select:

* RIASEC personality code
* Optional resume/CV image upload

### **4. Step 3 (Generate)**

Review inputs → click **START AI ANALYSIS**.

### **5. Step 4 (Career Analysis)**

Receive:

* Three personalized career suggestions
* Salary + growth data
* Clear next-step actions
* Option to **refine** results for a deeper-targeted suggestion

---

## 👤 Created By

**Amina Atta**

---


