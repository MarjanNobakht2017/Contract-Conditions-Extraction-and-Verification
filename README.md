# Contract Conditions Extraction and Task Analysis System

## Overview

This project provides a system for extracting key terms and conditions from a contract and analyzing task descriptions for compliance with these extracted conditions. The system is designed to help ensure that tasks adhere to contract constraints such as budget limits and allowable types of work.

## Features

- **Contract Conditions Extraction:** Automatically extracts and structures key terms from a provided contract text into a JSON format.
- **Task Compliance Analysis:** Analyzes task descriptions from a CSV file for compliance with the extracted contract conditions, specifying reasons for any violations.
- **User Interface:** Provides an interface for uploading documents, performing analysis, and displaying results.
- **Documentation:** Comprehensive documentation on the system's operation and each component.

## Installation

### Prerequisites

- Python 3.x
- Flask
- Pandas
- Other dependencies listed in `requirements.txt`

### Setup

1. **Clone the repository:**
    ```bash
    git clone git@github.com:MarjanNobakht2017/Contract-Conditions-Extraction-and-Verification.git
    cd Contract-Conditions-Extraction-and-Verification
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the application:**
    ```bash
    python app.py
    ```
   
## Usage

1. **Access the Interface:**
   - Open your web browser and navigate to `https://pristine-badlands-91837-8a3526ef12a6.herokuapp.com`.
   - Note: Due to limitations of Heroku and the time taken by OpenAI's API to process requests, completing the task might take some time. Please be patient while the system processes the contract and tasks.



2. **Upload Contract:**
   - Upload the contract text file containing the terms and conditions.

3. **Upload Task Descriptions:**
   - Upload the CSV file containing task descriptions with cost estimates.

4. **Analyze Tasks:**
   - Click on the "Analyze" button to check each task description for compliance with the contract conditions.

5. **View Results:**
   - The results will display whether each task is compliant or not, and if not, the reason for the violation.

## JSON Structure for Contract Conditions

The extracted contract conditions are structured in a JSON format as follows:

```json
{
  "section1": {
    "subsection1": {
      "term1": "description",
      "term2": "description"
    },
    "subsection2": {
      "term3": "description"
    }
  },
  "section2": {
    "subsection1": {
      "term4": "description"
    }
  }
}