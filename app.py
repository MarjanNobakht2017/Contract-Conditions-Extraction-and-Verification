from flask import Flask, request, jsonify, render_template
import os
import pandas as pd
from docx import Document
from dotenv import load_dotenv
import time

# Load .env configuration
load_dotenv()

app = Flask(__name__)

def read_docx(file):
    doc = Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def read_txt(file):
    try:
        return file.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            return file.read().decode('latin-1')
        except Exception as e:
            raise ValueError(f"Error decoding file: {e}")

def extract_conditions(contract_text):
    # Simulate long-running task
    time.sleep(10)  # Simulate a delay
    return {"conditions": "Extracted conditions from the contract."}

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        contract_file = request.files.get('contract')
        tasks_file = request.files.get('tasks')

        if not contract_file or not tasks_file:
            return jsonify({'error': 'Missing files'}), 400

        try:
            if contract_file.filename.lower().endswith('.docx'):
                contract_text = read_docx(contract_file)
            elif contract_file.filename.lower().endswith('.txt'):
                contract_text = read_txt(contract_file)
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

            conditions = extract_conditions(contract_text)
            return jsonify({'conditions': conditions}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
