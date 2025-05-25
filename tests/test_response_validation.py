import pytest
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.helpers import *

class TestUAskMultilingual:
    @pytest.fixture(scope="class")
    def locators(self):
        return load_locators()

    @pytest.fixture(scope="class")
    def test_data(self):
        return load_test_data()
    
    @pytest.fixture(autouse=True)
    def setup(self, driver, locators):
        """Use existing driver state from conftest"""
        self.driver = driver
        self.locators = locators
        self.wait = WebDriverWait(driver, 20)

    
    def send_english_query(self, driver, locators, query, input_field):
        """Improved version that can accept pre-found input field"""
        if input_field is None:
            input_field = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
            )
        #input_field.clear()
        input_field.send_keys(query + Keys.ENTER)
        return self.get_ai_response(driver, locators,query, "en")

    def send_arabic_query(self, driver, locators, query):
        """Handle Arabic query submission with special handling"""
        input_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, locators["chat_widget"]["input_field"]))
        )
        driver.execute_script("arguments[0].value = '';", input_field)
        time.sleep(0.5)
        
        actions = ActionChains(driver)
        actions.move_to_element(input_field).click()
        for char in query:
            actions.send_keys(char)
            time.sleep(0.1)
        actions.perform()
        time.sleep(0.5)
        input_field.send_keys(Keys.ENTER)
        return self.get_ai_response(driver, locators, query, "ar")

    def get_ai_response(self, driver, locators, query, lang):
        """Wait for AI response using appropriate locator based on language"""
        selector_key = "ai_message_rtl" if lang == "ar" else "ai_message"

        ai_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"][selector_key]))
        )
        
        # Save screenshot immediately after response appears
        safe_query = query.replace(" ", "_").replace("؟", "").replace("?", "")
        test_name = f"ai_response_{lang}_{safe_query}"
        save_screenshot(driver, test_name)
        
        return ai_element

    def validate_response(self, response, lang, expected_keywords, query=""):
        """Validate response content with logging"""
        response_text = response.text.strip()
        validation_passed = True
        failure_reasons = []
        
        try:
            assert len(response_text) > 20, "Response too short"
            assert not response_text.endswith("..."), "Incomplete response"
            #assert not any(tag in response_text for tag in ["<div", "<script", "</"]), "Broken HTML"
            
            if lang == "en":
                normalized_text = response_text.lower()
                for keyword in expected_keywords:
                    if keyword.lower() not in normalized_text:
                        failure_reasons.append(f"Missing English keyword: {keyword}")
                        validation_passed = False

            elif lang == "ar":
                for keyword in expected_keywords:
                    if keyword not in response_text:
                        failure_reasons.append(f"Missing Arabic keyword: {keyword}")
                        validation_passed = False
                if not any(char in response_text for char in ["ء", "آ", "أ"]):
                    failure_reasons.append("No characteristic Arabic letters found")
                    validation_passed = False

            log_validation_result(
                lang=lang,
                query=query,
                response_text=response_text,
                passed=validation_passed,
                failure_reasons=failure_reasons if not validation_passed else None
            )

            if not validation_passed:
                raise AssertionError(f"Validation failed: {', '.join(failure_reasons)}")

        except Exception as e:
            log_validation_result(
                lang=lang,
                query=query,
                response_text=response_text,
                passed=False,
                failure_reasons=[str(e)]
            )
            raise


   
    @pytest.mark.parametrize("query_data", load_test_data()["response_validation"]["common_queries"])
    def test_english_queries(self, driver, locators, query_data):
        """Test English queries using existing session from conftest"""
        input_field = setup_chat(driver, locators, "en")
        
        query = query_data["en"]  #Extract query
        response = self.send_english_query(driver, locators, query, input_field)
        
        #Pass the query to the validation method
        self.validate_response(response, "en", query_data["expected_keywords"]["en"], query=query)


    @pytest.mark.parametrize("query_data", load_test_data()["response_validation"]["common_queries"])
    def test_arabic_queries(self, driver, locators, query_data):
        """Test Arabic queries using existing session from conftest"""
        driver.get("https://ask.u.ae/ar/")
        wait = WebDriverWait(driver, 10)

        accept_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, locators["home_page"]["accept_button"]))
        )
        accept_button.click()

        query = query_data["ar"]  #Extract Arabic query
        response = self.send_arabic_query(driver, locators, query)
        
        #Pass query into validation
        self.validate_response(response, "ar", query_data["expected_keywords"]["ar"], query=query)



    def test_error_handling(self, driver: WebDriver, locators: EC.Any):
        """Test chatbot's fallback error messages and persistent loading indicator on network failure"""

        input_field = setup_chat(driver, locators, "en")
        
        # 1. Simulate network failure (dev tools or offline mode already toggled)
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": True,
            "latency": 0,
            "downloadThroughput": 0,
            "uploadThroughput": 0
        })

        # 2. Test empty input fallback
        driver.find_element(By.CSS_SELECTOR, locators["chat_widget"]["send_button"]).click()

        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["error_message"]))
        )
        assert any(phrase in error_message.text.lower() for phrase in ["message", "cannot", "empty"]), \
            "Expected fallback message not shown for empty input"

        save_screenshot(driver, "empty_input_error")
        driver.find_element(By.CSS_SELECTOR, locators["chat_widget"]["ok_button"]).click()


        # 3. Send a valid message while offline
        input_field.send_keys("test network failure")
        driver.find_element(By.CSS_SELECTOR, locators["chat_widget"]["send_button"]).click()

        # 4. Wait for loading state
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["loading_spinner"]))
            )
        except TimeoutException:
            raise AssertionError("Expected loading spinner not visible after sending message offline")

        # 5. Wait 30s and ensure it's still loading (no AI message received)
        try:
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, locators["chat_widget"]["loading_spinner"]))
            )
            raise AssertionError("Loading state disappeared — fallback may not have triggered as expected")
        except TimeoutException:
            # This is the expected path — still stuck in loading
            pass

        save_screenshot(driver, "persistent_loading_due_to_network_failure")

        # 6. Optionally check that fallback message is shown (if chatbot does that)
        try:
            fallback = driver.find_element(By.CSS_SELECTOR, locators["chat_widget"]["ai_message"])
            assert "sorry" in fallback.text.lower() and "try again" in fallback.text.lower(), \
                "Expected fallback message not shown after persistent loading"
        except NoSuchElementException:
            # Still in loading — acceptable as long as AI response didn't come through
            pass