import google.generativeai as genai
import streamlit as st
import PyPDF2
import re

# Configure Google Gemini API
genai.configure(api_key="AIzaSyBEf88rG3K8zIMshozKtiWfETcy8tz0Auw")

# Function to generate quiz questions using Google Gemini API
def generate_quiz_questions(text, num_questions):
    prompt = f"""
    Generate {num_questions} multiple-choice questions based on the following content:
    {text}
    
    Each question must follow this format:

    Q: <question text>
    A) <option 1>
    B) <option 2>
    C) <option 3>
    D) <option 4>
    Correct Answer: <letter of correct option>

    Ensure the correct answer is among the four options.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text if response else None

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

# Function to display quiz
def display_quiz(quiz_text):
    questions = re.findall(r'Q:.*?Correct Answer:.*?(?=Q:|$)', quiz_text, re.DOTALL)
    for i, question in enumerate(questions, start=1):
        q_text = re.search(r'Q:(.*?)A\)', question, re.DOTALL).group(1).strip()
        options = re.findall(r'([A-D]\) .*?)(?=\n|Correct Answer:)', question)
        correct_answer = re.search(r'Correct Answer: (.*)', question).group(1).strip()

        st.markdown(f"### **Question {i}: {q_text}**")
        for option in options:
            st.markdown(f"- {option.strip()}")
        st.markdown(f"**✅ Correct Answer:** {correct_answer}")

# Streamlit UI
st.set_page_config(page_title="SmartQuiz Generator", page_icon="🎓", layout="wide")
st.title("📘 SmartQuiz Generator")
st.markdown("Generate MCQs from PDFs or just by entering a topic!")

# User chooses input method
input_method = st.radio("Select input method:", ("Upload PDF", "Enter a Topic"))

if input_method == "Upload PDF":
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    num_questions = st.slider("Number of questions:", 1, 20, 5)

    if uploaded_file and st.button("Generate Quiz"):
        with st.spinner("Extracting text and generating questions..."):
            text_content = extract_text_from_pdf(uploaded_file)
            quiz_text = generate_quiz_questions(text_content, num_questions)
            if quiz_text:
                display_quiz(quiz_text)
            else:
                st.error("Failed to generate quiz. Try again!")

elif input_method == "Enter a Topic":
    topic = st.text_input("Enter a topic:", placeholder="e.g., Python Programming, Machine Learning, etc.")
    num_questions = st.slider("Number of questions:", 1, 20, 5)

    if topic and st.button("Generate Quiz"):
        with st.spinner("Generating quiz..."):
            quiz_text = generate_quiz_questions(topic, num_questions)
            if quiz_text:
                display_quiz(quiz_text)
            else:
                st.error("Failed to generate quiz. Try again!")

st.markdown("### 🔍 Powered by Google Gemini AI 🚀")
