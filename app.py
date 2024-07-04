from flask import Flask, request, jsonify
import pandas as pd
from docx import Document
from dotenv import load_dotenv
import os
from celery import Celery

# Load configuration from .env file
load_dotenv()

app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from tasks import analyze_task_description_with_openai, extract_conditions, save_conditions_to_file, load_conditions_from_file, clean_column_names, read_docx, read_txt

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

            task = extract_conditions.delay(contract_text)
            return jsonify({'task_id': task.id}), 202
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return render_template('index.html')

@app.route('/status/<task_id>')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'state': task.state, 'status': 'Pending...'}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'result': task.result}
    elif task.state == 'FAILURE':
        response = {'state': task.state, 'status': 'Failed', 'error': str(task.info)}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)