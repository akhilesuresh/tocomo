#!/bin/bash

# Trap Ctrl+C to exit gracefully
trap "echo -e '\nExecution interrupted by user. Exiting...'; exit 1" SIGINT

# Loop to get valid package name and launcher activity
while true; do
    read -p "Enter the package name of the app (e.g., com.application.zomato): " PACKAGE
    LAUNCHER_ACTIVITY=$(adb shell cmd package resolve-activity --brief "$PACKAGE" | tail -n 1)

    if [[ "$LAUNCHER_ACTIVITY" == "No activity found" || -z "$LAUNCHER_ACTIVITY" ]]; then
        echo "❌ Error: No valid launcher activity found for package '$PACKAGE'. Please try again."
    else
        echo "✅ Resolved launcher activity: $LAUNCHER_ACTIVITY"
        break
    fi
done

# Prompt user to enter the output directory name (with default fallback)
# Prompt user for an empty directory
while true; do
    read -p "Enter the directory to store log files [./performance_logs]: " OUTPUT_DIR
    OUTPUT_DIR=${OUTPUT_DIR:-./performance_logs}

    # If directory doesn't exist, create it and break
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        mkdir -p "$OUTPUT_DIR"
        break
    fi

    # If directory exists but is empty, continue
    if [[ -z "$(ls -A "$OUTPUT_DIR")" ]]; then
        break
    else
        echo "❌ Error: Directory '$OUTPUT_DIR' is not empty. Please enter an empty directory."
    fi
done

# Write OUTPUT_DIR to a temporary file in the project directory
echo "$OUTPUT_DIR" > "/home/astin/Desktop/Projects/Performance metrics/output_dir.txt"

# Path to store output directory and file paths
OUTPUT_PATHS_FILE="$OUTPUT_DIR/output_paths.txt"

# Write OUTPUT_DIR to the temporary file
echo "OUTPUT_DIR:$OUTPUT_DIR" > "$OUTPUT_PATHS_FILE"

# Function to capture and save gfxinfo, meminfo, cpuinfo, diskstats, and batterystats
capture_metrics() {
    SCREEN_NAME="$1"
    echo "---- Capturing metrics for $SCREEN_NAME ----"
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Define the output file where all metrics for a screen will be stored
    OUTPUT_FILE="$OUTPUT_DIR/${SCREEN_NAME}_performance.txt"

    # Append OUTPUT_FILE to the temporary file
    echo "OUTPUT_FILE:$OUTPUT_FILE" >> "$OUTPUT_PATHS_FILE"

    # Add timestamp to the output file
    echo ">>> $TIMESTAMP" >> "$OUTPUT_FILE"

    # Clear old frame data to isolate this screen only
    adb shell dumpsys gfxinfo "$PACKAGE" reset

    # Launch the app using the resolved launcher activity
    echo "Launching the application..."
    adb shell am start -W "$LAUNCHER_ACTIVITY"

    # Allow the app to start and stabilize
    echo "Waiting for app to load completely..."
    sleep 10

    # Prompt the user to navigate to the specific screen
    echo "Navigate to the $SCREEN_NAME screen in the app."
    read -p "Press [Enter] once you are on the $SCREEN_NAME screen to capture metrics."

    # Capture gfxinfo frame statistics
    echo -e "\n---- GFXINFO for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys gfxinfo "$PACKAGE" framestats >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture memory usage statistics
    echo -e "\n---- MEMINFO for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys meminfo "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture CPU usage statistics
    echo -e "\n---- CPUINFO for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys cpuinfo | grep -i "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture disk usage statistics
    echo -e "\n---- DISKSTATS for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys diskstats | grep "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture battery statistics
    echo -e "\n---- BATTERYSTATS for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys batterystats "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    echo "✅ Done: Saved to $OUTPUT_FILE"
}

# Prompt user to enter screen names dynamically
echo "Enter the screen/transaction names one by one (type 'end' to finish):"
TRANSACTIONS=()
while true; do
    read -p "Enter screen/transaction name: " SCREEN
    if [[ "$SCREEN" == "end" ]]; then
        break
    fi
    TRANSACTIONS+=("$SCREEN")
done

# Loop through each entered screen name
for SCREEN in "${TRANSACTIONS[@]}"; do
    capture_metrics "$SCREEN"
done

echo "✅ All metrics collected for all screens."
