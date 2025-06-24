import subprocess
import requests
import os

# Configuration: Replace with your paths and API details
SHELL_SCRIPT = "/home/user/scripts/run_commands.sh"  # Path to shell script
OUTPUT_FILE = "/home/user/scripts/output.txt"       # Path to output file
API_URL = "https://api.example.com/analyze"         # Chatbot API endpoint
API_KEY = "your-api-key-here"                      # Your API key
REPORT_FILE = "/home/user/scripts/analysis_report.md"  # Path to save analysis

# Prompt for the chatbot
PROMPT = """
Analyze the data in the provided file. Summarize key findings in text, noting trends or anomalies. Create a graph (e.g., bar or line chart) to visualize the data. Return the response in Markdown format with the graph as a base64-encoded image or URL.
"""

def run_shell():
    """Run the shell script."""
    try:
        subprocess.run([SHELL_SCRIPT], check=True)
        print("Shell script ran successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Shell script error: {e}")
        return False
    except FileNotFoundError:
        print(f"Shell script not found: {SHELL_SCRIPT}")
        return False

def read_output():
    """Read the output file."""
    if not os.path.exists(OUTPUT_FILE):
        print(f"Output file not found: {OUTPUT_FILE}")
        return None
    try:
        with open(OUTPUT_FILE, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def call_api(content):
    """Send file content and prompt to the API."""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"prompt": PROMPT, "data": content}
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("content", "No content received")
    except requests.RequestException as e:
        print(f"API error: {e}")
        return None

def save_report(content):
    """Save the API response to a file."""
    try:
        with open(REPORT_FILE, 'w') as f:
            f.write(f"# Analysis Report\n\n{content}")
        print(f"Report saved to: {REPORT_FILE}")
    except Exception as e:
        print(f"Error saving report: {e}")

def main():
    """Main workflow."""
    if not run_shell():
        return
    content = read_output()
    if not content:
        return
    response = call_api(content)
    if response:
        save_report(response)

if __name__ == "__main__":
    main()