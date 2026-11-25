import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv(dotenv_path="APIkey.env")
API_KEY = os.getenv("API_KEY")

# File paths
INPUT_FILE = "/home/astin/Desktop/Projects/Performance metrics/meminfo.txt"
OUTPUT_FILE = "C:\\Users\Akhil\PycharmProjects\\tocomo\meminfo.txt"

# Initialize client
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://llmgateway.qburst.build/v1"
    )
except Exception as e:
    print(f"❌ Error: Could not initialize QBurst LLM gateway client. {e}")
    sys.exit(1)

def read_raw_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_output_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def call_gpt4o(raw_metrics: str):
    """Send data + parsing instructions to GPT-4o-mini model and get formatted Influx lines."""
    prompt = f"""
You are a data structuring assistant.
I will provide you with raw performance metrics collected from an Android device for different app transactions (like launch the application, add to cart, etc.).
The metrics may include sections such as:

Applications Memory Usage (App Summary, Objects, SQL, Databases, etc.)

Your task is to:

Parse and separate each transaction block (identified by lines like ===== launch the application (timestamp) =====).

For each block, extract sub-metrics (e.g. App Summary, Objects, SQL, DATABASES, etc.).

Convert all extracted values into InfluxDB line protocol format as shown below:

<measurement>,transaction=<transaction_name>,submetric=<section_name> <field1>=<value1>,<field2>=<value2> <timestamp>


Example:

meminfo,transaction=launch,submetric=App_Summary java_heap_pss_kb=51684,native_heap_pss_kb=99960,total_pss_kb=465237,total_rss_kb=565380,total_swap_pss_kb=58459 1730675107
meminfo,transaction=launch,submetric=Objects views=1554,activities=1,assets=53,local_binders=163,proxy_binders=94,parcel_memory_kb=254,parcel_count=623,death_recipients=15,openssl_sockets=11,webviews=4 1730675107
meminfo,transaction=launch,submetric=SQL memory_used=3137,pagecache_overflow=1159,malloc_size=183 1730675107


Normalize all field names:

Use lowercase and underscores (e.g., Java Heap → java_heap_pss_kb)

Remove units and keep numbers only where possible.

Include a Unix timestamp in seconds (you can derive from the date/time in parentheses after the transaction name, if available).

Output only the parsed and cleaned InfluxDB lines — no explanations or summaries.

Example Input:

📄 Memory Metrics for com.application.zomato (Device: b356dc0d)
===== launch the application (2025-09-23 11:25:07) =====
Applications Memory Usage (in Kilobytes):
...


Expected Output:

meminfo,transaction=launch_the_application,submetric=App_Summary java_heap_pss_kb=51684,native_heap_pss_kb=99960,code_pss_kb=67732,stack_pss_kb=5472,graphics_pss_kb=134280,private_other_pss_kb=16036,system_pss_kb=90073,total_pss_kb=465237,total_rss_kb=565380,total_swap_pss_kb=58459 1758687307
meminfo,transaction=launch_the_application,submetric=Objects views=1554,appcontexts=29,activities=1,assets=53,local_binders=163,proxy_binders=94,parcel_memory_kb=254,parcel_count=623,death_recipients=15,openssl_sockets=11,webviews=4 1758687307
meminfo,transaction=launch_the_application,submetric=SQL memory_used=3137,pagecache_overflow=1159,malloc_size=183 1758687307


If multiple transactions exist in one file, output lines for all transactions in sequence.

Here is the raw data:
------------------------
{raw_metrics}
------------------------
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert Android performance analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        return None

def main():
    print("📥 Reading raw ADB metrics file...")
    raw_metrics = read_raw_file(INPUT_FILE)

    print("🤖 Sending data to ChatGPT API for parsing and formatting...")
    formatted_output = call_gpt4o(raw_metrics)

    if not formatted_output:
        print("❌ No output received from API.")
        sys.exit(1)

    print("💾 Saving formatted data to output file...")
    write_output_file(OUTPUT_FILE, formatted_output)

    print(f"✅ Done! Formatted InfluxDB lines saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
