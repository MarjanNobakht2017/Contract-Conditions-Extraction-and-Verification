from extract_conditions import *
from analyze_tasks import *
from flask import Flask, request, jsonify
import openai
import json
import pandas as pd
from docx import Document
from dotenv import load_dotenv
import os


app = Flask(__name__)
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

        conditions = extract_conditions(contract_text)

        if conditions:
            # save conditions to a JSON file
            save_conditions_to_file(conditions)

            # read the tasks file
            try:
                tasks_df = pd.read_excel(tasks_file)
                tasks_df = clean_column_names(tasks_df)
                print("Cleaned columns in tasks file:", tasks_df.columns)

                # load the conditions from the file
                loaded_conditions = load_conditions_from_file()

                violations = analyze_all_task_descriptions(tasks_df, loaded_conditions)
                return jsonify({'conditions': loaded_conditions, 'violations': violations})
            except Exception as e:
                return f'Error reading tasks file: {e}', 400
        else:
            return 'Error extracting conditions', 400
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Contract and Tasks</title>
    <!-- Link to Bootstrap CSS for styling -->
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .container {
            margin-top: 50px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-5">Upload Contract and Tasks</h1>
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label for="contractFile">Upload Contract:</label>
                <input type="file" class="form-control-file" id="contractFile" name="contract">
            </div>
            <div class="form-group">
                <label for="tasksFile">Upload Task Descriptions:</label>
                <input type="file" class="form-control-file" id="tasksFile" name="tasks">
            </div>
            <button type="submit" class="btn btn-primary">Analyze Tasks</button>
        </form>
    </div>

    <!-- Bootstrap JS and dependencies -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>
    '''


if __name__ == '__main__':
    app.run(debug=True)