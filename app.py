from flask import Flask, request, jsonify, render_template
import threading
import pandas as pd
import io
from extract_conditions import extract_conditions, save_conditions_to_file, load_conditions_from_file, read_docx, read_txt
from analyze_tasks import analyze_all_task_descriptions, clean_column_names
import uuid

app = Flask(__name__)

tasks = {}

def process_files_task(task_id, contract_file_data, tasks_file_data):
    try:
        contract_file = io.BytesIO(contract_file_data['content'])
        tasks_file = io.BytesIO(tasks_file_data['content'])

        if contract_file_data['filename'].endswith('.docx'):
            contract_text = read_docx(contract_file)
        elif contract_file_data['filename'].endswith('.txt'):
            contract_text = read_txt(contract_file)
        else:
            tasks[task_id] = {'error': 'Unsupported file type'}
            return

        conditions = extract_conditions(contract_text)

        if conditions:
            save_conditions_to_file(conditions)

            tasks_df = pd.read_excel(tasks_file)
            tasks_df = clean_column_names(tasks_df)

            loaded_conditions = load_conditions_from_file()

            violations = analyze_all_task_descriptions(tasks_df, loaded_conditions)
            tasks[task_id] = {'conditions': loaded_conditions, 'violations': violations}
        else:
            tasks[task_id] = {'error': 'Error extracting conditions'}

    except Exception as e:
        tasks[task_id] = {'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        contract_file = request.files['contract']
        tasks_file = request.files['tasks']

        contract_file_data = {
            'filename': contract_file.filename.lower(),
            'content': contract_file.read()
        }

        tasks_file_data = {
            'filename': tasks_file.filename.lower(),
            'content': tasks_file.read()
        }

        task_id = str(uuid.uuid4())
        tasks[task_id] = {'state': 'PENDING'}

        thread = threading.Thread(target=process_files_task, args=(task_id, contract_file_data, tasks_file_data))
        thread.start()

        return jsonify({"task_id": task_id}), 202

    return render_template('upload.html')

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = tasks.get(task_id, None)
    if task is None:
        response = {
            'state': 'NOT_FOUND',
            'status': 'Task not found'
        }
    elif 'error' in task:
        response = {
            'state': 'FAILURE',
            'result': task
        }
    elif 'conditions' in task and 'violations' in task:
        response = {
            'state': 'SUCCESS',
            'result': task
        }
    else:
        response = {
            'state': 'PENDING',
            'status': 'Pending...'
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
