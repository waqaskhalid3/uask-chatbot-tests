import json
import os
import html
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException




def load_locators():
    with open(os.path.join(os.path.dirname(__file__), '../data/locators.json')) as f:
        return json.load(f)

def load_test_data():
    with open(os.path.join(os.path.dirname(__file__), '../data/test-data.json')) as f:
        return json.load(f)
    
def save_screenshot(driver, test_name):
    """Save a screenshot of the current page and log message input"""
    folder = "screenshots"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = os.path.join(folder, f"{test_name}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)


def log_validation_result(lang, query, response_text, passed, failure_reasons=None):
    """Log validation details with UTF-8 support and full AI response"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "PASS" if passed else "FAIL"

    log_entry = (
        f"\n{'-'*60}\n"
        f"Timestamp       : {timestamp}\n"
        f"Language        : {lang.upper()}\n"
        f"Query           : {html.escape(query[:200])}\n"
        f"Status          : {status}\n"
        f"AI Full Response:\n{html.escape(response_text)}\n"
    )

    if not passed:
        log_entry += (
            f"Failure Reasons : {', '.join(failure_reasons)}\n"
        )

    os.makedirs("logs", exist_ok=True)

    # Write to both console and file
    print(log_entry)
    with open("logs/validation.log", "a", encoding="utf-8") as f:
        f.write(log_entry)


def setup_chat(driver, locators, language):
    """Set up the chat widget and switch language if needed"""
    if language == "ar":
        lang_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, locators["home_page"]["language_button"]))
        )
        lang_button.click()

    return WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
    )


def send_message(driver, locators, message: str):
    """Send a message to the chatbot and return the AI response element, with error handling."""
    try:
        input_box = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
        )
        input_box.send_keys(message + Keys.ENTER)
    except TimeoutException:
        save_screenshot(driver, "input_field_timeout")
        raise AssertionError("Timeout: Chat input field not found or clickable.")
    except WebDriverException as e:
        save_screenshot(driver, "input_field_error")
        raise AssertionError(f"WebDriverException during input field interaction: {e}")

    try:
        WebDriverWait(driver, 60).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, locators["chat_widget"]["ai_message"])
        )
        return driver.find_element(By.CSS_SELECTOR, locators["chat_widget"]["ai_message"])
    except TimeoutException:
        save_screenshot(driver, "ai_response_timeout")
        raise AssertionError("Timeout: AI response not received.")
