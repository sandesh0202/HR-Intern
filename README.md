# Multi-Resume Parser and Job Matcher

This Python Streamlit application parses resumes from a folder, extracts essential information (name, email, phone, LinkedIn profile, and skills) using `PyPDF2` and regex, and uses `LangChain` with the Groq language model to determine if a candidate is a good match for a job description. The app also features email functionality using OAuth 2.0 and the Gmail API to send emails to candidates.

## Features

1. **Resume Parsing**: Extracts text and links from PDF resumes.
2. **Information Extraction**: Uses regular expressions to extract email, phone numbers, and LinkedIn profiles from resumes.
3. **LangChain for Job Matching**: Uses `LangChain` with a Groq model to analyze resumes and determine if a candidate is a good match for a job description.
4. **Save Results to CSV**: Extracted data is saved to a CSV file for future use.
5. **OAuth 2.0 for Gmail API**: Allows sending personalized emails to candidates via Gmail after OAuth authorization.
6. **Streamlit GUI**: Provides an interactive web interface for managing resume processing, email authorization, and sending emails.

## Requirements

Ensure you have the following Python libraries installed:

- `streamlit`
- `PyPDF2`
- `re` (built-in module)
- `os` (built-in module)
- `csv` (built-in module)
- `langchain_groq`
- `langchain`
- `pydantic`
- `google-auth-oauthlib`
- `google-auth`
- `google-api-python-client`
- `email` (built-in module)
- `base64` (built-in module)

Install the required libraries via pip:

```bash
pip install streamlit PyPDF2 langchain_groq langchain pydantic google-auth google-auth-oauthlib google-api-python-client
```

## How to Use

1. **Set up Resumes Folder**: Store all your PDF resumes in a folder. The application will process all PDF files in the folder.
2. **Prepare Job Description**: Enter the job description that you want to match the resumes against.
3. **Run the Streamlit App**: Execute the following command in your terminal:
   
   ```bash
   streamlit run main.py
   ```

4. **Enter Required Information**: In the app, input the folder path containing the resumes, the job description, and the output CSV file name.
5. **Process Resumes**: Click the "Process Resumes" button. The app will parse the resumes and extract relevant information.
6. **Email Setup**: Use the OAuth 2.0 flow to authorize your Google account for sending emails via the Gmail API.
7. **Send Emails**: After authorization, you can send personalized emails to all candidates or only those who are a good match for the job.

## Functionality Breakdown

### 1. **extract_text_and_links_from_pdf(pdf_path)**
   - Extracts text and hyperlinks from a given PDF file.

### 2. **extract_linkedin_profiles(text, links)**
   - Extracts LinkedIn profile URLs from both the text and hyperlinks in a resume.

### 3. **extract_info(text, links)**
   - Extracts email addresses, phone numbers, and LinkedIn profiles using regular expressions.

### 4. **LangChain Integration**
   - Uses the `ChatGroq` model from LangChain to analyze the resume and match it against the job description.
   - Extracts name and skills from the resume and determines whether the candidate is a good fit.

### 5. **process_folder(folder_path, job_description)**
   - Iterates through all PDF resumes in the specified folder, extracts text, runs the Groq analysis, and collects results.

### 6. **save_to_csv(results, output_file)**
   - Saves the parsed results to a CSV file.

### 7. **OAuth 2.0 Gmail Integration**
   - Provides a flow to authenticate and authorize Gmail access using OAuth 2.0.
   - Sends personalized emails to candidates based on the parsed information.

### 8. **Streamlit Interface**
   - A simple, intuitive user interface for inputting folder paths, job descriptions, email content, and sending emails.

## Example CSV Output

The results CSV file will have the following format:

| Name       | Email              | Phone        | LinkedIn                    | Skills               | Is Match |
|------------|--------------------|--------------|-----------------------------|----------------------|----------|
| John Doe   | john@example.com    | 123-456-7890 | linkedin.com/in/johndoe      | Python, JavaScript    | True     |
| Jane Smith | jane@example.com    | 555-123-4567 | linkedin.com/in/janesmith    | Machine Learning, SQL | False    |

## OAuth 2.0 for Gmail API

The app supports sending personalized emails via Gmail using OAuth 2.0. To set this up:

1. Set up a project on Google Cloud and enable the Gmail API.
2. Download the OAuth credentials JSON file.
3. Use the `google-auth-oauthlib` and `google-api-python-client` libraries to handle OAuth and Gmail API access.

## License

This project is licensed under the MIT License.

---
