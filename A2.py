import streamlit as st
import requests
import os
import google.genai as genai
from dotenv import load_dotenv
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import subprocess
import sys

# Load environment variables
load_dotenv()

# Retrieve Gemini API key from environment variables
gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Configure Gemini API
genai.configure(api_key=gemini_api_key)

# Ensure BeautifulSoup is installed
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from bs4 import BeautifulSoup
except ImportError:
    install('beautifulsoup4')
    from bs4 import BeautifulSoup

# Function to scrape data from the provided URL
def scrape_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract relevant data from the soup object
        paragraphs = soup.find_all('p')
        text_content = ' '.join([para.get_text() for para in paragraphs if para.get_text().strip()])
        return text_content
    except requests.exceptions.RequestException as e:
        st.error(f"Error scraping data: {e}")
        return None

# Function to generate actionable items and risk mitigations using Gemini API
def generate_actionable_risk_mitigation(text, model_name, custom_prompt=None):
    try:
        model = genai.GenerativeModel(model_name)
        
        # Generate actionable items
        actionable_prompt = custom_prompt or f"""
        Analyze the following text and provide a clear list of actionable items referring to the Paragraph based on the RBI circular:
        {text}
        """
        actionable_response = model.generate_content(actionable_prompt)
        actionable = actionable_response.text.strip()

        # Generate risk mitigations
        risk_prompt = custom_prompt or f"""
        Analyze the following text and provide a clear list of risk mitigations referring to the Paragraph based on the RBI circular:
        {text}
        """
        risk_response = model.generate_content(risk_prompt)
        risk_mitigation = risk_response.text.strip()

        return actionable, risk_mitigation
    except Exception as e:
        st.error(f"Error generating actionable items and risk mitigations: {e}")
        return None, None

# Function to export results as Excel
def export_to_excel(actionable, risk_mitigation):
    wb = Workbook()
    ws = wb.active
    ws.title = "Analysis Results"
    
    # Add actionable items
    ws.append(["Actionable Items"])
    for item in actionable.split('\n'):
        ws.append([item.strip()])
    
    # Add risk mitigations
    ws.append([])
    ws.append(["Risk Mitigations"])
    for item in risk_mitigation.split('\n'):
        ws.append([item.strip()])
    
    # Save to a BytesIO object
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    return excel_file

# Function to export results as PDF
def export_to_pdf(actionable, risk_mitigation):
    pdf_file = io.BytesIO()
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter
    
    # Add actionable items
    c.drawString(30, height - 30, "Actionable Items")
    y = height - 50
    for item in actionable.split('\n'):
        if item.strip():  # Only add non-empty lines
            c.drawString(30, y, item.strip())
            y -= 15
            if y < 50:  # Add new page if content exceeds page height
                c.showPage()
                y = height - 30
    
    # Add risk mitigations
    c.drawString(30, y, "Risk Mitigations")
    y -= 20
    for item in risk_mitigation.split('\n'):
        if item.strip():  # Only add non-empty lines
            c.drawString(30, y, item.strip())
            y -= 15
            if y < 50:  # Add new page if content exceeds page height
                c.showPage()
                y = height - 30
    
    c.save()
    pdf_file.seek(0)
    return pdf_file

# Streamlit app
st.title("Web Scraping and Analysis with Google Gemini")

# User input for URL
url = st.text_input("Enter the URL to scrape:")

# User input for custom prompt
custom_prompt = st.text_area("Enter a custom prompt for analysis (optional):")

# User input for model selection
model_options = [
    "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-pro-exp-02-05",
    "gemini-2.0-flash-thinking-exp-01-21", "gemini-2.0-flash-exp", "learnlm-1.5-pro-experimental",
    "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"
]  # Add more models as needed
selected_model = st.selectbox("Select a Gemini model:", model_options)

if url:
    # Scrape data from the provided URL
    text_content = scrape_data(url)
    if text_content:
        # Generate actionable items and risk mitigations
        actionable, risk_mitigation = generate_actionable_risk_mitigation(text_content, selected_model, custom_prompt)
        if actionable and risk_mitigation:
            # Display the results
            st.write("### Actionable Items")
            st.write(actionable)
            st.write("### Risk Mitigations")
            st.write(risk_mitigation)

            # Export options
            st.write("### Export Results")
            export_format = st.selectbox("Select export format:", ["Excel", "PDF"])
            
            if export_format == "Excel":
                excel_file = export_to_excel(actionable, risk_mitigation)
                st.download_button(
                    label="Download Excel",
                    data=excel_file,
                    file_name="analysis_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif export_format == "PDF":
                pdf_file = export_to_pdf(actionable, risk_mitigation)
                st.download_button(
                    label="Download PDF",
                    data=pdf_file,
                    file_name="analysis_results.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("No actionable items or risk mitigations found.")
    else:
        st.warning("No data retrieved from the provided URL.")
else:
    st.info("Please enter a URL to begin.")
