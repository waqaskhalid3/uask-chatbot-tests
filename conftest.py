import json
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# Load locators from JSON
with open("data/locators.json") as f:
    locators = json.load(f)

@pytest.fixture(scope="function")
def driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://ask.u.ae/en/")

    wait = WebDriverWait(driver, 10)

    # Accept disclaimer
    try:
        accept_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, locators["home_page"]["accept_button"]))
        )
        accept_button.click()
    except Exception as e:
        print("Disclaimer button not found or already accepted:", e)

    # Wait for the chat widget or input box to be ready
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, locators["home_page"]["chat_input_box"]))
    )

    yield driver
    driver.quit()