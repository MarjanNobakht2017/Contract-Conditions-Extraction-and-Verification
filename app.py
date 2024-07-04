from flask import Flask, request, jsonify, render_template
import os
import pandas as pd
from docx import Document
from dotenv import load_dotenv
from tasks import extract_conditions, analyze_task_description_with_openai
import threading
import uuid
import json

# Load .env configuration
load_dotenv()

app = Flask(__name__)

# In-memory storage for task results (not suitable for production)
tasks = {}

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

def process_task(task_id, contract_text, tasks_df):
    try:
        conditions = extract_conditions(contract_text)
        analysis_results = []
        for _, row in tasks_df.iterrows():
            task_description = row['task_description']
            task_cost = row['amount']
            analysis = analyze_task_description_with_openai(task_description, task_cost, conditions)
            analysis_results.append({
                'task_description': task_description,
                'task_cost': task_cost,
                'analysis': analysis
            })
        tasks[task_id] = {'status': 'completed', 'conditions': conditions, 'analysis_results': analysis_results}
    except Exception as e:
        tasks[task_id] = {'status': 'failed', 'error': str(e)}

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

            tasks_df = pd.read_excel(tasks_file)
            tasks_df = tasks_df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))

            task_id = str(uuid.uuid4())
            tasks[task_id] = {'status': 'processing'}

            # Start the processing in a new thread
            thread = threading.Thread(target=process_task, args=(task_id, contract_text, tasks_df))
            thread.start()

            return jsonify({'task_id': task_id}), 202
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return render_template('index.html')

@app.route('/status/<task_id>')
def task_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task ID'}), 404
    return jsonify(task)

if __name__ == '__main__':
    app.run(debug=True)
