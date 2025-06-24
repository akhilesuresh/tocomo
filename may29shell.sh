#!/bin/bash

# Prompt the user if multiple devices are connected or error out if none
DEVICE_COUNT=$(adb devices | grep -w "device" | wc -l)
if [[ $DEVICE_COUNT -eq 0 ]]; then
    echo "❌ No Android device connected. Please connect a device and try again."
    exit 1
elif [[ $DEVICE_COUNT -gt 1 ]]; then
    echo "⚠️ Multiple devices detected. Please connect only one or specify device ID explicitly."
    adb devices
    exit 1
else
    DEVICE_ID=$(adb devices | grep -w "device" | awk 'NR==1 {print $1}')
    echo "✅ Using connected device: $DEVICE_ID"
fi

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

# Function to capture and save gfxinfo, meminfo, cpuinfo, diskstats, batterystats, and FPS
capture_metrics() {
    SCREEN_NAME="$1"
    echo "---- Capturing metrics for $SCREEN_NAME ----"
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    OUTPUT_FILE="$OUTPUT_DIR/${SCREEN_NAME}_performance.txt"

    # Write timestamp and device ID
    {
        echo ">>> Timestamp: $TIMESTAMP"
        echo ">>> Device ID: $DEVICE_ID"
        echo ">>> Package: $PACKAGE"
        echo ">>> Screen: $SCREEN_NAME"
        echo ""
    } >> "$OUTPUT_FILE"

    # Reset gfxinfo and SurfaceFlinger latency
    adb shell dumpsys gfxinfo "$PACKAGE" reset
    adb shell dumpsys SurfaceFlinger --latency-clear "$LAUNCHER_ACTIVITY"

    # Launch the app
    echo -e "\n---- Launching the application ----" >> "$OUTPUT_FILE"
    adb shell am start -W "$LAUNCHER_ACTIVITY" >> "$OUTPUT_FILE" 2>&1


    echo "Waiting for app to load completely..."
    sleep 10

    echo "Navigate to the $SCREEN_NAME screen in the app."
    read -p "Press [Enter] once you are on the $SCREEN_NAME screen to capture metrics."

    # Capture GFXINFO
    echo -e "\n---- GFXINFO for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys gfxinfo "$PACKAGE" framestats >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture MEMINFO
    echo -e "\n---- MEMINFO for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys meminfo "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture CPUINFO
    echo -e "\n---- CPUINFO for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys cpuinfo | grep -i "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture DISKSTATS
    echo -e "\n---- DISKSTATS for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys diskstats | grep "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture BATTERYSTATS
    echo -e "\n---- BATTERYSTATS for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    adb shell dumpsys batterystats "$PACKAGE" >> "$OUTPUT_FILE"
    echo -e "\n\n" >> "$OUTPUT_FILE"

    # Capture FPS data
     echo "Now collecting FPS data — interact with the app for 10 seconds..."
    sleep 10

    echo -e "\n---- FPS (SurfaceFlinger) Latency Data for $SCREEN_NAME ----" >> "$OUTPUT_FILE"
    FPS_DATA=$(adb shell dumpsys SurfaceFlinger --latency "$PACKAGE")
    echo "$FPS_DATA" >> "$OUTPUT_FILE"

    # Calculate average FPS if frame data is available
    FRAME_LINES=$(echo "$FPS_DATA" | tail -n +2 | grep -v '^0$' | wc -l)

    if [[ $FRAME_LINES -gt 0 ]]; then
        AVERAGE_FPS=$(echo "$FPS_DATA" | tail -n +2 | awk 'NF==3 && $1 > 0 && $2 > $1 { print 1e9 / ($2 - $1) }' | awk '{sum+=$1; count++} END {if(count>0) print int(sum/count); else print "N/A"}')
        echo -e "\nCalculated Average FPS: $AVERAGE_FPS\n" >> "$OUTPUT_FILE"
    else
        echo -e "\n⚠️ Not enough frame data available to calculate FPS.\n" >> "$OUTPUT_FILE"
    fi

    echo "✅ Done: Metrics saved to $OUTPUT_FILE"
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

