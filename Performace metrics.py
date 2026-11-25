import subprocess
import os
from docx import Document
from openai import OpenAI
import sys
from dotenv import load_dotenv
import time
import pypandoc

load_dotenv(dotenv_path="APIkey.env")
API_KEY = os.getenv("API_KEY")

# Paths
SHELL_SCRIPT_PATH = "C:\\Users\Akhil\PycharmProjects\\tocomo\may29shell.sh"
DEFAULT_OUTPUT_PATHS_FILE = "C:\\Users\Akhil\PycharmProjects\\tocomo\\newfile\output_path.txt"
ANALYSIS_DIR = "C:\\Users\Akhil\PycharmProjects\\tocomo\Analysis_Reports"
DOCX_OUTPUT_PATH = os.path.join(ANALYSIS_DIR, "final_report.docx")

try:
#print("The API key is ", API_KEY)
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
        timeout = 60 # 2 minutes timeout
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
Analyze the following Android performance metrics data for an app, captured from `gfxinfo`, `meminfo`, `cpuinfo`, `diskstats`, and `batterystats` across multiple screens/transactions. The data is organized by screen, with each section labeled 'Metrics for screen <screen_name>'.

{data}

Read the given performance text and analyze the results of the adb commands. Generate a structured **markdown-formatted report** for use in a DOCX export.

**Important:** Ensure that all markdown tables maintain a consistent column structure, column headers align with data cells, and column widths are optimized so they fit within standard DOCX page margins without manual adjustment.

---

# <Package> Performance Report

## 1. Introduction

Provide a formal introduction to the document, describing its purpose and scope.

## 2. Assumptions

Mention that environmental factors such as network latency, hardware performance, background processes, and OS-level activity may influence metrics observed during this test.

## 3. App Info

Extract and display the following app-level metadata in a markdown table:

|**Field**|**Value**|
|---------|---------|
|Timestamp|f(x)     |
|Device ID|f(x)     |
|Package  |f(x)     |
|Screen   |f(x)     |
---

## 4. Metrics Tables

Include the following metric groups, using **standard markdown tables**. The **Status** column should show `PASS` or `FAIL` based on known thresholds or general best practices.

### 4.1 Frame Rendering Metrics

|**Metric**                    |**Value**|**Status**|
|------------------------------|---------|----------|
|Total frames rendered         | f(x)    |PASS/FAIL |
|Janky frames                  | f(x)    |PASS/FAIL |
|Janky frames (legacy)         | f(x)    |PASS/FAIL |
|50th percentile frame time    | f(x)    |PASS/FAIL |
|90th percentile frame time    | f(x)    |PASS/FAIL |
|95th percentile frame time    | f(x)    |PASS/FAIL |
|99th percentile frame time    | f(x)    |PASS/FAIL |
|Frame deadline missed         | f(x)    |PASS/FAIL |
|Frame deadline missed (legacy)| f(x)    |PASS/FAIL |

### 4.2 UI Performance Bottlenecks

|**Metric**             | **Value**|**Status**|
|-----------------------|----------|----------|
|Missed Vsync           | f(x)     |PASS/FAIL |
|High input latency     | f(x)     |PASS/FAIL |
|Slow UI thread         | f(x)     |PASS/FAIL |
|Slow bitmap uploads    | f(x)     |PASS/FAIL |
|Slow issue draw commands | f(x)   |PASS/FAIL |

### 4.3 GPU Metrics

|**Metric**                    |**Value**|**Status**|
|------------------------------|---------|----------|
|50th percentile GPU frame time|f(x)     |PASS/FAIL |
|90th percentile GPU frame time|f(x)     |PASS/FAIL |
|95th percentile GPU frame time|f(x)     |PASS/FAIL |
|99th percentile GPU frame time|f(x)     |PASS/FAIL |

### 4.4 CPU Memory Usage

| **Metric**                       | **Value** | **Status** |
|----------------------------------|-----------|------------|
| Glyph Cache Glyph Count Total CPU| f(x)      | PASS/FAIL  |
| MemoryMemory Usage (RSS)         | f(x)      | PASS/FAIL  |
| MemoryMemory Usage (PSS)         | f(x)      | PASS/FAIL  |

### 4.5 Memory Usage

| **Metric**     | **Value (PSS)**  | **Value (RSS)**  | **Status** |
|----------------|------------------|------------------|------------|
| Java Heap      | f(x)             | f(x)             | PASS/FAIL  |
| Native Heap    | f(x)             | f(x)             | PASS/FAIL  |
| Code           | f(x)             | f(x)             | PASS/FAIL  |
| Stack          | f(x)             | f(x)             | PASS/FAIL  |
| Graphics       | f(x)             | f(x)             | PASS/FAIL  |
| Private        | f(x)             | f(x)             | PASS/FAIL  |
| System         | f(x)             | f(x)             | PASS/FAIL  |

### 4.6 GPU Memory Usage

| **Metric**     | **Value** | **Status** |
|----------------|-----------|------------|
| Texture (Image)| f(x)      | PASS/FAIL  |
| RenderTarget   | f(x)      | PASS/FAIL  |
| Stencil        | f(x)      | PASS/FAIL  |
| Other (Total)  | f(x)      | PASS/FAIL  |

---

## 5. Test Results

Summarize how the app performed across different screens and transactions. Highlight:

- Which metrics failed to meet optimal thresholds
- Which screens were most impacted
- Recommendations for improvement based on findings
---    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
    """Convert markdown response to DOCX using Pandoc, then auto-fit tables."""
    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    try:
        # Step 1: Convert markdown to .docx with Pandoc
        pypandoc.convert_text(
            response_text,
            to='docx',
            format='md',
            outputfile=DOCX_OUTPUT_PATH,
            extra_args=['--standalone']
        )

        # Step 2: Auto-fit all tables in the generated DOCX
        doc = Document(DOCX_OUTPUT_PATH)
        for table in doc.tables:
            table.autofit = True
            for row in table.rows:
                for cell in row.cells:
                    cell.width = None  # Let Word auto-size
        doc.save(DOCX_OUTPUT_PATH)

        print(f"✅ Analysis saved to {DOCX_OUTPUT_PATH} with auto-fit tables")
    except Exception as e:
        print(f"❌ Error saving DOCX file using Pandoc: {e}")

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
    #print(response)
    if not response:
        sys.exit(1)
    
    # Step 4: Save to DOCX
    save_to_docx(response)

if __name__ == "__main__":
    main()