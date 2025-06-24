import subprocess
import os
from docx import Document
from openai import OpenAI
import sys
import time

# Open AI API Key
# IMPORTANT: Replace 'your-api-key-here' with your actual Open AI API key.
# WARNING: Hardcoding your API key is insecure. Do not share this script or store it in version control (e.g., Git).
API_KEY = "eeb30a1f4ce12d9ee245401f7ad803cdc21fde7"

# Paths
SHELL_SCRIPT_PATH = "/home/astin/Desktop/Projects/Performance metrics/perfffmetriclsshellscript.sh"
DEFAULT_OUTPUT_PATHS_FILE = "/home/astin/Desktop/Projects/Performance metrics/newfile/output_path.txt"
ANALYSIS_DIR = "/home/astin/Desktop/Projects/Performance metrics/Analysis_Reports"
DOCX_OUTPUT_PATH = os.path.join(ANALYSIS_DIR, "final_report.docx")

# Initialize Open AI client
try:
    client = OpenAI(api_key=API_KEY)
except Exception as e:
    print(f"Error: Could not initialize Open AI client. Ensure API_KEY is valid. {e}")
    sys.exit(1)

def run_shell_script():
    """Run the shell script interactively and wait for output_paths.txt to appear."""
    print("Running shell script. Waiting for user to enter package name, output directory, screen names, and navigate screens...")
    try:
        # Run without capturing output to allow interactive prompts
        subprocess.run([SHELL_SCRIPT_PATH], check=True)
        print("Shell script executed successfully.")
        
        # Wait for output_paths.txt to appear
        global OUTPUT_PATHS_FILE
        OUTPUT_PATHS_FILE = DEFAULT_OUTPUT_PATHS_FILE
        timeout = 120  # 2 minutes timeout
        check_interval = 5  # Check every 5 seconds
        elapsed = 0
        
        print(f"Waiting for output_paths.txt to appear at {OUTPUT_PATHS_FILE}...")
        while not os.path.exists(OUTPUT_PATHS_FILE) and elapsed < timeout:
            time.sleep(check_interval)
            elapsed += check_interval
            print(f"Still waiting... ({elapsed}/{timeout} seconds elapsed)")
        
        if not os.path.exists(OUTPUT_PATHS_FILE):
            print(f"Error: Output paths file not found at {OUTPUT_PATHS_FILE} after {timeout} seconds.")
            return False
        
        # Read output_paths.txt to get OUTPUT_DIR and output files
        output_files = []
        output_dir = None
        with open(OUTPUT_PATHS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("OUTPUT_DIR:"):
                    output_dir = line[len("OUTPUT_DIR:"):]
                    OUTPUT_PATHS_FILE = os.path.join(output_dir, "output_paths.txt")
                elif line.startswith("OUTPUT_FILE:"):
                    output_file = line[len("OUTPUT_FILE:"):]
                    if os.path.isfile(output_file):
                        output_files.append(output_file)
        
        if not output_files:
            print("No valid output files found in output_paths.txt")
            return False
        
        global OUTPUT_FILE_PATHS
        OUTPUT_FILE_PATHS = output_files
        print(f"Output files found: {', '.join(OUTPUT_FILE_PATHS)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running shell script: {e}")
        return False
    except FileNotFoundError:
        print(f"Shell script not found at {SHELL_SCRIPT_PATH}")
        return False

def read_output_files():
    """Read the contents of all output files."""
    data = []
    for output_file in OUTPUT_FILE_PATHS:
        if not os.path.exists(output_file):
            print(f"Output file not found at {output_file}")
            continue
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                # Extract screen name from file name
                screen_name = os.path.basename(output_file).replace("_performance.txt", "")
                data.append(f"Metrics for screen '{screen_name}':\n{content}\n{'='*80}\n")
        except Exception as e:
            print(f"Error reading output file {output_file}: {e}")
    if not data:
        print("No data read from output files")
        return None
    return "\n".join(data)

def call_gpt4o(data):
    """Send data to GPT-4o API with a prompt and get response."""
    prompt = f"""
    Analyze the following Android performance metrics data for an app, captured from gfxinfo, meminfo, cpuinfo, diskstats, and batterystats across multiple screens/transactions. The data is organized by screen, with each section labeled 'Metrics for screen <screen_name>'.

    {data}

    Provide a detailed textual analysis including:
    1. **Summary**: Key findings from the metrics for each screen (e.g., frame rendering performance, memory usage patterns, CPU load, disk I/O, battery consumption). Compare performance across screens where relevant.
    2. **Insights**: Identify performance bottlenecks, anomalies, or areas for optimization (e.g., high memory usage, frame drops, excessive battery drain) for each screen and across screens.
    3. **Recommendations**: Suggest specific improvements for the app's performance, prioritizing issues that impact multiple screens or have significant performance implications.

    Format the response clearly with sections for 'Summary', 'Insights', and 'Recommendations'. Ensure the analysis addresses each screen individually and provides a comparative overview where appropriate.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Android performance analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000  # Increased to handle multiple screens
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
    
    # Step 2: Read the output files
    data = read_output_files()
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