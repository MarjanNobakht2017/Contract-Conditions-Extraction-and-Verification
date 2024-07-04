from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from tasks import extract_conditions, analyze_task_description_with_openai, read_docx, read_txt

# Load .env configuration
load_dotenv()

app = Flask(__name__)

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

            # Read tasks and analyze each task with conditions
            tasks_df = pd.read_excel(tasks_file)
            tasks_df = tasks_df.rename(columns=lambda x: x.strip().lower().replace(' ', '_'))
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

            return jsonify({'conditions': conditions, 'analysis_results': analysis_results}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
