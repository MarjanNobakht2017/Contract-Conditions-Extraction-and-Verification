import openai
import json
import os
import re
from docx import Document
from dotenv import load_dotenv

# Load configuration from .env file
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

def clean_column_names(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

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

def validate_and_clean_json(response_content):
    try:
        return json.loads(response_content)
    except json.JSONDecodeError:
        cleaned_content = response_content.strip().strip('`').replace("'", '"')
        cleaned_content = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', cleaned_content)
        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
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
        return {"error": "API call failed", "details": str(e)}

def extract_conditions(contract_text):
    prompt = f"""
    Extract and structure in JSON format all key terms and conditions from the following contract. The JSON should clearly separate different sections and subsections of the contract. Pay special attention to the 'Amendment to the Service Agreement Regarding Travel Expenses', providing a detailed breakdown of each adjustment factor, its multiplier, and specific examples of their application. Format the output to facilitate automated analysis and ensure terms are related to their appropriate sections.

    Contract Text:
    {contract_text}

    Example of expected JSON format:
    {{
        "section1": {{
            "title": "Section Title",
            "terms": [
                {{
                    "term": "Term description",
                    "details": "Term details"
                }}
            ]
        }},
        "amendment_to_the_service_agreement_regarding_travel_expenses": {{
            "adjustment_factors": [
                {{
                    "factor": "Factor description",
                    "multiplier": "Multiplier value",
                    "example": "Example of application"
                }}
            ]
        }}
    }}
    """
    try:
        response = openai.ChatCompletion.create(
            engine=deployment_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        conditions = response['choices'][0]['message']['content'].strip()
        conditions_json = validate_and_clean_json(conditions)
        if conditions_json is None:
            raise json.JSONDecodeError("Failed to decode JSON after cleanup.", conditions, 0)
        return conditions_json
    except json.JSONDecodeError as json_err:
        return {"error": "Failed to decode JSON. Check the formatting of the output."}
    except Exception as e:
        return {"error": str(e)}
