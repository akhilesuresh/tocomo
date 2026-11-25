#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import re
from dotenv import load_dotenv
from openai import OpenAI

# Load env
load_dotenv(dotenv_path="APIkey.env")
API_KEY = os.getenv("API_KEY")

# Paths (keep these as you had them)
SHELL_SCRIPT_PATH = "C:\\Users\Akhil\PycharmProjects\\tocomo\may29shell.sh"
DEFAULT_OUTPUT_PATHS_FILE = "C:\\Users\Akhil\PycharmProjects\\tocomo\\newfile\output_path.txt"
ANALYSIS_DIR = "C:\\Users\Akhil\PycharmProjects\\tocomo\Analysis_Reports"

# safety: where files will be written
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# Initialize client
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://llmgateway.qburst.build/v1"
    )
except Exception as e:
    print(f"Error: Could not initialize QBurst LLM gateway client. Ensure API_KEY is valid. {e}")
    sys.exit(1)


def sanitize_filename(name: str) -> str:
    """Make a filesystem-safe filename from screen/transaction name."""
    name = name.strip()
    # replace spaces with underscores and remove unsafe chars
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^A-Za-z0-9_\-\.]', '', name)
    # fallback
    return name[:200] if name else "screen_report"


def run_shell_script(timeout: int = 60):
    """
    Run the shell script interactively and wait for output_paths.txt to appear.
    On success sets global OUTPUT_FILE_PATHS to a list of output files.
    """
    print("Running shell script. Waiting for user to enter package name, output directory, screen names, and navigate screens...")
    try:
        subprocess.run([SHELL_SCRIPT_PATH], check=True)
        print("Shell script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running shell script: {e}")
        return False
    except FileNotFoundError:
        print(f"Shell script not found at {SHELL_SCRIPT_PATH}")
        return False

    # Wait for output_paths.txt to appear
    output_paths_file = DEFAULT_OUTPUT_PATHS_FILE
    elapsed = 0
    check_interval = 5
    print(f"Waiting for output_paths.txt to appear at {output_paths_file} (timeout {timeout}s)...")
    while not os.path.exists(output_paths_file) and elapsed < timeout:
        time.sleep(check_interval)
        elapsed += check_interval
        print(f"Still waiting... ({elapsed}/{timeout} seconds elapsed)")

    if not os.path.exists(output_paths_file):
        print(f"Error: Output paths file not found at {output_paths_file} after {timeout} seconds.")
        return False

    # Read output_paths.txt to get OUTPUT_DIR and output files
    output_files = []
    output_dir = None
    try:
        with open(output_paths_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("OUTPUT_DIR:"):
                    output_dir = line[len("OUTPUT_DIR:"):].strip()
                    # if output dir provided, update path to the file inside that dir
                    possible = os.path.join(output_dir, "output_paths.txt")
                    if os.path.exists(possible):
                        output_paths_file = possible
                elif line.startswith("OUTPUT_FILE:"):
                    output_file = line[len("OUTPUT_FILE:"):].strip()
                    if os.path.isfile(output_file):
                        output_files.append(output_file)
    except Exception as e:
        print(f"Error reading {output_paths_file}: {e}")
        return False

    if not output_files:
        print("No valid output files found in output_paths.txt")
        return False

    global OUTPUT_FILE_PATHS
    OUTPUT_FILE_PATHS = output_files
    print(f"Output files found: {', '.join(OUTPUT_FILE_PATHS)}")
    return True


def read_output_files():
    """
    Read the contents of each output file and return a list of dicts:
    [{'screen_name':..., 'content':...}, ...]
    Keeps the original format of your content but separates by file/screen.
    """
    screens = []
    for output_file in OUTPUT_FILE_PATHS:
        if not os.path.exists(output_file):
            print(f"Output file not found at {output_file} — skipping")
            continue
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                screen_name = os.path.basename(output_file).replace("_performance.txt", "")
                screens.append({
                    "screen_name": screen_name,
                    "content": f"Metrics for screen '{screen_name}':\n{content}\n{'='*80}\n"
                })
        except Exception as e:
            print(f"Error reading output file {output_file}: {e}")
    if not screens:
        print("No data read from output files")
        return None
    return screens


def call_gpt4o(data: str, screen_name: str):
    """
    Send data and screen_name to the LLM and return the generated markdown string.
    Keeps your original prompt instructions but requests a markdown file per screen.
    """
    prompt = f"""
Analyze the following Android performance metrics data for an app, captured from gfxinfo, meminfo, cpuinfo, diskstats, and batterystats across multiple screens/transactions. The data is organized by screen, with this batch containing metrics for the screen/transaction: **{screen_name}**.

{data}

Read the given performance text and analyze the results of the adb commands. Generate a structured **markdown-formatted report** suitable for saving as a `.md` file.

**Important Formatting Instruction:** All markdown tables must have a consistent structure, with each column width sized to fit the largest text (including headers) so that the table does not exceed standard A4 page margins when converted. Avoid unnecessary text wrapping or overly long column names that could cause overflow.

---

# {screen_name} Performance Report

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

Include the following metric groups, using **standard markdown tables**. The **Status** column should show PASS or FAIL based on known thresholds or general best practices.

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
            max_tokens=10000
        )
        # Depending on the client library version the structure may differ;
        # this matches the structure you used earlier.
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling QBurst LLM gateway for screen {screen_name}: {e}")
        return None


def save_to_md(response_text: str, screen_name: str):
    """
    Save the markdown response to a per-screen file inside ANALYSIS_DIR.
    File name pattern: <sanitized_screen_name>_performance_report.md
    """
    sanitized = sanitize_filename(screen_name)
    filename = f"{sanitized}_performance_report.md"
    path = os.path.join(ANALYSIS_DIR, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(response_text)
        print(f"✅ Analysis for '{screen_name}' saved to {path}")
    except Exception as e:
        print(f"❌ Error saving markdown for '{screen_name}': {e}")


def main():
    # 1) Run shell script (interactive)
    if not run_shell_script():
        sys.exit(1)

    # 2) Read per-screen files
    screens = read_output_files()
    if not screens:
        sys.exit(1)

    # 3) For each screen, call GPT and save a separate markdown file
    for idx, s in enumerate(screens, start=1):
        screen_name = s['screen_name']
        content = s['content']
        print(f"\n---- Processing ({idx}/{len(screens)}) screen: {screen_name} ----")
        response = call_gpt4o(content, screen_name)
        if not response:
            print(f"Skipping save for '{screen_name}' due to LLM error.")
            continue
        save_to_md(response, screen_name)

        # Small pause to avoid hammering the LLM/gateway if many screens
        time.sleep(1)

    print("\nAnalysis completed for all transactions.")


if __name__ == "__main__":
    main()
