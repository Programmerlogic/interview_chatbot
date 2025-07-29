import random
from datetime import datetime
import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="TalentScout - AI Hiring Assistant",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS (keeping your original styling)
st.markdown("""
<style>
    /* Main app styling */
    .main {
        padding-top: 1rem;
    }
    
    /* Chat container styling */
    .stChatMessage {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
        display: flex;
        width: 100%;
    }
    
    /* User message styling */
    .stChatMessage[data-testid="user-message"] {
        background-color: #007bff;
        color: white;
        border-left: none;
        border-right: 4px solid #0056b3;
        margin-left: auto;
        margin-right: 0;
        max-width: 70%;
        flex-direction: row-reverse;
        text-align: right;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        margin-left: 0;
        margin-right: auto;
        max-width: 70%;
        text-align: left;
    }
    
    /* Chat input styling */
    .stChatInput {
        position: sticky;
        bottom: 0;
        background: white;
        border-top: 1px solid #e0e0e0;
        padding: 1rem 0;
        z-index: 100;
    }
    
    .stChatInput > div {
        max-width: 100%;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #007bff;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Sidebar header */
    .css-1lcbmhc h1 {
        color: #007bff;
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Summary box styling */
    .css-1v0mbdj {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Avatar styling */
    .stChatMessage .css-1v0mbdj {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    
    /* User avatar - positioned on right */
    .stChatMessage[data-testid="user-message"] .css-1v0mbdj {
        margin-left: 1rem;
        margin-right: 0;
        background-color: #0056b3;
        color: white;
    }
    
    /* Assistant avatar - positioned on left */
    .stChatMessage[data-testid="assistant-message"] .css-1v0mbdj {
        margin-right: 1rem;
        margin-left: 0;
        background-color: #4caf50;
        color: white;
    }
    
    /* Spinner styling */
    .stSpinner {
        color: #007bff;
    }
    
    /* Title styling */
    h1 {
        color: #007bff;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 600;
    }
    
    /* Privacy notice styling */
    .css-1v0mbdj blockquote {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    /* Question styling */
    .stChatMessage strong {
        color: #007bff;
        font-size: 1.1rem;
    }
    
    /* User message question styling */
    .stChatMessage[data-testid="user-message"] strong {
        color: white;
    }
    
    /* Evaluation styling */
    .stChatMessage h3 {
        color: #28a745;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


PRIVACY_NOTICE = (
    "Your information will be used solely for recruitment purposes. "
    "We comply with GDPR and data-protection regulations. "
    "You can request data deletion at any time."
    "Export Your Data as We will not store your Data after this session is over due to privacy "
)

FALLBACK_RESPONSES = [
    "I didn't quite understand that 🤔  Could you please re-phrase?",
    "Let me try a different approach – can you give more detail?",
    "Hmm, I'm not sure I follow. Could you clarify?",
    "That's interesting! Can you elaborate a bit more?",
    "I want to be sure I understand – could you re-state that?",
]


PHASES = [
    "welcome",
    "consent",
    "personal_info",
    "professional_info",
    "tech_stack",
    "technical_assessment",
    "summary",
    "completion",
]

PHASE_FRIENDLY = {
    "welcome": "Getting Started",
    "consent": "Privacy Consent",
    "personal_info": "Personal Information",
    "professional_info": "Professional Background",
    "tech_stack": "Tech-Stack Review",
    "technical_assessment": "Technical Assessment",
    "summary": "Summary Review",
    "completion": "Complete",
}

# Helper functions
def add_message(role: str, content: str, avatar: str | None = None):
    """Store message in session state and render it."""
    # Store message in session state
    st.session_state.messages.append({
        "role": role, 
        "content": content, 
        "avatar": avatar,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Render the message
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

def update_progress_bar():
    """Update the progress bar based on current phase and assessment progress."""
    current_phase = st.session_state.phase
    phase_idx = PHASES.index(current_phase)
    total_phases = len(PHASES)
    
    if current_phase == "technical_assessment":
        # Calculate fine-grained progress within technical assessment
        answered_questions = len(st.session_state.get("technical_responses", []))
        total_questions = st.session_state.get("total_questions", 3)
        
        # Base progress from completed phases
        base_progress = phase_idx / total_phases
        # Progress within current phase
        phase_progress = (answered_questions / total_questions) / total_phases
        
        total_progress = int((base_progress + phase_progress) * 100)
        label = f"{PHASE_FRIENDLY[current_phase]} ({answered_questions}/{total_questions})"
    else:
        # Standard phase progress
        total_progress = int(((phase_idx + 1) / total_phases) * 100)
        label = PHASE_FRIENDLY[current_phase]
    
    st.sidebar.progress(total_progress, text=f"Phase: {label}")

def find_matching_tech(label: str) -> str | None:
    norm = label.lower().strip()
    for key in TECH_STACK_DATA:
        if key.lower() == norm:
            return key
    for key in TECH_STACK_DATA:
        if norm in key.lower() or key.lower() in norm:
            return key
    return None

def generate_ai_question(tech_stack: list, experience, position: str, question_num: int, total_questions: int):
    """Generate a technical question using Groq AI based on candidate's tech stack and position."""
    tech_stack_str = ", ".join(tech_stack)
    question_prompt = (
        f"Generate 1 technical interview question for a {position} role. "
        f"Focus on the following technologies: {tech_stack_str}. "
        f"Make it practical and relevant to real-world development scenarios. "
        f"Return only the question without additional formatting."
        f"Generate question for short one line answers."
        f"Level: {experience}/20"
    )
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": question_prompt}],
            temperature=0.8,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating question: {str(e)}")
        return f"Describe your experience working with {tech_stack[0] if tech_stack else 'your primary technology'} in a production environment."

def evaluate_answer(question: str, answer: str, tech_context: str):
    """Evaluate candidate's answer using Groq AI."""
    eval_prompt = (
        f"You are an expert technical interviewer evaluating a candidate's response. "
        f"Your role is strictly limited to technical interview evaluation.\n\n"
        f"IMPORTANT CONSTRAINTS:\n"
        f"Technology context: {tech_context}\n"
        f"Question: '{question}'\n"
        f"Candidate's answer: '{answer}'\n\n"
        f"Provide a brief evaluation covering:\n"
        f"1. Technical accuracy (0-10)\n"
        f"2. Completeness (0-10)\n"
        f"3. Clarity of explanation (0-10)\n"
        f"4. Correctness of explanation (0-10)\n"
        f"5. Brief constructive feedback\n"
        f"Keep the response concise and professional."
        f"Remember: You are conducting a technical interview. Stay focused on evaluating technical competency."
    )
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": eval_prompt}],
            temperature=0.3,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error evaluating answer: {str(e)}")
        return "Unable to evaluate answer at this time. Thank you for your response!"

def update_summary():
    cd = st.session_state.candidate
    lines = []
    if cd.get("name"):
        lines.append(f"**Name**: {cd['name']}")
    if cd.get("email"):
        lines.append(f"**Email**: {cd['email']}")
    if cd.get("phone"):
        lines.append(f"**Phone**: {cd['phone']}")
    if cd.get("location"):
        lines.append(f"**Location**: {cd['location']}")
    if cd.get("experience"):
        lines.append(f"**Experience**: {cd['experience']}")
    if cd.get("position"):
        lines.append(f"**Position**: {cd['position']}")
    if cd.get("tech_stack"):
        stack = ", ".join(cd["tech_stack"])
        lines.append(f"**Tech-Stack**: {stack}")
    summary.markdown("\n\n".join(lines) if lines else "_No information yet…_")

def ask_next_question():
    idx = st.session_state.q_idx
    total_q = st.session_state.total_questions
    
    if idx >= total_q:
        finish_technical()
        return
    
    cd = st.session_state.candidate
    tech_stack = cd.get("tech_stack", [])
    experience = cd.get("experience")
    position = cd.get("position", "Software Developer")
    
    with st.spinner("🤖 Generating your next question..."):
        question = generate_ai_question(tech_stack, experience, position, idx + 1, total_q)
        st.session_state.current_question = question
        
        add_message("assistant", f"**Question {idx+1}/{total_q}**\n\n{question}")
        st.session_state.q_idx += 1

def finish_technical():
    add_message("assistant", "🎉 Excellent work – you've completed the technical assessment.")
    st.session_state.phase = "summary"
    build_summary()

def build_summary():
    cd = st.session_state.candidate
    add_message(
        "assistant",
        "### Application Summary\n"
        f"**Name:** {cd.get('name','_Not provided_')}  \n"
        f"**Email:** {cd.get('email','_Not provided_')}  \n"
        f"**Experience:** {cd.get('experience','_Not provided_')}  \n"
        f"**Position:** {cd.get('position','_Not provided_')}  \n"
        f"**Location:** {cd.get('location','_Not provided_')}  \n"
        f"**Tech-Stack:** {', '.join(cd.get('tech_stack',[])) or '_Not provided_'}",
    )
    add_message(
        "assistant",
        "Thank you for completing the screening! Our recruitment team will review "
        "your responses within **2-3 business days** and contact you if there is a match.",
    )
    st.session_state.phase = "completion"

# Session-state initialization
if "phase" not in st.session_state:
    st.session_state.phase = "welcome"
    st.session_state.messages = []  # Store all chat messages
    st.session_state.candidate = {}
    st.session_state.tech_questions = []
    st.session_state.q_idx = 0
    st.session_state.consent_given = False
    st.session_state.personal_step = "name"
    st.session_state.current_question = ""
    st.session_state.total_questions = 3
    st.session_state.technical_responses = []

# Re-render all stored messages to maintain chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])

# Sidebar summary
st.sidebar.header("📋 Candidate Summary")
summary = st.sidebar.empty()

# 
update_progress_bar()

# Display welcome  on first load
if st.session_state.phase == "welcome":
    add_message("assistant", "Hello! I'm **TalentScout**, your AI hiring assistant. 👋")
    add_message(
        "assistant",
        "This screening takes roughly *5–10 minutes* and uses **AI-powered questions** "
        "tailored to your skills and background.",
    )
    add_message(
        "assistant",
        f"Before we begin, **do you consent** to our privacy policy?\n\n> {PRIVACY_NOTICE}\n\n"
        "Please respond with **yes** or **no**.",
    )
    st.session_state.phase = "consent"

# Chat input / processing loop
user_input = st.chat_input("Type your response and hit ⮐")

if user_input:
    add_message("user", user_input, avatar="👤")
    
    phase = st.session_state.phase
    
    # Consent phase
    if phase == "consent":
        if user_input.lower().startswith(("y", "yes")):
            st.session_state.consent_given = True
            add_message(
                "assistant",
                "Excellent! Let's start with some basic information. What's your **full name**?",
            )
            st.session_state.phase = "personal_info"
            st.session_state.personal_step = "name"
            
        elif user_input.lower().startswith(("n", "no")):
            add_message(
                "assistant",
                "I understand. Without consent we cannot proceed. Feel free to return when ready. 👋",
            )
            st.session_state.phase = "completion"
           
        else:
            add_message("assistant", "Please reply **yes** or **no** regarding consent.")
    
    # Personal information
    elif phase == "personal_info":
        step = st.session_state.personal_step
        cd = st.session_state.candidate
        
        if step == "name":
            cd["name"] = user_input.strip()
            add_message("assistant", "Great! What's your **email address**?")
            st.session_state.personal_step = "email"
        
        elif step == "email":
            if "@" in user_input and "." in user_input:
                cd["email"] = user_input.strip()
                add_message("assistant", "Thanks! What's your **phone number**?")
                st.session_state.personal_step = "phone"
            else:
                add_message("assistant", "That doesn't look like a valid email. Please try again.")
        
        elif step == "phone":
            cd["phone"] = user_input.strip()
            add_message("assistant", "And your **current location** (city, country)?")
            st.session_state.personal_step = "location"
        
        elif step == "location":
            cd["location"] = user_input.strip()
            add_message(
                "assistant",
                "Awesome. How many **years of experience** do you have in technology?",
            )
            st.session_state.phase = "professional_info"
            st.session_state.personal_step = "experience"
            
        update_summary()
    
    # Professional info
    elif phase == "professional_info":
        step = st.session_state.personal_step
        cd = st.session_state.candidate
        
        if step == "experience":
            cd["experience"] = user_input.strip()
            add_message(
                "assistant",
                "What **position(s)** are you interested in or currently seeking?",
            )
            st.session_state.personal_step = "position"
        
        elif step == "position":
            cd["position"] = user_input.strip()
            add_message(
                "assistant",
                "Great choice! Please list your **tech stack** "
                "(languages / frameworks / tools) separated by commas.",
            )
            st.session_state.phase = "tech_stack"
           
        update_summary()
    
    # Tech stack phase
    elif phase == "tech_stack":
        techs = [t.strip() for t in user_input.split(",") if t.strip()]
        if techs:
            cd = st.session_state.candidate
            cd["tech_stack"] = techs
            update_summary()
            
            add_message("assistant", f"Impressive stack: {', '.join(techs)}")
            add_message(
                "assistant",
                "Perfect! Now I'll generate **AI-powered technical questions** "
                f"tailored to your skills. Ready for {st.session_state.total_questions} questions?",
            )
            
            st.session_state.q_idx = 0
            st.session_state.technical_responses = []  # Reset responses
            st.session_state.phase = "technical_assessment"
            
            ask_next_question()
        else:
            add_message("assistant", "Please provide at least one technology.")
    
    # Technical Q&A
    elif phase == "technical_assessment":
        # Store the user's answer
        if not hasattr(st.session_state, 'technical_responses'):
            st.session_state.technical_responses = []
        
        # Get the current question info
        current_q_num = st.session_state.q_idx - 1
        current_question = st.session_state.current_question
        tech_context = ", ".join(st.session_state.candidate.get("tech_stack", []))
        
        # Store response
        st.session_state.technical_responses.append({
            "question_number": current_q_num + 1,
            "question": current_question,
            "answer": user_input,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Evaluate the answer using AI
        with st.spinner("🤖 Evaluating your answer..."):
            evaluation = evaluate_answer(current_question, user_input, tech_context)
            add_message("assistant", f"**📊 Evaluation:**\n\n{evaluation}")
        
        # Move to next question or finish
        if st.session_state.q_idx < st.session_state.total_questions:
            ask_next_question()
        else:
            finish_technical()
    
    # Fallback for completion
    else:
        if st.session_state.phase == "completion":
            add_message(
                "assistant", "The session is complete. Thank you for using TalentScout! 👋"
            )
        else:
            add_message("assistant", random.choice(FALLBACK_RESPONSES))
    
   
    st.rerun()

# Export / reset widgets
st.sidebar.markdown("---")

# Export functionality
if st.sidebar.button("⬇️ Export Session Data"):
    try:
        # Create text format export
        export_lines = []
        export_lines.append("=" * 60)
        export_lines.append("TALENTSCOUT SESSION EXPORT")
        export_lines.append("=" * 60)
        export_lines.append(f"Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        export_lines.append(f"Session Phase: {st.session_state.get('phase', 'unknown').title()}")
        export_lines.append("")
        
        # Candidate Information
        cd = st.session_state.get('candidate', {})
        if cd:
            export_lines.append("CANDIDATE INFORMATION:")
            export_lines.append("-" * 25)
            for key, value in cd.items():
                if isinstance(value, list):
                    value = ", ".join(value)
                export_lines.append(f"{key.replace('_', ' ').title()}: {value}")
            export_lines.append("")
        
        # Chat Messages
        export_lines.append("CONVERSATION HISTORY:")
        export_lines.append("-" * 25)
        
        for msg in st.session_state.get('messages', []):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            if role == 'assistant':
                # Assistant messages on the left
                export_lines.append(f"🤖 AI Assistant:")
                export_lines.append(f"{content}")
                export_lines.append("")
            elif role == 'user':
                
                lines = content.split('\n')
                max_width = 60
                export_lines.append(f"{'👤 User:':>60}")
                for line in lines:
                    if len(line) <= max_width:
                        export_lines.append(f"{line:>{max_width}}")
                    else:
                        
                        words = line.split(' ')
                        current_line = ""
                        for word in words:
                            if len(current_line + word + " ") <= max_width:
                                current_line += word + " "
                            else:
                                if current_line:
                                    export_lines.append(f"{current_line.strip():>{max_width}}")
                                current_line = word + " "
                        if current_line:
                            export_lines.append(f"{current_line.strip():>{max_width}}")
                export_lines.append("")
        
        # Technical Responses Summary
        tech_responses = st.session_state.get('technical_responses', [])
        if tech_responses:
            export_lines.append("TECHNICAL ASSESSMENT SUMMARY:")
            export_lines.append("-" * 35)
            for i, response in enumerate(tech_responses, 1):
                export_lines.append(f"Question {i}:")
                export_lines.append(f"Q: {response.get('question', 'N/A')}")
                export_lines.append(f"A: {response.get('answer', 'N/A')}")
                export_lines.append("")
        
        # Session Metadata
        export_lines.append("SESSION METADATA:")
        export_lines.append("-" * 20)
        export_lines.append(f"Total Questions: {st.session_state.get('total_questions', 3)}")
        export_lines.append(f"Questions Answered: {len(st.session_state.get('technical_responses', []))}")
        export_lines.append(f"Completion Status: {st.session_state.get('phase', 'unknown').title()}")
        export_lines.append("")
        export_lines.append("=" * 60)
        export_lines.append("END OF SESSION EXPORT")
        export_lines.append("=" * 60)

        text_content = "\n".join(export_lines)
        
        st.sidebar.download_button(
            label="📄 Download Session Data (TXT)",
            data=text_content,
            file_name=f"talentscout_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="download_session"
        )
        
    except Exception as e:
        st.sidebar.error(f"Export error: {str(e)}")

# Reset functionality
if st.sidebar.button("🔄 New Session", key="reset_session"):
    try:
        # Clear all session state variables
        keys_to_delete = list(st.session_state.keys())
        for key in keys_to_delete:
            del st.session_state[key]
        
        # Force a clean rerun
        st.rerun()
        
    except Exception as e:
        st.sidebar.error(f"Reset error: {str(e)}")

# Add configuration in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Privacy")
st.sidebar.markdown(PRIVACY_NOTICE)
