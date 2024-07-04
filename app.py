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

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        contract_file = request.files['contract']
        tasks_file = request.files['tasks']

        filename = contract_file.filename.lower()

        try:
            if filename.endswith('.docx'):
                contract_text = read_docx(contract_file)
            elif filename.endswith('.txt'):
                contract_text = read_txt(contract_file)
            else:
                return 'Unsupported file type', 400
        except Exception as e:
            return f'Error reading file: {e}', 400

        # Process conditions extraction asynchronously
        task = extract_conditions.delay(contract_text)
        return jsonify({'task_id': task.id}), 202
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Contract and Tasks</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    <style>
        #result { display: none; }
        #status { margin-top: 20px; }
    </style>
</head>
<body>
    <form id="uploadForm" action="/" method="post" enctype="multipart/form-data">
        <input type="file" name="contract" required>
        <input type="file" name="tasks" required>
        <button type="submit">Upload and Analyze</button>
    </form>
    <div id="status"></div>
    <div id="result"></div>

    <script>
        $(document).ready(function() {
            $('#uploadForm').submit(function(e) {
                e.preventDefault();
                var formData = new FormData(this);
                $('#status').text('Processing...');

                $.ajax({
                    url: '/',
                    type: 'POST',
                    data: formData,
                    success: function(data) {
                        var taskId = data.task_id;
                        checkStatus(taskId);
                    },
                    cache: false,
                    contentType: false,
                    processData: false
                });
            });

            function checkStatus(taskId) {
                var interval = setInterval(function() {
                    $.getJSON('/status/' + taskId, function(data) {
                        if (data.state === 'SUCCESS') {
                            $('#status').text('Completed');
                            $('#result').text(JSON.stringify(data.result, null, 2)).show();
                            clearInterval(interval);
                        } else if (data.state === 'FAILURE') {
                            $('#status').text('Failed: ' + data.status);
                            clearInterval(interval);
                        }
                    });
                }, 2000);
            }
        });
    </script>
</body>
</html>

    '''

@app.route('/status/<task_id>')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info), 
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
