import subprocess
import os
from docx import Document
from openai import OpenAI
import sys
import re

# Paths
SHELL_SCRIPT_PATH = "/home/astin/Desktop/Projects/Performance metrics/perfffmetriclsshellscript.sh"
# OUTPUT_FILE_PATH will be dynamically determined from shell script output
ANALYSIS_DIR = "/home/astin/Desktop/Projects/Performance metrics/Analysis_Reports"
DOCX_OUTPUT_PATH = os.path.join(ANALYSIS_DIR, "final_report.docx")

# Initialize Open AI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Error: Could not initialize Open AI client. Ensure OPENAI_API_KEY is set. {e}")
    sys.exit(1)

def run_shell_script():
    """Run the shell script and extract OUTPUT_FILE_PATH from stdout."""
    try:
        result = subprocess.run([SHELL_SCRIPT_PATH], check=True, capture_output=True, text=True)
        print("Shell script executed successfully.")
        # Search for 'Done: Saved to <path>' in stdout
        match = re.search(r"Done: Saved to (.+)", result.stdout)
        if match:
            output_file = match.group(1).strip()
            if os.path.isfile(output_file):
                global OUTPUT_FILE_PATH
                OUTPUT_FILE_PATH = output_file
                print(f"Output file path set to: {OUTPUT_FILE_PATH}")
                return True
            else:
                print(f"Output file not found at: {output_file}")
                return False
        else:
            print("Could not find output file path in shell script output")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error running shell script: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Shell script not found at {SHELL_SCRIPT_PATH}")
        return False

def read_output_file():
    """Read the output file if it exists."""
    if not os.path.exists(OUTPUT_FILE_PATH):
        print(f"Output file not found at {OUTPUT_FILE_PATH}")
        return None
    try:
        with open(OUTPUT_FILE_PATH, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading output file: {e}")
        return None

def call_gpt4o(data):
    """Send data to GPT-4o API with a prompt and get response."""
    prompt = f"""
    Analyze the following Android performance metrics data for the Zomato app, captured from gfxinfo, meminfo, cpuinfo, diskstats, and batterystats:
    {data}

    Provide a detailed textual analysis including:
    1. **Summary**: Key findings from the metrics (e.g., frame rendering performance, memory usage patterns, CPU load, disk I/O, battery consumption).
    2. **Insights**: Identify any performance bottlenecks, anomalies, or areas for optimization (e.g., high memory usage, frame drops, excessive battery drain).
    3. **Recommendations**: Suggest specific improvements for the app's performance based on the data.

    Format the response clearly with sections for 'Summary', 'Insights', and 'Recommendations'.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Android performance analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling GPT-4o API: {e}")
        return None

def save_to_docx(response_text):
    """Save the API response to a DOCX file in a new folder."""
    # Create Analysis_Reports folder if it doesn't exist
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    
    doc = Document()
    doc.add_heading("Final Report", 0)
    doc.add_paragraph(response_text)
    
    try:
        doc.save(DOCX_OUTPUT_PATH)
        print(f"Analysis saved to {DOCX_OUTPUT_PATH}")
    except Exception as e:
        print(f"Error saving DOCX file: {e}")

def main():
    # Step 1: Run the shell script
    if not run_shell_script():
        sys.exit(1)
    
    # Step 2: Read the output file
    data = read_output_file()
    if not data:
        sys.exit(1)
    
    # Step 3: Call GPT-4o API
    response = call_gpt4o(data)
    if not response:
        sys.exit(1)
    
    # Step 4: Save to DOCX
    save_to_docx(response)

if __name__ == "__main__":
    main()