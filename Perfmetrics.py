import subprocess
import requests
import os
from datetime import datetime

# Configuration: Replace these with your actual paths and API details
SHELL_SCRIPT_PATH = "/path/to/run_commands.sh"  # Path to your shell script
OUTPUT_FILE_PATH = "/path/to/output.txt"       # Path to the shell script's output file
API_ENDPOINT = "https://api.example.com/analyze"  # Replace with chatbot API endpoint
API_KEY = "your-api-key-here"                  # Replace with your API key
OUTPUT_REPORT_PATH = "analysis_report.md"      # Path to save the chatbot's response

# Prompt for the chatbot
PROMPT = """
Analyze the data in the provided file. Provide a detailed text summary of the key findings, including any trends or anomalies. Generate at least one relevant graph (e.g., bar chart, line plot) to visualize the data. Return the response in Markdown format, with the graph embedded as a base64-encoded image or URL.
"""

def run_shell_script():
    """Run the shell script and check for errors."""
    try:
        result = subprocess.run(
            [SHELL_SCRIPT_PATH],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Shell script executed successfully.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running shell script: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Shell script not found at: {SHELL_SCRIPT_PATH}")
        return False

def read_output_file():
    """Read the content of the output file."""
    if not os.path.exists(OUTPUT_FILE_PATH):
        print(f"Output file not found at: {OUTPUT_FILE_PATH}")
        return None
    try:
        with open(OUTPUT_FILE_PATH, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"Error reading output file: {e}")
        return None

def send_to_chatbot(file_content):
    """Send the file content and prompt to the chatbot API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": PROMPT,
        "file_content": file_content
    }
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()  # Assuming the API returns JSON
    except requests.RequestException as e:
        print(f"Error sending request to API: {e}")
        return None

def save_response(response_data):
    """Save the chatbot's response to a file."""
    try:
        # Assuming the API returns a 'content' field with Markdown
        content = response_data.get('content', 'No content received.')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(OUTPUT_REPORT_PATH, 'w') as file:
            file.write(f"# Analysis Report\n\n")
            file.write(f"Generated on: {timestamp}\n\n")
            file.write(content)
        print(f"Analysis report saved to: {OUTPUT_REPORT_PATH}")
    except Exception as e:
        print(f"Error saving response: {e}")

def main():
    """Main function to orchestrate the workflow."""
    # Step 1: Run the shell script
    if not run_shell_script():
        print("Aborting due to shell script error.")
        return

    # Step 2: Read the output file
    file_content = read_output_file()
    if not file_content:
        print("Aborting due to output file error.")
        return

    # Step 3: Send to chatbot API
    response_data = send_to_chatbot(file_content)
    if not response_data:
        print("Aborting due to API error.")
        return

    # Step 4: Save the response
    save_response(response_data)

if __name__ == "__main__":
    main()