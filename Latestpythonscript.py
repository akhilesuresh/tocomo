import subprocess
import os
from docx import Document
from openai import OpenAI
import sys
import time

# QBurst LLM Gateway API Key
# IMPORTANT: Replace 'your-qburst-api-key-here' with your actual QBurst LLM gateway API key.
# WARNING: Hardcoding your API key is insecure. Do not share this script or store it in version control (e.g., Git).
API_KEY = "79c03ca6297bcab2b21cb918010df67bb654fe7232a0f58c"

# Paths
SHELL_SCRIPT_PATH = "/home/astin/Desktop/Projects/Performance metrics/perfffmetriclsshellscript.sh"
DEFAULT_OUTPUT_PATHS_FILE = "/home/astin/Desktop/Projects/Performance metrics/newfile/output_path.txt"
ANALYSIS_DIR = "/home/astin/Desktop/Projects/Performance metrics/Analysis_Reports"
DOCX_OUTPUT_PATH = os.path.join(ANALYSIS_DIR, "final_report.docx")

# Initialize Open AI client with QBurst LLM gateway
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://llmgateway.qburst.build/v1"
    )
except Exception as e:
    print(f"Error: Could not initialize QBurst LLM gateway client. Ensure API_KEY is valid. {e}")
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
    """Send data to QBurst LLM gateway (Mistral provider, gpt-4o model) with a prompt and get response."""
    prompt = f"""
    Analyze the following Android performance metrics data for an app, captured from gfxinfo, meminfo, cpuinfo, diskstats, and batterystats across multiple screens/transactions. The data is organized by screen, with each section labeled 'Metrics for screen <screen_name>'.

    {data}
Read the given text file in data and analyse the results of the adb commands and generate a report with the following contents:
Title: <Package> Performance Report
Introduction: <Give a formal introduction to the document>
Assumptions: <point out that network conditions and other test environment factors that may affect the result>
3. App Info <create a table with bold boundaries>
Timestamp: <Fetch from the top of the document>
Device ID: f(x)
Package: f(x)
Screen: f(x)
PID: f(x)
Rendering Pipeline: f(x)
Function f(x) = <Fetch from the document>
Function table(Metric[], name, additional parameter) = <create a table with 3 columns namely Metric, Value and Status. table name = name. populate the Metric column with values in Metric[]. For Value  column Metric[i] = f(x). For Status column - PASS or FAIL as against the (if provided(Parameters) else(normal industry standard)). table boundaries = bold. font = sans serif. >
table([Total frames rendered, Janky frames, Janky frames (legacy), 50th percentile frame time, 90th percentile frame time, 95th percentile frame time, 99th percentile frame time, Frame deadline missed, Frame deadline missed (legacy)], Frame Rendering Metrics)
table([ Missed Vsync, High input latency, Slow UI thread, Slow bitmap uploads, Slow issue draw commands], UI Performance Bottleneck)

table([ 50th percentile GPU frame time, 90th percentile GPU frame time, 95th percentile GPU frame time, 99th percentile GPU frame time], GPU Metrics)

table([Glyph Cache Glyph Count Total CPU MemoryMemory Usage], CPU Memory Usage, Display RSS and PSS for each)

table([Java Heap, Native Heap, Code, Stack, Graphics, Private, System],Memory Usage, add more columns to accommodate all data)
table([Texture (Image), RenderTarget, Stencil, Other (Total)], GPU Memory Usage)
Test Results: <Write the test results>
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Android performance analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10000  # Increased to handle multiple screens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling QBurst LLM gateway: {e}")
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
    
    # Step 3: Call QBurst LLM gateway
    response = call_gpt4o(data)
    print(response)
    if not response:
        sys.exit(1)
    
    # Step 4: Save to DOCX
    save_to_docx(response)

if __name__ == "__main__":
    main()