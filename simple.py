import streamlit as st
import PyPDF2
import re
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import os
from typing import List


# Set your Groq API key
os.environ["GROQ_API_KEY"] = "gsk_"

# Function to extract text from PDF
def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to extract information using regex
def extract_info(text):
    email = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phone = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
    linkedin = re.findall(r'linkedin.com/in/[\w-]+', text)
    
    return {
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "linkedin": linkedin[0] if linkedin else ""
    }

# Pydantic model for structured output
class ResumeAnalysis(BaseModel):
    name: str = Field(description="The full name of the candidate")
    skills: List[str] = Field(description="A list of skills extracted from the resume")
    is_match: bool = Field(description="Whether the candidate is a good match for the job (True/False)")

# Create the parser
parser = PydanticOutputParser(pydantic_object=ResumeAnalysis)

# LangChain setup with ChatGroq
llm = ChatGroq(model_name="mixtral-8x7b-32768", temperature=0)

# Combined template
combined_template = """
Analyze the following resume text and job description, then provide the requested information in the specified JSON format.

Resume text:
{text}

Job Description:
{job_description}

Extract and provide the following information:
1. The full name of the candidate
2. A list of skills from the resume
3. Whether the candidate is a good match for the job (True/False)

{format_instructions}
"""

prompt = PromptTemplate(
    template=combined_template,
    input_variables=["text", "job_description"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

chain = LLMChain(llm=llm, prompt=prompt)

# Streamlit app
st.title("Resume Parser and Job Matcher")

uploaded_file = st.file_uploader("Choose a resume PDF", type="pdf")
job_description = st.text_area("Enter the job description")

if uploaded_file is not None and job_description:
    text = extract_text_from_pdf(uploaded_file)
    
    # Extract email, phone, and LinkedIn using regex
    info = extract_info(text)
    
    # Run the LLM chain
    result = chain.run(text=text, job_description=job_description)
    
    # Parse the result
    parsed_result = parser.parse(result)
    
    st.subheader("Extracted Information")
    st.write(f"Name: {parsed_result.name}")
    st.write(f"Email: {info['email']}")
    st.write(f"Phone: {info['phone']}")
    st.write(f"LinkedIn: {info['linkedin']}")
    st.write(f"Skills: {', '.join(parsed_result.skills)}")
    
    st.subheader("Job Match Analysis")
    st.write(f"Is a good match: {'Yes' if parsed_result.is_match else 'No'}")
