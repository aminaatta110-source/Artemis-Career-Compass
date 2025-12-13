import streamlit as st
import os
import requests
import json
from dotenv import load_dotenv
from base64 import b64encode
import time
import re # <-- Added import for robust link parsing

# --- Setup ---
load_dotenv()

# Use an empty string for API key if not defined, allowing Canvas to inject it
api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")

# Set api_key to empty string if still none, relying on the environment
if not api_key:
    api_key = ""    
    st.error("⚠️ **API Key Missing!** Please ensure you have created the **.env** file (local) or set your secrets (cloud).")

# Use the latest recommended model for general tasks
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

# Define the constant conclusion text for robust post-processing cleanup
CONCLUSION_TEXT = "Future success awaits those who specialize—start learning the critical next skill now."

def convert_markdown_to_html(markdown_content: str) -> str:
    """
    Simpler and more robust conversion of the LLM's structured Markdown 
    (### headings and * lists) and bolding (**) into HTML for guaranteed rendering,
    including link conversion.
    """
    html_content = markdown_content.strip()
    
    # 1. Hyperlink Conversion: Convert [Link Text](URL) to <a href="URL">Link Text</a>
    # This must happen first to correctly parse the URL structure before splitting lines.
    # Added target="_blank" for user experience
    html_content = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', html_content)
    
    lines = html_content.split('\n')
    new_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        if not stripped_line:
            continue
            
        content = stripped_line
        
        # 2. Bolding Conversion: Convert **text** to <strong>text</strong>
        # Simple implementation for pairs of **
        parts = content.split('**')
        processed_content = []
        for i, part in enumerate(parts):
            if i % 2 == 1:
                processed_content.append(f'<strong>{part}</strong>')
            else:
                processed_content.append(part)
        content = "".join(processed_content)


        # 3. Handle H3 headings (###) - MODIFIED TO GUARANTEE SALARY BRACKETS
        if content.startswith('### '):
            heading_text = content[4:].strip()
            
            # Look for the last dash/bracket for the salary split
            if ' - ' in heading_text:
                title_raw, salary_raw = heading_text.rsplit(' - ', 1)
                
                # 1. Clean up Salary: Remove any accidental brackets or common prefixes
                salary_text = salary_raw.strip('[] ')
                salary_text = re.sub(r'^(Salary: |Salaries: |Salary:)\s*', '', salary_text, flags=re.IGNORECASE) 
                
                # 2. Construct the final HTML, guaranteeing the format [Salary: $Xk-$Yk]
                guaranteed_salary_display = f'[Salary: {salary_text}]'
                
                new_lines.append(f'<h3>{title_raw} <span class="salary-tag"> - {guaranteed_salary_display}</span></h3>')
            else:
                new_lines.append(f'<h3>{heading_text}</h3>')
        
        # 4. Handle list items (*)
        elif stripped_line.startswith('* '):
            # Strip the leading '* ' and wrap in <li>
            list_content = content[2:].strip()
            # Handle the 🔗 icon presentation
            list_content = list_content.replace('🔗 ', '<span style="font-size:1.2em;">🔗</span> ')
            new_lines.append(f'<li>{list_content}</li>')
        
        # 5. Handle paragraph text (conclusion, etc.)
        else:
            new_lines.append(f'<p>{content}</p>')

    # 6. Wrap list items in <ul>. This is the cleaner, reliable post-processing logic.
    final_html = '\n'.join(new_lines)
    wrapped_content = []
    in_list = False
    
    for line in final_html.split('\n'):
        if line.startswith('<li>'):
            if not in_list:
                wrapped_content.append('<ul>')
                in_list = True
            wrapped_content.append(line)
        else: # Found a non-<li> element (like <h3> or <p>)
            if in_list:
                wrapped_content.append('</ul>')
                in_list = False
            wrapped_content.append(line)

    if in_list:
        wrapped_content.append('</ul>')
    
    # Remove unwanted empty lines that might have appeared during list wrapping
    return '\n'.join([line for line in wrapped_content if line.strip()])


def display_markdown_in_styled_box(markdown_content):
    """
    Pre-converts the markdown content to HTML and displays it inside the custom 'result-box' div.
    This uses a single st.markdown call with the pre-converted HTML for reliable rendering.
    """
    # 1. Convert the LLM's Markdown output into reliable HTML
    html_content = convert_markdown_to_html(markdown_content)
    
    # 2. Inject the HTML into the styled div in a single call
    st.markdown(f"""
<div class='result-box'>
{html_content}
</div>
    """, unsafe_allow_html=True)


def get_image_part(uploaded_file):
    """Converts a Streamlit uploaded file to the required base64 inlineData format."""
    if uploaded_file is None:
        return []
    
    # Reset the file pointer to the beginning for reading
    uploaded_file.seek(0)
    image_bytes = uploaded_file.read()
    base64_image = b64encode(image_bytes).decode('utf-8')
    
    return [
        {
            "inlineData": {
                "mimeType": uploaded_file.type,
                "data": base64_image
            }
        }
    ]

def clear_history():
    """Rests the history list and clears input text boxes."""
    st.session_state.history = []
    st.session_state.user_input_key = ""
    st.session_state.refine_input_key = ""
    st.session_state.academic_level = "Entry-Level / Training"
    st.session_state.personality_select = "None" # Reset personality
    st.session_state.uploaded_file_data = None # Clear uploaded file
    st.session_state.step = 1
    st.rerun()

def go_home():
    """Returns to the welcome screen and resets color theme."""
    st.session_state.step = 0
    st.session_state.personality_select = "None" # Reset personality to remove color
    st.session_state.user_input_key = "" # Clear text input
    st.session_state.academic_level = "Entry-Level / Training" # Reset academic level
    st.session_state.uploaded_file_data = None # Clear uploaded file
    st.rerun() # Rely on global scroll fix

def get_career_guidance(prompt_text: str, image_part: list = [], refine_mode: bool = False) -> str:
    """Sends prompt and optional image data to the Gemini API with Google Search grounding."""
    
    # Determine CV status (needed for both regular and refine mode)
    cv_uploaded = len(image_part) > 0
    cv_line = f"* **CV Analysis:** Relevant experience from resume" if cv_uploaded else ""

    # --------------------------------------------------------------------------------
    # System instruction setup
    # --------------------------------------------------------------------------------
    if refine_mode:
        # Enforcing the structured list format for the single refined output
        system_instruction = f"""
        You are a specialized career expert. Refine the previous career suggestion based on the new user input/feedback. 

        **CRITICAL:** Provide ONLY ONE updated career path. You MUST adhere to the following Markdown format precisely:

        ### [Job Title] - [Salary: $Xk-$Yk]
        * **Level Fit:** Why this suits {st.session_state.academic_level}
        * **Background Match:** How their skills/education apply
        {cv_line}
        * **Personality Alignment:** Connection to {st.session_state.personality_select}
        * **Next Step:** One essential action to start
        * 🔗 [Search Job Growth](https://www.google.com/search?q=job+growth+[Job Title])

        **IMPORTANT:** Do NOT add any introductory paragraph or explanatory text before the career suggestion. Start directly with the ### heading.
        
        End with: "{CONCLUSION_TEXT}"
        """
    else:
        # Original system instruction for 3 careers, MODIFIED TO INCLUDE INTRO PARAGRAPH
        cv_instructions = ""
        if cv_uploaded:
            cv_instructions = """
            **CV ANALYSIS IS MANDATORY:** A CV/resume has been uploaded. You MUST extract and use information from it, even if it contradicts or adds to the text background.
            **CV Match:** Specifically mention how their CV experience/degree supports this career path.
            """
        else:
            cv_instructions = """
            **NO CV UPLOADED:** Focus only on the text background provided by the user.
            """
            
        system_instruction = f"""
        You are a **Future-Ready Career Strategist** specializing in ALL career fields and industries.

        **CRITICAL REQUIREMENT - ADJUST FOR ACADEMIC LEVEL:**
        The user is at: **{st.session_state.academic_level}**
        You MUST tailor career suggestions to be realistic and appropriate for this level:

        - **Entry-Level / Training**: Suggest starter positions, certificates, apprenticeships, on-the-job training
        - **Current Student (Undergraduate)**: Focus on internships, graduate programs, entry-level roles matching their studies 
        - **Advanced Degree (Graduate)**: Recommend specialized, research-oriented, or leadership roles requiring advanced education
        - **Experienced Professional**: Suggest career advancement, management, specialization leveraging experience
        - **Seeking Career Pivot**: Propose transitional roles, reskilling paths, transferable skills applications

        **Combine ALL information:**
        1. Academic Level: {st.session_state.academic_level}
        2. RIASEC Personality: {st.session_state.personality_select}
        3. User Background: [from text]
        {cv_instructions}

        **CAREER SCOPE: OPEN TO ALL FIELDS**
        - Suggest careers from **ANY industry** that matches their background, personality, AND academic level
        - Include technology, healthcare, education, arts, sciences, business, engineering, social services, etc.
        - Focus on future-growth careers across all sectors
        - Consider both traditional and emerging career paths

        **REQUIRED START & FORMAT ENFORCEMENT (Use Markdown Headings/Bullets):**
        
        **REQUIRED START:** Start with a single, brief, conversational introductory paragraph (2-3 sentences maximum) that uses the user's background (interests/skills) and personality (`{st.session_state.personality_select}`) to set the context for the suggestions.

        You MUST provide exactly 3 career suggestions. Each suggestion MUST follow this structure precisely:

        ### 1. [Job Title] - [Salary: $Xk-$Yk]
        * **Level Fit:** Why this suits {st.session_state.academic_level}
        * **Background Match:** How their skills/education apply
        * **Personality Alignment:** Connection to {st.session_state.personality_select}
        * **Next Step:** One essential action to start
        * 🔗 [Search Job Growth](https://www.google.com/search?q=job+growth+[Job Title])

        End with: "{CONCLUSION_TEXT}"
        """
    # --------------------------------------------------------------------------------

    contents = [
        {"parts": [{"text": prompt_text}]}
    ]
    
    if image_part:
        # Prepend image part to the contents
        contents[0]["parts"] = image_part + contents[0]["parts"]
        # The prompt text is still needed to guide the model on what to do with the image

    data = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "tools": [{"google_search": {} }],
        # Setting maxOutputTokens high to ensure the entire structured response is generated.
        "generationConfig": {
            "maxOutputTokens": 4096
        }
    }

    headers = {"Content-Type": "application/json"}

    # Implement exponential backoff for API calls
    for i in range(5): # Retry up to 5 times
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            # Successful response, proceed to extract text
            result = response.json()
            candidate = result.get("candidates", [{}])[0]
            
            if candidate and candidate.get("content", {}).get("parts"):
                raw_text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                        
                return raw_text
            else:
                # Handle cases where response is structured but empty/blocked
                return f"❌ AI Response Error: The API returned an empty or blocked response. Check safety settings or prompt content."


        except requests.exceptions.HTTPError as errh:
            if response.status_code == 429: # Rate limit exceeded
                delay = 2**i
                time.sleep(delay)
                continue # Retry
            return f"❌ HTTP Error (API Key likely invalid or quota exceeded): {errh}. Status: {response.status_code}"
        except Exception as e:
            return f"❌ An unexpected API or parsing error occurred: {e}"
            
    return "❌ Failed to get a response after multiple retries due to rate limiting."

# ============================================================
# RIASEC MAPPING & UI COLORS
# ============================================================
RIASSEC_DETAILS = {
    "Realistic (Hands-On)": {"color": "#BC5D4A", "desc": "Prefers practical, hands-on tasks, working with tools, machines, or systems."},
    "Investigative (Thinking)": {"color": "#E9CE7F", "desc": "Prefers abstract problem-solving, science, mathematics, and complex analysis."},
    "Artistic (Creating)": {"color": "#43B0B0", "desc": "Prefers unstructured tasks, creativity, self-expression, and design."},
    "Social (Helping)": {"color": "#5D9EC9", "desc": "Prefers helping, teaching, advising, and working with people."},
    "Enterprising (Persuading)": {"color": "#3D4F97", "desc": "Prefers leading, selling, managing, and achieving organizational goals."},
    "Conventional (Organizing)": {"color": "#C389E8", "desc": "Prefers structured tasks, data management, organization, and precision."},
}
BASE_COLOR = "#FFFFFF"

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "user_input_key" not in st.session_state:
    st.session_state.user_input_key = ""
if "refine_input_key" not in st.session_state:
    st.session_state.refine_input_key = ""
if "academic_level" not in st.session_state:
    st.session_state.academic_level = "Entry-Level / Training"
if "personality_select" not in st.session_state:
    st.session_state.personality_select = "None"
if "uploaded_file_data" not in st.session_state:
    st.session_state.uploaded_file_data = None
if "step" not in st.session_state:
    st.session_state.step = 0
if "refine_error_message" not in st.session_state:
    st.session_state.refine_error_message = ""
# New state variable for scroll fix:
if "__last_step_for_scroll" not in st.session_state:
    st.session_state.__last_step_for_scroll = 0

# Control Wizard Steps
def navigate_next(current_step):
    st.session_state.step = current_step + 1
    
def navigate_prev(current_step):
    st.session_state.step = current_step - 1
    
def start_journey():
    st.session_state.step = 1
    st.rerun()

# --- Header & Step Tracker ---
# Only show header for steps 1-4, not for welcome page (step 0)
if st.session_state.step > 0:
    st.header("💡 **Artemis: Career Compass**")


# ============================================================
# GLOBAL SCROLL FIX (MODIFIED FOR RELIABILITY - V2)
# ============================================================
# This script is injected if the step has changed, forcing a reliable scroll to top.
def scroll_to_top():
    # Use a script that specifically targets the main scrollable content container in Streamlit
    st.markdown("""
        <script>
            var scrollableElement = parent.document.querySelector('.main .block-container').parentElement.parentElement;
            if (scrollableElement) {
                scrollableElement.scrollTop = 0;
            } else {
                window.scrollTo(0, 0);
            }
        </script>
    """, unsafe_allow_html=True)

if st.session_state.step != st.session_state.__last_step_for_scroll:
    scroll_to_top()
    st.session_state.__last_step_for_scroll = st.session_state.step
# ============================================================


# DYNAMIC COLOR INJECTION CALCULATION
current_color_data = RIASSEC_DETAILS.get(st.session_state.personality_select, {"color": BASE_COLOR, "desc": ""})
current_color = current_color_data["color"]

# ============================================================
# SIDEBAR LOGIC
# ============================================================
with st.sidebar:
    st.title("About Artemis 🧭")
    st.markdown("""
    Artemis: Career Compass is an **AI-powered career strategist** that provides personalized, future-focused career recommendations.

    It analyzes your:
    * **Academic/Professional Level**
    * **Background and Skills**
    * **RIASEC Personality Trait** (Holland Code)
    * **(Optional) Resume/CV Image** (Multimodal Analysis)
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🧠 Powered By
    This application leverages the **Gemini 2.5 Flash** model with **Google Search Grounding** to ensure the career paths and salary information are relevant and up-to-date.
    """)

    st.markdown("---")
    
    st.markdown("Created by **Amina Atta**")

# ============================================================
# END SIDEBAR LOGIC
# ============================================================


# UPDATED CSS (Fixing HANGING INDENT for list items)
if st.session_state.step > 0:
    dynamic_bg_style = ""
    
    # Use a solid color background for better visibility when a trait is selected
    if st.session_state.personality_select != "None":
        # INCREASED OPACITY from 60 to A0 (62.5%) for pale colors like Investigative yellow
        dynamic_bg_style = f"background-color: {current_color}A0 !important;"    
        
    st.markdown(f"""
    <style>
    /* Dynamic Color Injection */
    .stApp {{
        transition: background-color 0.5s ease;
        {dynamic_bg_style}
    }}

    /* Step title box: light blue background + dark blue left bar */
    .blue-title-box {{
        background-color: #E6F3FF;
        padding: 14px 18px;
        border-left: 6px solid #1A4C88;
        border-radius: 8px;
        font-size: 20px;
        font-weight: 700;
        margin-top: 18px;
        margin-bottom: 12px;
        color: #052639;
    }}
    
    .small-muted {{ color: #6b7a86; font-size: 13px; }}
    
    /* FIX: Increase max-width for better content flow, especially for wide headings */
    .block-container {{
        max-width: 1200px !important;    
        padding-left: 1rem !important;    
        padding-right: 1rem !important;    
    }}
    
    .result-box {{
        background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%);
        border-left: 4px solid #1A4C88;
        padding: 14px;
        border-radius: 8px;
        font-size: 15px;
        line-height: 1.6;
        margin-bottom: 16px;
    }}
    
    /* Enhance Markdown List/Header rendering within the result-box */
    .result-box h3 {{
        margin-top: 1.5rem !important;
        margin-bottom: 0.5rem !important;
        color: #1A4C88;
        display: block;    
    }}
    
    /* Style for the salary tag within H3 */
    .salary-tag {{
        display: inline-block;    
        margin-left: 8px;
        font-weight: 500;
        color: #2E8B57;    
    }}
    
    /* FIX: Hanging Indent for List Items */
    .result-box ul {{
        list-style-position: outside;
        margin-left: 0;
        padding-left: 20px; /* Base padding for the whole list */
    }}
    
    .result-box ul li {{
        list-style-type: disc;
        margin-bottom: 8px;
        /* The magic for hanging indent: */
        padding-left: 15px; /* Pushes the text right */
        text-indent: -15px; /* Pulls the first line back over the bullet */
    }}

    .refine-input {{
        width: 100%;
    }}
    .badge-pill {{
        display:inline-block;
        background:#eef6ff;
        color:#1A4C88;
        padding:6px 10px;
        border-radius:999px;
        font-weight:600;
        margin-right:8px;
    }}
    
    /* Custom style for professional-looking metrics */
    .stMetric {{
        background: #f0f8ff;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #eef6ff;
        box-shadow: 0 2px 5px rgba(26, 76, 136, 0.1);
        margin-bottom: 10px;
    }}
    /* Targeting the label (first div in the second child div) */
    .stMetric > div:first-child > div:nth-child(2) > div:first-child {{
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #1A4C88;
    }}
    /* Targeting the value (second div in the second child div) */
    .stMetric > div:first-child > div:nth-child(2) > div:nth-child(2) {{
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #052639;
    }}
    
    /* Ensure main content area blends with background, using transparent initially to avoid white box */
    .main .block-container {{
        padding-top: 2rem;
        background-color: transparent;
    }}
    
    /* Style native Streamlit elements to match theme */
    div[data-testid="stExpander"] {{
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    
    </style>
    """, unsafe_allow_html=True)

# --- Step Tracker UI (kept) ---
if st.session_state.step > 0:
    cols_nav = st.columns(4)
    if cols_nav[0].button("1", key="nav1", on_click=lambda: st.session_state.update(step=1), disabled=st.session_state.step < 1): pass
    if cols_nav[1].button("2", key="nav2", on_click=lambda: st.session_state.update(step=2), disabled=st.session_state.step < 2): pass
    if cols_nav[2].button("3", key="nav3", on_click=lambda: st.session_state.update(step=3), disabled=st.session_state.step < 3): pass
    if cols_nav[3].button("4", key="nav4", on_click=lambda: st.session_state.update(step=4), disabled=st.session_state.step < 4): pass

# ============================================================
# WIZARD UI LOGIC
# ============================================================

if st.session_state.step == 0:
    # ======= HOMEPAGE: UNCHANGED =======
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0a1929 0%, #1a3658 50%, #2d4a6e 100%);
        color: #ffffff;
    }
    .elegant-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        padding: 60px 40px;
        border-radius: 20px;
        text-align: center;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .main-title {
        font-size: 4.5em;
        font-weight: 300;
        background: linear-gradient(45deg, #64b5f6, #90caf9, #bbdefb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px;
        letter-spacing: 2px;
        font-family: 'Segoe UI', sans-serif;
    }
    .subtitle {
        font-size: 1.6em;
        color: #bbdefb;
        font-weight: 300;
        margin-bottom: 30px;
        letter-spacing: 1px;
        opacity: 0.9;
    }
    .description {
        font-size: 1.2em;
        color: #e3f2fd;
        line-height: 1.7;
        margin-bottom: 40px;
        opacity: 0.8;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }
    .feature-card {
        background: linear-gradient(135deg, rgba(100, 181, 246, 0.1) 0%, rgba(144, 202, 249, 0.05) 100%);
        padding: 30px 20px;
        border-radius: 15px;
        border: 1px solid rgba(100, 181, 246, 0.2);
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }
    .feature-card:hover {
        transform: translateY(-3px);
        border-color: rgba(100, 181, 246, 0.4);
        box-shadow: 0 8px 25px rgba(100, 181, 246, 0.2);
    }
    .feature-icon {
        font-size: 2.8em;
        margin-bottom: 15px;
        display: block;
        opacity: 0.9;
    }
    .feature-text {
        font-size: 1.1em;
        color: #e3f2fd;
        font-weight: 400;
        opacity: 0.9;
    }
    .stat-container {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(5px);
    }
    .stat-number {
        font-size: 2.3em;
        font-weight: 300;
        color: #64b5f6;
        display: block;
        font-family: 'Segoe UI', sans-serif;
    }
    .stat-label {
        font-size: 0.95em;
        color: #bbdefb;
        font-weight: 400;
        opacity: 0.8;
    }
    .light-blue-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%);
        padding: 25px 20px;
        border-radius: 12px;
        border: 1px solid #64b5f6;
        margin: 8px 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(100, 181, 246, 0.2);
    }
    .light-blue-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(100, 181, 246, 0.3);
    }
    .dark-blue-tick {
        color: #1565c0;
        font-weight: bold;
        font-size: 1.2em;
        margin-right: 12px;
    }
    .card-content {
        color: #0d47a1;
        font-size: 1.05em;
        font-weight: 500;
        line-height: 1.5;
        display: flex;
        align-items: center;
    }
    /* Light Sea Green Button */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #20B2AA 0%, #2E8B57 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.2em !important;
        padding: 15px 30px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(32, 178, 170, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(32, 178, 170, 0.4) !important;
        background: linear-gradient(135deg, #2E8B57 0%, #20B2AA 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main Welcome Card - NO HEADER
    st.markdown("""
    <div class="elegant-card">
        <h1 class="main-title">ARTEMIS</h1>
        <h2 class="subtitle">AI-Powered Career Compass</h2>
        <p class="description">
            Discover future-proof careers tailored to your unique personality, skills, and aspirations. 
            Powered by advanced AI and psychological insights for strategic career planning.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🎯</span>
            <div class="feature-text">Personalized Career Matching</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🧠</span>
            <div class="feature-text">RIASEC Personality Analysis</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-icon">🔍</span>
            <div class="feature-text">Real-time Market Insights</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("<br>", unsafe_allow_html=True)
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    
    with stats_col1:
        st.markdown("""
        <div class="stat-container" style="text-align: center;">
            <span class="stat-number">10K+</span>
            <div class="stat-label">Career Paths Analyzed</div>
        </div>
        """, unsafe_allow_html=True)
        
    with stats_col2:
        st.markdown("""
        <div class="stat-container" style="text-align: center;">
            <span class="stat-number">95%</span>
            <div class="stat-label">User Satisfaction</div>
        </div>
        """, unsafe_allow_html=True)
        
    with stats_col3:
        st.markdown("""
        <div class="stat-container" style="text-align: center;">
            <span class="stat-number">5min</span>
            <div class="stat-label">Average Session</div>
        </div>
        """, unsafe_allow_html=True)

    # LIGHT SEA GREEN CTA Button
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Use a container to prevent conflicts
    with st.container():
        # Using a distinct key for the welcome button
        if st.button("🚀 START YOUR CAREER JOURNEY", key="welcome_cta_btn", use_container_width=True, type="primary"):
            start_journey()
    
    # Light Blue Cards Section
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <h3 style="color: #bbdefb; margin-bottom: 30px; font-size: 1.8em; font-weight: 300; letter-spacing: 1px;">WHAT YOU'LL DISCOVER</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Light blue cards with dark blue ticks
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="light-blue-card">
            <div class="card-content">
                <span class="dark-blue-tick">✓</span>3 Personalized Career Paths
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="light-blue-card">
            <div class="card-content">
                <span class="dark-blue-tick">✓</span>Salary Expectations & Ranges
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="light-blue-card">
            <div class="card-content">
                <span class="dark-blue-tick">✓</span>Growth Projections & Trends
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="light-blue-card">
            <div class="card-content">
                <span class="dark-blue-tick">✓</span>RIASEC Personality Alignment
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="light-blue-card">
            <div class="card-content">
                <span class="dark-blue-tick">✓</span>Academic Level Matching
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="light-blue-card">
            <div class="card-content">
                <span class="dark-blue-tick">✓</span>Real-time Market Research
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Final CTA
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <p style="color: #90caf9; font-style: italic; font-size: 1.2em; opacity: 0.9;">Take the first step toward your future career today</p>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------
# Step 1 
# ---------------------------
elif st.session_state.step == 1:
    st.markdown('<div class="blue-title-box">Step 1 — Define Your Foundation (Background)</div>', unsafe_allow_html=True)

    # Academic level dropdown with detailed guidance
    st.markdown("##### 🎓 Select Your Academic/Professional Level")
    with st.expander("💡 **How to choose the right level?**", expanded=False):
        st.markdown("""
        **Choose the option that best describes your current situation:**
        
        - **🏁 Entry-Level / Training**: Just starting out, limited work experience, currently in training programs, or considering career changes with minimal formal experience
        - **📚 Current Student (Undergraduate)**: Currently enrolled in college/university (associate's or bachelor's degree)
        - **🎓 Advanced Degree (Graduate)**: Currently pursuing or completed master's, PhD, or professional degrees
        - **💼 Experienced Professional**: 2+ years of work experience in any field, seeking advancement or specialization
        - **🔄 Seeking Career Pivot**: Significant experience in one field but want to transition to a completely different industry
        """)

    academic_level = st.selectbox(
        "Your Current Level",
        ["Entry-Level / Training", "Current Student (Undergraduate)", "Advanced Degree (Graduate)", "Experienced Professional", "Seeking Career Pivot"],
        key="academic_level_widget",
        index=["Entry-Level / Training", "Current Student (Undergraduate)", "Advanced Degree (Graduate)", "Experienced Professional", "Seeking Career Pivot"].index(st.session_state.academic_level),
        help="This helps us suggest realistic career paths for your current stage"
    )

    # Update session state when academic level changes
    if academic_level != st.session_state.academic_level:
        st.session_state.academic_level = academic_level

    st.markdown("##### 📝 Describe Your Background & Skills")
    user_input = st.text_area(
        "Share your education, skills, experience, and interests:",
        height=150,
        placeholder="Examples:\n• 'High school graduate with strong computer skills interested in technology careers'\n• 'Business degree with 3 years marketing experience, learning Python for data analysis'\n• 'Nursing background wanting to transition into healthcare technology'\n• 'Recent engineering graduate interested in renewable energy fields'",
        value=st.session_state.user_input_key,
        key="user_input_area"
    )

    # Update session state when user types
    if user_input != st.session_state.user_input_key:
        st.session_state.user_input_key = user_input

    # Validation and navigation
    if st.session_state.user_input_key.strip():
        char_count = len(st.session_state.user_input_key.strip())
        if char_count >= 10:
            st.button("Next Step: Add Context", on_click=lambda: navigate_next(1), use_container_width=True, type="primary")
            st.success(f"✓ Ready to proceed! You provided {char_count} characters.")
        else:
            st.warning(f"Please provide a bit more information (currently {char_count}/10 characters)")
            st.button("Next Step: Add Context", on_click=lambda: navigate_next(1), use_container_width=True, disabled=True)
    else:
        st.info("💡 **Tip**: Share your education, any work experience, skills you have, and what interests you career-wise. Even brief information helps!")

    # Preview & Home
    st.markdown("---")
    st.markdown("##### 👤 Your Profile Preview")
    st.markdown('<div class="small-muted">Review of current selection and input.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Academic Level", st.session_state.academic_level)
    with col2:
        st.metric("Background Length", f"{len(st.session_state.user_input_key.strip())} chars" if st.session_state.user_input_key.strip() else "Not provided")

    st.markdown("---")
    if st.button("🏠 Home", use_container_width=True):
        go_home()

# ---------------------------
# Step 2 
# ---------------------------
elif st.session_state.step == 2:
    st.markdown('<div class="blue-title-box">Step 2 — Add Context (Traits & Documents)</div>', unsafe_allow_html=True)

    # Layout columns
    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("##### 🧬 RIASEC Personality Code")
        riasec_options = ["None"] + list(RIASSEC_DETAILS.keys())

        # Get current index safely
        current_personality = st.session_state.personality_select
        current_index = 0 # Default to "None"
        if current_personality in riasec_options:
            current_index = riasec_options.index(current_personality)

        # Use a unique key for the selectbox to maintain state
        selected_personality = st.selectbox(
            "Filter careers by your primary Holland Code",
            riasec_options,
            index=current_index,
            key="personality_selector",
            help="Selecting a code will filter suggestions towards jobs matching that psychological profile."
        )

        # Update session state when selection changes
        if selected_personality != st.session_state.personality_select:
            st.session_state.personality_select = selected_personality
            st.rerun()

        trait_display = st.session_state.personality_select
        # Ensure the selected trait card uses the dynamic color for the border
        if trait_display != "None":
            trait_info = RIASSEC_DETAILS[trait_display]
            st.markdown(f'##### <span style="color: {trait_info["color"]};">Selected Trait:</span> {trait_display}', unsafe_allow_html=True)
            st.markdown(f'<p style="border-left: 3px solid {trait_info["color"]}; padding-left: 10px;">{trait_info["desc"]}</p>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### Optional — Upload Portfolio / Resume (Image)")
        st.session_state.uploaded_file_data = st.file_uploader(
            "Upload Portfolio/Resume Screenshot (Optional)",
            type=["png", "jpg", "jpeg"],
            help="The AI will analyze the document image for keywords and structure."
        )

    with col_b:
        st.markdown("##### 📚 Holland Code Reference")
        st.image("https://www.publichealthdegrees.org/wp-content/uploads/sites/53/2022/08/Personality-Types-Holland-Code-System.png",
                 caption="The Holland Code (RIASEC) System Hexagon", use_container_width=True)
        

        with st.expander("Expand for Trait Key", expanded=False):
            for name, details in RIASSEC_DETAILS.items():
                st.markdown(f'<span style="color:{details["color"]}; font-weight: bold;">{name}</span>: {details["desc"]}</span>', unsafe_allow_html=True)

    # NAV BUTTONS
    st.markdown("---")
    cols_nav_bottom = st.columns(3)
    if cols_nav_bottom[0].button("🏠 Home", use_container_width=True):
        go_home()
    if cols_nav_bottom[1].button("← Back to Foundation", on_click=lambda: navigate_prev(2), use_container_width=True): pass
    if cols_nav_bottom[2].button("Next Step: Generate", on_click=lambda: navigate_next(2), use_container_width=True, type="primary"): pass

# ---------------------------
# Step 3 
# ---------------------------
elif st.session_state.step == 3:
    st.markdown('<div class="blue-title-box">Step 3 — Review & Generate Analysis</div>', unsafe_allow_html=True)

    # Profile summary
    st.markdown("##### 🔍 Profile Summary")
    
    col_level, col_trait = st.columns(2)
    with col_level:
        st.metric("Academic Level", st.session_state.academic_level)
    with col_trait:
        st.metric("RIASEC Filter", st.session_state.personality_select)
        
    st.markdown('<div class="small-muted">Review your background and filters before generating the AI analysis.</div>', unsafe_allow_html=True)

    # Background text and generation controls
    st.markdown("##### Background Text")
    st.info(st.session_state.user_input_key)

    generate_button = st.button("✨ START AI ANALYSIS", key="generate_btn", use_container_width=True, type="primary")

    if generate_button:
        enhanced_input = f"Academic Level: {st.session_state.academic_level}\nUser Background: {st.session_state.user_input_key}"
        if st.session_state.personality_select != "None":
            enhanced_input += f"\n\nCRITICAL FILTER: The careers suggested MUST align with the {st.session_state.personality_select} RIASEC Code and be appropriate for {st.session_state.academic_level}."

        uploaded_file = st.session_state.uploaded_file_data
        image_part = get_image_part(uploaded_file)

        # Progress bar replaced with st.spinner
        with st.spinner("🤖 Thinking... Analyzing data and generating pathways (using Google Search for grounding)..."):
            # The API call is now the only thing within the spinner context
            result = get_career_guidance(enhanced_input, image_part)    

        # Save result and show it in a styled result box
        st.session_state.history.insert(0, (enhanced_input, result, uploaded_file.name if uploaded_file else None))
        st.success("✅ AI Analysis Complete — view results in the next screen.")
        # Move to analysis
        st.session_state.step = 4
        st.rerun()

    # NAV
    st.markdown("---")
    cols_nav_bottom = st.columns(3)
    if cols_nav_bottom[0].button("🏠 Home", use_container_width=True):
        go_home()
    if cols_nav_bottom[1].button("← Back to Filters", on_click=lambda: navigate_prev(3), use_container_width=True): pass
    if cols_nav_bottom[2].button("Skip to Analysis Page", on_click=lambda: navigate_next(3), use_container_width=True, disabled=not st.session_state.history, type="secondary"): pass

# ---------------------------
# Step 4 
# ---------------------------
elif st.session_state.step == 4:
    st.markdown('<div class="blue-title-box">Step 4 — Final Analysis & History</div>', unsafe_allow_html=True)

    tab_analysis, tab_history = st.tabs(["✅ Latest Analysis", "🕰️ Analysis History"])

    with tab_analysis:
        # Display badges
        st.markdown("#### 4. Final Analysis Results")
        col_badges = st.columns(3)
        col_badges[0].markdown(f"<span class='badge-pill'>Level: {st.session_state.academic_level}</span>", unsafe_allow_html=True)
        col_badges[1].markdown(f"<span class='badge-pill'>Trait: {st.session_state.personality_select}</span>", unsafe_allow_html=True)
        col_badges[2].markdown(f"<span class='badge-pill'>Multimodal: {'Yes' if st.session_state.uploaded_file_data else 'No'}</span>", unsafe_allow_html=True)

        st.markdown('---')

        if st.session_state.history:
            latest_query, latest_result, file_name = st.session_state.history[0]
            
            # Robust Post-processing to ensure the conclusion text is on its own line
            latest_result = latest_result.replace(CONCLUSION_TEXT, f"\n\n{CONCLUSION_TEXT}")

            # Check if the latest result was a refinement to adjust the main heading
            is_refined = latest_query.startswith('[REFINED:')    

            if is_refined:
                st.markdown("### 🔄 Refined Career Path")
            else:
                st.markdown("### 💼 Your Personalized Career Analysis (3 Options)")

            if file_name:
                st.markdown(f"<div class='small-muted'>Analyzed with file: {file_name}</div>", unsafe_allow_html=True)
            
            # Display result using the fixed function which converts Markdown to HTML
            display_markdown_in_styled_box(latest_result)
        else:
            st.info("No analysis generated yet. Start a new analysis in Step 1.")

        # Refine section
        st.markdown("---")
        st.subheader("🔄 Refine Latest Suggestion")
        if st.session_state.history:
            col_refine_input, col_refine_button = st.columns([4,1])
            refine_input = col_refine_input.text_input(
                "Enter feedback to get ONE new, refined career path:",
                placeholder="E.g., I don't like coding, suggest non-technical roles only.",
                key="refine_input_key"
            )
            if col_refine_button.button("Refine", key="refine_btn", use_container_width=True):
                if refine_input.strip():
                    st.session_state.refine_error_message = ""
                    previous_query, previous_result, previous_file = st.session_state.history[0]
                    refine_prompt = f"""
                    REFINEMENT REQUEST: {refine_input}.
                    PREVIOUS ANALYSIS CONTEXT: (Summary of user's background: {previous_query[:100]}... )
                    """
                    with st.spinner("🔄 Finding better matches based on your feedback..."):
                        image_part = get_image_part(st.session_state.uploaded_file_data) # Re-analyze the file if present
                        result = get_career_guidance(refine_prompt, image_part=image_part, refine_mode=True)
                    if result and not result.startswith("❌"):
                        st.session_state.history.insert(0, (f"[REFINED: {refine_input}]", result, None))
                        st.rerun()
                    else:
                        st.error(f"Refinement failed: {result}")
                else:
                    st.warning("Please enter feedback for refinement")
        else:
            st.info("Generate an analysis first to enable refinement.")
        if st.session_state.get("refine_error_message"):
            st.error(st.session_state.refine_error_message)

    # History tab
    with tab_history:
        st.markdown("### 🕰️ Analysis History")
        if len(st.session_state.history) > 0:
            # Calculation to number oldest as #1 (session_num=1) while keeping newest at the top (i=0)
            total_analyses = len(st.session_state.history)    
            for i, (query, analysis, filename) in enumerate(st.session_state.history):
                session_num = total_analyses - i # Calculates the session number (e.g., if total=3, i=0 => #3, i=2 => #1)
                
                # Robust Post-processing to ensure the conclusion text is on its own line
                analysis_display = analysis.replace(CONCLUSION_TEXT, f"\n\n{CONCLUSION_TEXT}")

                with st.expander(f"Analysis #{session_num} - {query[:50]}...", expanded=(i==0)):
                    is_refined = query.startswith('[REFINED:')
                    if is_refined:
                        feedback_text = query.replace('[REFINED: ', '').replace(']', '')
                        st.markdown(f"**🔄 Refined based on:** *{feedback_text}*")
                    if filename:
                        st.caption(f"📎 Analyzed with file: {filename}")
                    
                    # Display result using the fixed function which converts Markdown to HTML
                    display_markdown_in_styled_box(analysis_display)
                    
                    if i < len(st.session_state.history) - 1:
                        st.markdown("---")
        else:
            st.info("No previous analyses available. Generate a new one first!")

    # Navigation buttons
    st.markdown("---")
    cols_final_nav = st.columns(2)
    if cols_final_nav[0].button("🏠 Home", use_container_width=True):
        go_home()
    if cols_final_nav[1].button("🔄 Start New Analysis", use_container_width=True, key="restart_analysis"):
        st.session_state.personality_select = "None"
        st.session_state.user_input_key = ""
        st.session_state.academic_level = "Entry-Level / Training"
        st.session_state.uploaded_file_data = None
        st.session_state.step = 1
        st.rerun()
