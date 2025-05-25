import pytest
from utils.helpers import *

class TestUAskSecurity:
    @pytest.fixture(scope="class")
    def locators(self):
        return load_locators()

    @pytest.fixture(scope="class")
    def test_data(self):
        return load_test_data()

    @pytest.mark.parametrize("xss_attempt", load_test_data()["security_tests"]["xss_attempts"])
    def test_xss_protection(self, driver, locators, test_data, xss_attempt):
        """Test for XSS vulnerabilities."""
        test_name = f"xss_{xss_attempt[:10].strip()}"
        response = send_message(driver, locators, xss_attempt)
        response_html = response.get_attribute("innerHTML").lower()

        save_screenshot(driver, test_name)

        failure_reasons = [
            f"XSS: {tag} detected"
            for tag in test_data["security_tests"]["xss_expected_strings"]
            if tag.lower() in response_html
        ]

        passed = not failure_reasons
        log_validation_result("en", xss_attempt, response_html, passed, failure_reasons)

        assert passed, f"XSS vulnerability detected: {', '.join(failure_reasons)}"

    @pytest.mark.parametrize("malicious_prompt", load_test_data()["security_tests"]["malicious_prompts"])
    def test_malicious_prompts(self, driver, malicious_prompt):
        """Test that chatbot properly rejects malicious prompt injections."""
        locators = load_locators()
        test_data = load_test_data()

        test_name = f"malicious_{malicious_prompt[:15].replace(' ', '_')}"
        response = send_message(driver, locators, malicious_prompt)
        response_text = response.text.lower()

        save_screenshot(driver, test_name)

        expected_phrases = test_data["security_tests"]["expected_rejection_phrases"]
        matched_phrases = [phrase for phrase in expected_phrases if phrase in response_text]

        passed = bool(matched_phrases)
        failure_reasons = [] if passed else ["No expected fallback phrase found in response"]

        log_validation_result("en", malicious_prompt, response_text, passed, failure_reasons)

        assert passed, f"Malicious prompt not properly rejected: {malicious_prompt}"
