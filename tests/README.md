# ApiDemos Appium + pytest test

This project tests the uploaded `ApiDemos-debug.apk` on a **physical Android device**.

## Test scenario

1. Install and launch ApiDemos.
2. Open **Text**.
3. Open **LogTextBox**.
4. Click **Add**.
5. Verify **This is a test** is displayed.

## Prerequisites

- Python 3.9 or later.
- Java JDK compatible with your Appium installation.
- Android SDK Platform Tools (`adb`).
- Appium 2 installed and running.
- UiAutomator2 driver installed in Appium.
- A physical Android device with Developer options and USB debugging enabled.
- USB debugging authorization accepted on the device.

Install Appium and its Android driver (if not already installed):

```bash
npm install -g appium
appium driver install uiautomator2
```

Start the Appium server:

```bash
appium
```

## Project setup

Place `ApiDemos-debug.apk` in this project directory, or set `ANDROID_APP_PATH`.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Connect the physical device

Connect the phone using USB and run:

```bash
adb devices -l
```

Accept the USB debugging authorization prompt on the phone.

Copy the device serial from the output. Then set the environment variable.

Windows PowerShell:

```powershell
$env:ANDROID_UDID="YOUR_DEVICE_SERIAL"
```

macOS/Linux:

```bash
export ANDROID_UDID="YOUR_DEVICE_SERIAL"
```

If the APK is not in this project directory:

Windows PowerShell:

```powershell
$env:ANDROID_APP_PATH="C:\path\to\ApiDemos-debug.apk"
```

macOS/Linux:

```bash
export ANDROID_APP_PATH="/path/to/ApiDemos-debug.apk"
```

Optional Appium server URL:

```powershell
$env:APPIUM_SERVER_URL="http://127.0.0.1:4723"
```

## Run the test

From the project directory:

```bash
pytest
```

Run with more detailed Appium/pytest output:

```bash
pytest -vv -s
```

## Physical-device enforcement

The fixture requires `ANDROID_UDID`, verifies that the device is connected and authorized, and checks `ro.kernel.qemu` to reject typical Android emulators. If your device reports that property differently, inspect:

```bash
adb -s YOUR_DEVICE_SERIAL shell getprop ro.kernel.qemu
```

## Notes

- The test uses Android UI text selectors. If the app's UI exposes different visible labels or accessibility properties on your device, inspect the Appium page source and adjust the selectors.
- The APK is installed by the Appium session using the `app` capability.
- The test is not executed automatically on upload; run it against your connected physical device.
- The test currently verifies the requested positive flow. It does not yet include negative cases, repeated Add clicks, or performance measurements.
