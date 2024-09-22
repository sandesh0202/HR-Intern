import streamlit as st
import PyPDF2
import re
import os
import csv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from email.mime.text import MIMEText
import base64

# Set your Groq API key
os.environ["GROQ_API_KEY"] = "gsk_"

# Function to extract text and links from PDF
def extract_text_and_links_from_pdf(pdf_path):
    text = ""
    links = []
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        pages = len(reader.pages)
        for page_num in range(pages):
            page = reader.pages[page_num]
            text += page.extract_text()
            
            if '/Annots' in page:
                for annot in page['/Annots']:
                    obj = annot.get_object()
                    if '/A' in obj and '/URI' in obj['/A']:
                        links.append(obj['/A']['/URI'])
    
    return text, links

# Function to extract LinkedIn profiles
def extract_linkedin_profiles(text, links):
    linkedin_patterns = [
        r'https?://(?:www\.)?linkedin\.com/in/[\w-]+/?',
        r'https?://(?:www\.)?linkedin\.com/pub/[\w-]+(?:/[\w-]+){0,3}/?',
        r'https?://(?:www\.)?linkedin\.com/profile/view\?id=\d+',
        r'linkedin\.com/in/[\w-]+',
        r'linkedin\.com/pub/[\w-]+(?:/[\w-]+){0,3}'
    ]
    linkedin_regex = re.compile('|'.join(linkedin_patterns), re.IGNORECASE)
    profiles_from_text = linkedin_regex.findall(text)
    profiles_from_links = [link for link in links if linkedin_regex.search(link)]
    return list(set(profiles_from_text + profiles_from_links))

# Function to extract information using regex
def extract_info(text, links):
    email = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phone = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
    linkedin = extract_linkedin_profiles(text, links)
    
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

# Function to process all PDFs in a folder
def process_folder(folder_path, job_description):
    results = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            text, links = extract_text_and_links_from_pdf(file_path)
            info = extract_info(text, links)
            result = chain.run(text=text, job_description=job_description)
            parsed_result = parser.parse(result)
            results.append({
                "name": parsed_result.name,
                "email": info['email'],
                "phone": info['phone'],
                "linkedin": info['linkedin'],
                "skills": ', '.join(parsed_result.skills),
                "is_match": parsed_result.is_match
            })
    return results

# Function to save results to CSV
def save_to_csv(results, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'email', 'phone', 'linkedin', 'skills', 'is_match']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


# OAuth 2.0 setup
CLIENT_CONFIG = {
    "web": {
        "client_id": "",
        "client_secret": "",
        "auth_uri": "",
        "token_uri": "",
    }
}

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Function to initiate OAuth 2.0 flow
def start_oauth_flow():
    flow = Flow.from_client_config(CLIENT_CONFIG, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    st.session_state['auth_url'] = auth_url
    st.session_state['flow'] = flow

# Function to complete OAuth 2.0 flow
def complete_oauth_flow(auth_code):
    flow = st.session_state['flow']
    flow.fetch_token(code=auth_code)
    st.session_state['credentials'] = flow.credentials
    del st.session_state['flow']
    del st.session_state['auth_url']

# Function to send email using Gmail API
def send_email(to_email, subject, body):
    try:
        credentials = st.session_state.get('credentials')
        if not credentials:
            st.error("Not authorized. Please complete the authorization process.")
            return False

        service = build('gmail', 'v1', credentials=credentials)

        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False
    


# Streamlit app
st.title("Multi-Resume Parser and Job Matcher")

folder_path = "C:\LangchainProjects\HRrrr\Files"
job_description = st.text_area("Enter the job description:")
output_file = st.text_input("Enter the name of the output CSV file:", "results.csv")

if st.button("Process Resumes"):
    if folder_path and job_description:
        results = process_folder(folder_path, job_description)
        save_to_csv(results, output_file)
        st.success(f"Processing complete. Results saved to {output_file}")
        st.session_state['results'] = results
    else:
        st.error("Please provide both folder path and job description.")

if 'results' in st.session_state:
    email_body = st.text_area("Enter the email body:")
    
    # Add authorization section
st.header("Email Authorization")
if 'credentials' not in st.session_state:
    if st.button("Start Authorization Process"):
        start_oauth_flow()
    
    if 'auth_url' in st.session_state:
        st.write("Please visit this URL to authorize the application:")
        st.write(st.session_state['auth_url'])
        auth_code = st.text_input("Enter the authorization code:")
        if auth_code:
            complete_oauth_flow(auth_code)
            st.success("Authorization successful!")
else:
    st.success("Application is authorized to send emails.")

    # Update the email sending buttons
    if st.button("Send Email to All"):
        if 'credentials' not in st.session_state:
            st.warning("Please authorize the application first.")
        else:
            success_count = 0
            for result in st.session_state['results']:
                if send_email(result['email'], "Job Application Update", email_body):
                    success_count += 1
            st.success(f"Emails sent successfully to {success_count} out of {len(st.session_state['results'])} candidates.")

    if st.button("Send Email to Good Matches"):
        if 'credentials' not in st.session_state:
            st.warning("Please authorize the application first.")
        else:
            success_count = 0
            good_matches = [r for r in st.session_state['results'] if r['is_match']]
            for result in good_matches:
                if send_email(result['email'], "Job Application Update", email_body):
                    success_count += 1
            st.success(f"Emails sent successfully to {success_count} out of {len(good_matches)} good matches.")
