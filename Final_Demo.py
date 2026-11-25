import subprocess
import os
from openai import OpenAI
import sys
from dotenv import load_dotenv
import time
import pypandoc

# Load API key
load_dotenv(dotenv_path="APIkey.env")
API_KEY = os.getenv("API_KEY")

# Paths
SHELL_SCRIPT_PATH = "C:\\Users\Akhil\PycharmProjects\\tocomo\may29shell.sh"
DEFAULT_OUTPUT_PATHS_FILE = "C:\\Users\Akhil\PycharmProjects\\tocomo\\newfile\output_path.txt"
ANALYSIS_DIR = "C:\\Users\Akhil\PycharmProjects\\tocomo\Analysis_Reports"

# Initialize client
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://llmgateway.qburst.build/v1"
    )
except Exception as e:
    print(f"Error: Could not initialize QBurst LLM gateway client. Ensure API_KEY is valid. {e}")
    sys.exit(1)


def run_shell_script():
    """Run shell script and wait for output_paths.txt."""
    print("Running shell script...")
    try:
        subprocess.run([SHELL_SCRIPT_PATH], check=True)
        print("Shell script executed successfully.")

        global OUTPUT_PATHS_FILE
        OUTPUT_PATHS_FILE = DEFAULT_OUTPUT_PATHS_FILE
        timeout = 60
        check_interval = 5
        elapsed = 0

        print(f"Waiting for output_paths.txt at {OUTPUT_PATHS_FILE}...")
        while not os.path.exists(OUTPUT_PATHS_FILE) and elapsed < timeout:
            time.sleep(check_interval)
            elapsed += check_interval
            print(f"Still waiting... ({elapsed}/{timeout}s elapsed)")

        if not os.path.exists(OUTPUT_PATHS_FILE):
            print(f"❌ output_paths.txt not found after {timeout}s.")
            return False

        # Read all output file paths
        output_files = []
        with open(OUTPUT_PATHS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("OUTPUT_FILE:"):
                    output_file = line[len("OUTPUT_FILE:"):]
                    if os.path.isfile(output_file):
                        output_files.append(output_file)

        if not output_files:
            print("❌ No valid output files found in output_paths.txt")
            return False

        global OUTPUT_FILE_PATHS
        OUTPUT_FILE_PATHS = output_files
        print(f"✅ Output files found: {', '.join(OUTPUT_FILE_PATHS)}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running shell script: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Shell script not found at {SHELL_SCRIPT_PATH}")
        return False


def read_output_file(file_path):
    """Read the content of a single output file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            transaction_name = os.path.basename(file_path).replace("_performance.txt", "")
            return transaction_name, content
    except Exception as e:
        print(f"❌ Error reading output file {file_path}: {e}")
        return None, None


def call_gpt4o(transaction_name, metrics_data):
    """Send data to GPT-4o-mini model and get analysis."""
    prompt = f"""
Analyze the following Android performance metrics for transaction: {transaction_name}

{metrics_data}

Read the given performance text and analyze the results of the adb commands. Generate a structured **markdown-formatted report** for use in a DOCX export.
**Important Formatting Instruction:** All markdown tables must have a consistent structure, with each column width sized to fit the largest text (including headers) so that the table does not exceed standard A4 DOCX page margins. Avoid unnecessary text wrapping or overly long column names that could cause overflow.

Follow this structure:
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
|Screen   |{transaction_name}|
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
---
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert Android performance analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=5000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        return None


def save_to_docx(transaction_name, response_text):
    """Save analysis as DOCX file."""
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    docx_path = os.path.join(ANALYSIS_DIR, f"Final_Report_{transaction_name}.docx")

    try:
        pypandoc.convert_text(
            response_text,
            to='docx',
            format='md',
            outputfile=docx_path
        )
        print(f"✅ Report saved: {docx_path}")
    except Exception as e:
        print(f"❌ Error saving DOCX for {transaction_name}: {e}")


def main():
    if not run_shell_script():
        sys.exit(1)

    for file_path in OUTPUT_FILE_PATHS:
        transaction_name, metrics_data = read_output_file(file_path)
        if not metrics_data:
            continue

        response = call_gpt4o(transaction_name, metrics_data)
        if not response:
            continue

        save_to_docx(transaction_name, response)


if __name__ == "__main__":
    main()
