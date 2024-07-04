from flask import Flask, request, jsonify
import openai
import json
import pandas as pd
from docx import Document
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


def clean_column_names(df):
    # cleans and standardizes column names by stripping whitespace and converting to lowercase
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
        # clean the content by fixing common JSON issues
        cleaned_content = response_content.strip().strip('`')
        cleaned_content = cleaned_content.replace("'", '"')

        # missing quotes around property names
        cleaned_content = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', cleaned_content)

        try:
            return json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"Final attempt failed to clean and parse JSON: {e}")
            print("Final cleaned content:", cleaned_content)
            return None


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

        print("Extracted conditions:", conditions)

        conditions_json = validate_and_clean_json(conditions)
        if conditions_json is None:
            raise json.JSONDecodeError("Failed to decode JSON after cleanup.", conditions, 0)
        return conditions_json
    except json.JSONDecodeError as json_err:
        print(f"JSONDecodeError: {json_err}")
        return {"error": "Failed to decode JSON. Check the formatting of the output."}
    except Exception as e:
        print(f"Error extracting conditions: {e}")
        return {"error": str(e)}


def save_conditions_to_file(conditions, filename='extracted_conditions_new.json'):
    """Save the extracted conditions to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(conditions, json_file, indent=4)


def load_conditions_from_file(filename='extracted_conditions_new.json'):
    with open(filename, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)
