import logging
import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

SHORT_WAIT = 10
MEDIUM_WAIT = 20
LONG_WAIT = 30


class GmailLogin:
    """Automates Gmail login flow on Android device via Appium."""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, MEDIUM_WAIT)

    def login(self, email: str, password: str, totp_code: str) -> None:
        """Full Gmail login flow including 2FA."""
        logger.info("Starting Gmail login for %s", email)
        self._open_gmail()
        self._handle_welcome_screen()
        self._enter_email(email)
        self._enter_password(password)
        self._handle_2fa(totp_code)
        self._verify_login_success()
        logger.info("Gmail login successful for %s", email)

    def _open_gmail(self) -> None:
        """Launch Gmail app."""
        self.driver.activate_app("com.google.android.gm")
        time.sleep(3)

    def _handle_welcome_screen(self) -> None:
        """Dismiss any welcome or setup screens."""
        for res_id in [
            "com.google.android.gm:id/setup_addresses_add_another",
            "com.google.android.gm:id/action_done",
            "com.google.android.setupwizard:id/next_button",
        ]:
            try:
                el = self.driver.find_element(AppiumBy.ID, res_id)
                el.click()
                time.sleep(1)
            except NoSuchElementException:
                pass

    def _enter_email(self, email: str) -> None:
        """Enter email address on the sign-in screen."""
        # Try native Gmail add-account flow
        try:
            add_account = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.TextView[@text="Add an email address"]')
                )
            )
            add_account.click()
            time.sleep(1)
        except TimeoutException:
            pass

        # Select Google
        try:
            google_option = self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.TextView[@text="Google"]')
                )
            )
            google_option.click()
            time.sleep(2)
        except TimeoutException:
            pass

        # Enter email
        email_field = self.wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, '//android.widget.EditText[@resource-id="identifierId"]')
            )
        )
        if email_field.get_attribute("text"):
            email_field.clear()
        email_field.send_keys(email)

        # Click Next
        self._click_next()
        time.sleep(2)

    def _enter_password(self, password: str) -> None:
        """Enter password on the password screen."""
        pwd_field = self.wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, '//android.widget.EditText[@resource-id="password"]')
            )
        )
        pwd_field.clear()
        pwd_field.send_keys(password)
        self._click_next()
        time.sleep(3)

    def _handle_2fa(self, totp_code: str) -> None:
        """Handle 2FA/TOTP challenge if presented."""
        try:
            # Check for authenticator app / OTP screen
            totp_field = WebDriverWait(self.driver, SHORT_WAIT).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.EditText[@resource-id="totpPin"]')
                )
            )
            logger.info("2FA screen detected, entering TOTP code")
            totp_field.clear()
            totp_field.send_keys(totp_code)
            self._click_next()
            time.sleep(3)
        except TimeoutException:
            logger.info("No 2FA screen detected (may not be required)")

        # Handle SMS/other 2FA prompts if needed
        try:
            sms_btn = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Get a verification code")]')
                )
            )
            sms_btn.click()
            time.sleep(2)
            sms_field = WebDriverWait(self.driver, SHORT_WAIT).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, '//android.widget.EditText')
                )
            )
            sms_field.send_keys(totp_code)
            self._click_next()
        except TimeoutException:
            pass

    def _verify_login_success(self) -> None:
        """Verify we are logged into Gmail."""
        try:
            self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ID, "com.google.android.gm:id/conversation_list_view")
                )
            )
            logger.info("Gmail inbox visible - login confirmed")
        except TimeoutException:
            # Also accept the compose button as indicator
            self.wait.until(
                EC.presence_of_element_located(
                    (AppiumBy.ID, "com.google.android.gm:id/compose_button")
                )
            )

    def _click_next(self) -> None:
        """Click the Next button (various possible locators)."""
        for locator in [
            (AppiumBy.XPATH, '//android.widget.Button[@text="Next"]'),
            (AppiumBy.XPATH, '//android.widget.Button[@resource-id="identifierNext"]'),
            (AppiumBy.XPATH, '//android.widget.Button[@resource-id="passwordNext"]'),
            (AppiumBy.XPATH, '//android.widget.Button[contains(@text,"Next")]'),
        ]:
            try:
                btn = self.driver.find_element(*locator)
                btn.click()
                return
            except NoSuchElementException:
                pass
        raise RuntimeError("Could not find Next button")
