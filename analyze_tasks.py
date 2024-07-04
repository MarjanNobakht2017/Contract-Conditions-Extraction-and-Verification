import openai
import json
from dotenv import load_dotenv
import os
import re

# load configuration from .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID")

# Configure OpenAI
openai.api_key = api_key
openai.api_base = azure_endpoint
openai.api_type = "azure"
openai.api_version = api_version


def validate_and_clean_json(response_content):
    try:
        return json.loads(response_content)
    except json.JSONDecodeError:
        # fix common JSON formatting issues
        cleaned_content = response_content.strip().strip('`').replace("'", '"')
        cleaned_content = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', cleaned_content)
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"Final attempt failed to clean and parse JSON: {e}")
            print("Final cleaned content:", cleaned_content)
            return None


def analyze_task_description_with_openai(task_description, task_cost, conditions):
    prompt = f"""
    Given the following contract conditions:
    {json.dumps(conditions, indent=4)}

    Analyze the following task description for compliance with these contract conditions, specifically considering the provided cost estimate:
    Task Description: {task_description}
    Cost Estimate: {task_cost}

    If the task description or the cost violates one or more conditions, specify the reason for the violation in structured JSON format.
    """
    try:
        response = openai.ChatCompletion.create(
            engine=deployment_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        analysis = response['choices'][0]['message']['content'].strip()
        analysis_json = validate_and_clean_json(analysis)
        return analysis_json if analysis_json else {"error": "Failed to decode JSON after cleanup."}
    except Exception as e:
        print(f"Error analyzing task description: {e}")
        return {"error": "API call failed", "details": str(e)}


def analyze_all_task_descriptions(tasks_df, conditions):
    results = []
    for index, row in tasks_df.iterrows():
        task_description = row['task_description']
        task_cost = row['amount']
        analysis = analyze_task_description_with_openai(task_description, task_cost, conditions)
        results.append({'task': task_description, 'cost': task_cost, 'analysis': analysis})
    return results
