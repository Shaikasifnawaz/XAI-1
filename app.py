import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from docx import Document
import re
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Set up the Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/*": {"origins": ["http://localhost:3000", "https://asci.meanhost.in"]}
})

# Get the XAI API key from the environment variables
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Set a file size limit for uploads (16MB limit)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Function to extract text from a Word file in a memory-efficient manner
def extract_text_from_word(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return '\n'.join(text)

# Function to handle markdown-style links and emails
def handle_links(line):
    link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
    line = link_pattern.sub(r'<a href="\2">\1</a>', line)

    url_pattern = re.compile(r'(http[s]?://[^\s]+)')
    line = url_pattern.sub(r'<a href="\1">\1</a>', line)

    email_pattern = re.compile(r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)')
    line = email_pattern.sub(r'<a href="mailto:\1">\1</a>', line)

    return line

# Function to escape HTML special characters
def escape_html(text):
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#039;"))

# Function to convert markdown-like text to HTML
def get_html(text: str, is_table: bool = False) -> str:
    lines = text.split('\n')
    html_output = """<div style="max-width: 1000px; padding: 15px; margin: 0 auto; height: 100%; display: flex; flex-direction: column; justify-content: center; overflow-x: auto;">"""
    
    # If is_table is True, start the table
    if is_table:
        html_output += "<table style='border-collapse: collapse; width: 100%;'>"

    list_open = False
    table_open = False
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip blank lines

        # Check for markdown table structure
        if "|" in line:
            if not table_open:
                html_output += "<tr>"  # Start a table row for the first table line
                table_open = True

            # Detect table header (usually separated by dashes)
            if "-" in line:
                headers = line.split("|")
                for header in headers:
                    html_output += f"<th style='border: 1px solid black; padding: 5px; text-align: left;'>{escape_html(header.strip())}</th>"
                html_output += "</tr>"
            else:
                cells = line.split("|")
                html_output += "<tr>"
                for cell in cells:
                    cell_content = cell.strip()
                    if cell_content:  # Only add <td> if the content is not empty
                        html_output += f"<td style='border: 1px solid black; padding: 5px;'>{escape_html(cell_content)}</td>"
                html_output += "</tr>"

        # Handle other markdown formats
        elif line.startswith("# "):
            html_output += f'<h2>{escape_html(line[2:])}</h2>'
        elif line.startswith("## "):
            html_output += f'<h3>{escape_html(line[3:])}</h3>'
        elif line.startswith("### "):
            html_output += f'<h4>{escape_html(line[4:])}</h4>' 
        elif line.startswith("**") and line.endswith("**"):
            html_output += f'<strong>{escape_html(line[2:-2])}</strong>'
        elif line.startswith("* "):
            if not list_open:
                html_output += '<ul>'
                list_open = True
            html_output += f'<li>{escape_html(line[2:])}</li>'
        else:
            if list_open:
                html_output += '</ul>'
                list_open = False

            line = handle_links(escape_html(line))

            if is_table:
                # Convert line into a table row if 'is_table' is True
                html_output += f"<tr><td>{line}</td></tr>"
            else:
                html_output += f'<div style="margin-bottom: 10px;">{line}</div>'

    # Close the table if 'is_table' is True
    if table_open:
        html_output += "</table>"

    html_output += '</div>'
    return html_output

# Remaining functions and routes remain the same...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
