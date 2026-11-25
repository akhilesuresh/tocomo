import os
import subprocess
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_APK = PROJECT_ROOT / "ApiDemos-debug.apk"


def _adb(*args):
    return subprocess.run(
        ["adb", *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    ).stdout.strip()


def _is_physical_device(udid):
    # Android emulators commonly expose ro.kernel.qemu=1.
    # If the property is unavailable, fail closed rather than assume physical.
    value = _adb("-s", udid, "shell", "getprop", "ro.kernel.qemu")
    return value == "0"


@pytest.fixture(scope="session")
def device_udid():
    udid = os.getenv("ANDROID_UDID")
    if not udid:
        pytest.fail(
            "Set ANDROID_UDID to the serial of your physical Android device. "
            "Find it with: adb devices -l"
        )

    devices_output = _adb("devices")
    connected = {
        line.split()[0]: line.split()[1]
        for line in devices_output.splitlines()[1:]
        if len(line.split()) >= 2
    }

    if connected.get(udid) != "device":
        pytest.fail(
            f"Device {udid!r} is not connected and authorized. "
            "Check `adb devices -l` and accept the USB debugging prompt."
        )

    if not _is_physical_device(udid):
        pytest.fail(
            f"{udid!r} appears to be an emulator. "
            "This test is configured to require a physical device."
        )

    return udid


@pytest.fixture(scope="session")
def apk_path():
    configured = os.getenv("ANDROID_APP_PATH")
    path = Path(configured).expanduser().resolve() if configured else DEFAULT_APK

    if not path.is_file():
        pytest.fail(
            f"APK not found at {path}. Set ANDROID_APP_PATH to its location."
        )
    return str(path)


@pytest.fixture
def driver(device_udid, apk_path):
    server_url = os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723")

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = device_udid
    options.udid = device_udid
    options.app = apk_path
    options.app_package = "io.appium.android.apis"
    options.app_activity = ".ApiDemos"
    options.no_reset = False
    options.new_command_timeout = 120

    session = webdriver.Remote(server_url, options=options)
    session.implicitly_wait(5)

    yield session

    session.quit()
