from appium.webdriver.common.appiumby import AppiumBy


def find_text(driver, text):
    """Find an Android UI element by its visible text."""
    return driver.find_element(
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().text("{text}")'
    )


def sample_test(driver):

    # 2. Click on 'Text'
    find_text(driver, "Text").click()

    # 3. Click on 'LogTextBox'
    find_text(driver, "LogTextBox").click()

    # 4. Click on 'Add'
    find_text(driver, "ADD").click()
    print(driver.page_source)

    # 5. Verify 'This is a test' appears in the box
    added_text = driver.find_element(
        AppiumBy.ID, "io.appium.android.apis:id/text"
    )
    assert "This is a test" in added_text.text, (
        "'This is a test' was not displayed after clicking Add."
    )
    driver.terminate_app("io.appium.android.apis")