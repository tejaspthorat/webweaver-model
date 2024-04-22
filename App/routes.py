from openai import OpenAI
from flask import Flask, request, jsonify, Blueprint
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import io
import PyPDF2
import base64
from docx import Document
# import supabase


TOGETHER_API_KEY = "7f1a00ec62d34939cc57c8c59e68f5fea25867c892d1ec141af64fe3324b516c"


client = OpenAI(
  api_key=TOGETHER_API_KEY,
  base_url='https://api.together.xyz/v1',
)

def askLLM(prompt):
    completion = client.chat.completions.create(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    messages=[
      {
        "role": "user",
        "content": prompt,
      }
    ],
    n=1,
    max_tokens=4000,
    temperature=0.1,
    top_p=0.9,
   )
    return completion.choices[0].message.content

def base64_to_docx(base64_string, filename):
    '''
    converts base64 string to docx file
    '''
    binary_data = base64.b64decode(base64_string)
    docx_buffer = io.BytesIO(binary_data)
    docx_doc = Document(docx_buffer)
    docx_doc.save(filename)

# def upload_to_supabase(base64_string, path):
#     with open(path, 'rb') as f:
#         supabase.storage.from_("testbucket").upload(file=f,path="/docs")

def extract_text(url):
  '''
  Extracts data from the supabase/firebase public url

  '''
  response = requests.get(url)
  pdf_content = io.BytesIO(response.content)
  
  pdf_reader = PyPDF2.PdfReader(pdf_content)
  text = ''
  for page_number in range(len(pdf_reader.pages)):
    text += pdf_reader.pages[page_number].extract_text()

  text = text.encode('ascii', 'backslashreplace').decode('ascii', 'ignore')
  print(text)

  return text

def getPrompt(job_description, resume):
    prompt = f"""You are a smart AI assistant expert to compare resume against job description and provide feedback.
    
    Job Description:{job_description}
    
    Resume:{resume}

    Provide feedback in a point format with suggestions for improvement and areas of strength. Include specific examples or references from the resume and job description to support your evaluation.
    """

    return prompt

def getPromptForGeneration(resumeJSON):
    prompt = f"""
    You are a smart AI assistant expert to generate a resume based on the given JSON data.

    json: {resumeJSON}

    Generate a resume based on the given JSON data. Include all the relevant information and format it in a professional manner.

"""
    return prompt

def getPromptForColdEmail(name , job_description, company ,contact):
    prompt = f"""
    You are a smart AI assistant responsible to write proffessional emails based on the job descripion and email type.

    name of the applicant: {name}

    contact information: {contact}

    job description: {job_description}

    email_type: {email_type}

"""
    return prompt



def send_email(sendto, name, reply_to, is_html, title, body):

    msg = MIMEMultipart()
    msg['From'] = reply_to
    msg['To'] = sendto
    msg['Subject'] = title

    msg.attach(MIMEText(body, 'plain'))

    # Connect to SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sendto, 'jhdt nfec tqlv pwpo')

    # Send the email
    server.sendmail(sendto, reply_to, msg.as_string())

    # Close the SMTP server connection
    server.quit()




# app = Flask(__name__)
main = Blueprint('main', __name__)

@main.route('/compare', methods=['POST'])
def compare():
    data = request.get_json()
    job_description = data['job_description']
    url = data['resume_url']
    resume = extract_text(url)
    print(resume)
    prompt = getPrompt(job_description, resume)
    response = askLLM(prompt)
    return jsonify({'response': response})

@main.route('/generation', methods=['POST'])
def generation():
    data = request.get_json()
    print(data)
    prompt = getPromptForGeneration(data)
    response = askLLM(prompt)
    return jsonify({'response': response})
    
# @app.route('/coldEmail', methods = ["POST"])
# def getEmail():
#     data = request.get_json()
#     jd = data["job_description"]
#     email_type = data["email_type"]

#     prompt = getPromptForColdEmail(jd, email_type)
#     response = askLLM(prompt)

#     return jsonify({"response": response})

@main.route('/sendEmail', methods = ["POST"])
def sendMail():
    data = request.get_json()
    reply_to = data["sendTo"]
    name = data["name"]
    job_description = data["job_description"]
    email_type = data["mail_type"]

    if(data['name'] == 'unknown'):
        data['name'] = 'Ameya Surana'

    print(data)

    prompt = getPromptForColdEmail(name , job_description, email_type, "+91 1234567890")
    response = askLLM(prompt)

    sendto = "ameyasurana10@gmail.com"
    is_html = "false"
    title = "Job Application"
    body = response
    print(response)
    send_email(sendto, name, reply_to, is_html, title, body)

    return jsonify({"response": "Email sent successfully"})
