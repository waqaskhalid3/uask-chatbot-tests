import pytest
import time
from selenium.webdriver.chrome.webdriver import WebDriver
from utils.helpers import *


class TestUAskUIBehavior:
    @pytest.fixture(scope="class")
    def locators(self):
        return load_locators()

    @pytest.fixture(scope="class")
    def test_data(self):
        return load_test_data()

    def test_01_widget_loads_correctly(self, driver: WebDriver, locators: EC.Any):
        widget = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["widget_container"]))
        )
        assert widget.is_displayed(), "Chat widget did not load correctly."
        

    def test_02_user_can_send_message(self, driver: WebDriver, locators: EC.Any):
        wait = WebDriverWait(driver, 10)

        # Load test message from JSON
        test_data = load_test_data()
        test_msg = test_data["ui_tests"]["test_messages"]["input_field_test"]["message"]

        # Step 1: Send message
        input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
        )
        input_box.send_keys(test_msg + Keys.ENTER)

        # Step 2: Assert loading spinner appears
        spinner = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["loading_spinner"]))
        )
        assert spinner.is_displayed(), "Loading spinner not visible — Captcha Appeared."

        # Step 3: Screenshot
        save_screenshot(driver, "user_can_send_message")
    

    def test_03_ai_response_rendered(self, driver: WebDriver, locators: EC.Any):

        # Step 1: Load English version of chat and get input box
        input_box = setup_chat(driver, locators, "en")

        # Step 2: Load test message from JSON
        test_data = load_test_data()
        test_msg = test_data["ui_tests"]["test_messages"]["input_field_test"]["message"]
        test_msg_response = test_data["ui_tests"]["test_messages"]["input_field_test"]["expected_keyword"]

        # Step 3: Send the message to the chatbot
        input_box.send_keys(test_msg + Keys.ENTER)

        # Step 4: Wait for the AI response element to appear
        ai_response = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["ai_message"]))
        )

        # Step 5: Save screenshot for visual verification
        save_screenshot(driver, "ai_response_rendered")

        # Step 6: Validate that AI response includes expected keyword
        assert test_msg_response in ai_response.text.lower(), "AI response not rendered correctly."

   
    @pytest.mark.parametrize("language_data", load_test_data()["ui_tests"]["language_direction"])
    def test_04_multilingual_support(self, driver, locators, language_data):
        """ Test: Verify chat input field respects LTR/RTL direction based on language."""
        language = language_data["language"]
        expected_direction = language_data["expected_direction"]

        wait = WebDriverWait(driver, 30)

        # Step 1: If Arabic, switch from English via language toggle
        if language == "ar":
            lang_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, locators["home_page"]["language_button"]))
            )
            lang_button.click()
            wait.until(EC.url_contains("/ar/"))

        # Step 2: Locate input field and check text direction
        input_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
        )
        actual_direction = input_box.get_attribute("dir") or input_box.value_of_css_property("direction")

        # Step 3: Screenshot & Logging
        test_name = f"multilingual_direction_{language}"
        save_screenshot(driver, test_name)

        passed = actual_direction == expected_direction
        log_validation_result(
            lang=language,
            query="N/A",
            response_text=f"Detected direction: {actual_direction}",
            passed=passed,
            failure_reasons=[f"Expected: {expected_direction}, Found: {actual_direction}"] if not passed else None
        )

        # Step 4: Assertion
        assert passed, f"[{language.upper()}] Input direction mismatch: expected '{expected_direction}', got '{actual_direction}'"



    def test_05_input_is_cleared_after_sending(self, driver, locators):
        """ Test: Verify that the input field is cleared after sending a message. """
        # Step 1: Load English version of chat and get input box
        input_box = setup_chat(driver, locators, "en")

        # Step 1: Send message

        input_box.send_keys("How to renew Emirates ID?" + Keys.ENTER)
        time.sleep(5)  # Wait for the message to be sent
        # Step 3: Wait for input field to appear on chat screen
        input_field = WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
        )

        # Step 4: Take screenshot for verification
        save_screenshot(driver, "input_is_cleared_after_sending")

        # Step 5: Assert the input field is empty
        input_value = input_field.text.strip()
        assert input_value == "", "Input field is not cleared after clicking a question card."


    def test_06_scroll_and_accessibility(self, driver, locators):
        """
        Test: Ensure chat scroll works and input field is accessible (aria-label present).
        """

        wait = WebDriverWait(driver, 30)

        # Step 1: Load English chat widget and locate the input box
        input_box = setup_chat(driver, locators, "en")

        # Step 2: Send a message to generate AI response
        test_msg = "How to renew Emirates ID?"
        input_box.send_keys(test_msg + Keys.ENTER)
        time.sleep(10)  # Let AI response render 

        # Step 3: Locate the scrollable message container
        container = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["message_container"]))
        )

        # Step 4: Scroll to the top of the container
        driver.execute_script("arguments[0].scrollTop = 0", container)
        time.sleep(1)  # Let it settle

        # Step 5: Capture current scroll position
        scroll_position = driver.execute_script("return arguments[0].scrollTop", container)
        assert scroll_position == 0, "Scroll to top did not work properly in chat message container."

        # Step 6: Save screenshot to verify top messages are visible
        save_screenshot(driver, "scrolled_to_top")

    def test_07_accessibility_input_field(self, driver: WebDriver, locators: EC.Any):
        """
        Test: Verify that the chatbot input field includes a valid aria-label for accessibility.
        """
        wait = WebDriverWait(driver, 15)
        # Step 2: Wait for the chat input field to be present
        input_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
        )

        # Step 3: Validate accessibility using aria-label
        aria_label = input_element.get_attribute("aria-label") or "None"
        placeholder = input_element.get_attribute("placeholder") or "None"
        role = input_element.get_attribute("role") or "None"
        name_attr = input_element.get_attribute("name") or "None"
        id_attr = input_element.get_attribute("id") or "None"
        input_type = input_element.get_attribute("type") or "None"

        all_attrs = (
            f"aria-label: {aria_label}\n"
            f"placeholder: {placeholder}\n"
            f"role: {role}\n"
            f"name: {name_attr}\n"
            f"id: {id_attr}\n"
            f"type: {input_type}"
        )

        # Assertion
        passed = bool(aria_label.strip() and aria_label != "None")
        failure_reason = [] if passed else ["Missing or empty aria-label"]

        # Log accessibility validation result
        log_validation_result(
            lang="lang",
            query="Accessibility Check (aria-label)",
            response_text=all_attrs,
            passed=passed,
            failure_reasons=failure_reason
        )

        assert passed, "Input field is missing a valid aria-label."
