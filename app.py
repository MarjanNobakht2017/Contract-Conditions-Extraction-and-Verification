from flask import Flask, request, jsonify, render_template
from celery_config import celery_app
import pandas as pd
import io
from extract_conditions import extract_conditions, save_conditions_to_file, load_conditions_from_file, read_docx, read_txt
from analyze_tasks import analyze_all_task_descriptions, clean_column_names

app = Flask(__name__)

@celery_app.task(bind=True)
def process_files(self, contract_file_data, tasks_file_data):
    try:
        contract_file = io.BytesIO(contract_file_data['content'])
        tasks_file = io.BytesIO(tasks_file_data['content'])

        if contract_file_data['filename'].endswith('.docx'):
            contract_text = read_docx(contract_file)
        elif contract_file_data['filename'].endswith('.txt'):
            contract_text = read_txt(contract_file)
        else:
            return {'error': 'Unsupported file type'}

        conditions = extract_conditions(contract_text)

        if conditions:
            save_conditions_to_file(conditions)

            tasks_df = pd.read_excel(tasks_file)
            tasks_df = clean_column_names(tasks_df)

            loaded_conditions = load_conditions_from_file()

            violations = analyze_all_task_descriptions(tasks_df, loaded_conditions)
            return {'conditions': loaded_conditions, 'violations': violations}
        else:
            return {'error': 'Error extracting conditions'}

    except Exception as e:
        return {'error': str(e)}

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

        task = process_files.delay(contract_file_data, tasks_file_data)
        return jsonify({"task_id": task.id}), 202

    return render_template('upload.html')

@app.route('/task_status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = process_files.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info),
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)