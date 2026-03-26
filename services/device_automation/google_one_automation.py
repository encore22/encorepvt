import logging
import re
import time
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

GOOGLE_ONE_PACKAGE = "com.google.android.apps.subscriptions.red"
OFFER_LINK_PREFIX = "https://one.google.com/partner-eft-onboard/"
SHORT_WAIT = 10
LONG_WAIT = 30


class GoogleOneAutomation:
    """Automates Google One app to retrieve Gemini Pro offer link."""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, LONG_WAIT)

    def get_offer_link(self) -> str:
        """Open Google One and extract the Gemini Pro offer link."""
        logger.info("Opening Google One app")
        self._open_google_one()
        self._dismiss_dialogs()
        link = self._extract_offer_link()
        if not link:
            link = self._fallback_ocr_extraction()
        if not link:
            raise RuntimeError("Could not find Gemini Pro offer link in Google One app")
        logger.info("Offer link extracted: %s", link)
        return link

    def _open_google_one(self) -> None:
        """Launch the Google One app."""
        self.driver.activate_app(GOOGLE_ONE_PACKAGE)
        time.sleep(4)

    def _dismiss_dialogs(self) -> None:
        """Dismiss any onboarding or permission dialogs."""
        for text in ["Not now", "Skip", "Maybe later", "No thanks", "Got it"]:
            try:
                btn = self.driver.find_element(
                    AppiumBy.XPATH, f'//android.widget.Button[@text="{text}"]'
                )
                btn.click()
                time.sleep(1)
            except NoSuchElementException:
                pass

    def _extract_offer_link(self) -> Optional[str]:
        """
        Try multiple strategies to find the Gemini Pro offer redemption link.
        Strategy 1: Find banner element with content-desc or text containing the URL.
        Strategy 2: Navigate to Benefits tab and find deep link.
        Strategy 3: Use UIAutomator to search all clickable elements.
        """
        # Strategy 1: Look for any element with the offer link URL
        link = self._find_link_in_elements()
        if link:
            return link

        # Strategy 2: Navigate to Upgrade/Benefits tab
        self._navigate_to_upgrade()
        time.sleep(2)
        link = self._find_link_in_elements()
        if link:
            return link

        # Strategy 3: Look for Gemini banner and tap to get deep link
        link = self._tap_gemini_banner()
        if link:
            return link

        return None

    def _find_link_in_elements(self) -> Optional[str]:
        """Search all UI elements for the offer link."""
        try:
            # Use UIAutomator2 to find elements containing the offer URL
            elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().descriptionContains("one.google.com/partner-eft-onboard")',
            )
            for el in elements:
                desc = el.get_attribute("contentDescription") or ""
                link = self._extract_url(desc)
                if link:
                    return link
        except Exception as exc:
            logger.debug("UIAutomator search failed: %s", exc)

        # Search page source for the URL
        try:
            page_source = self.driver.page_source
            link = self._extract_url(page_source)
            if link:
                return link
        except Exception as exc:
            logger.debug("Page source search failed: %s", exc)

        return None

    def _navigate_to_upgrade(self) -> None:
        """Navigate to Upgrade or Benefits tab in Google One."""
        for tab_text in ["Upgrade", "Benefits", "Plans", "Get more storage"]:
            try:
                tab = self.driver.find_element(
                    AppiumBy.XPATH, f'//android.widget.TextView[@text="{tab_text}"]'
                )
                tab.click()
                time.sleep(2)
                return
            except NoSuchElementException:
                pass

        # Try bottom navigation
        try:
            nav = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().className("android.widget.BottomNavigationView")',
            )
            items = nav.find_elements(AppiumBy.CLASS_NAME, "android.widget.FrameLayout")
            if len(items) > 1:
                items[1].click()
                time.sleep(2)
        except Exception:
            pass

    def _tap_gemini_banner(self) -> Optional[str]:
        """Find and tap the Gemini Pro banner, then capture the resulting deep link."""
        gemini_texts = [
            "Gemini Pro",
            "Gemini Advanced",
            "Try Gemini",
            "AI Premium",
            "Claim offer",
            "Get offer",
            "Free trial",
        ]

        for text in gemini_texts:
            try:
                banner = self.driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{text}")',
                )
                # Get current activity before tapping
                banner.click()
                time.sleep(3)

                # Check if a browser/Chrome opened with the offer URL
                link = self._check_browser_url()
                if link:
                    return link

                # Check page source again
                page_source = self.driver.page_source
                link = self._extract_url(page_source)
                if link:
                    return link

                # Navigate back
                self.driver.back()
                time.sleep(1)
            except NoSuchElementException:
                continue
            except Exception as exc:
                logger.debug("Banner tap failed for text '%s': %s", text, exc)
                try:
                    self.driver.back()
                except Exception:
                    pass

        return None

    def _check_browser_url(self) -> Optional[str]:
        """Check if Chrome/browser is open with the offer URL."""
        try:
            # Switch context to see if browser opened
            contexts = self.driver.contexts
            for ctx in contexts:
                if "WEBVIEW" in ctx or "CHROMIUM" in ctx:
                    self.driver.switch_to.context(ctx)
                    url = self.driver.current_url
                    if OFFER_LINK_PREFIX in url:
                        self.driver.switch_to.context("NATIVE_APP")
                        return url
                    self.driver.switch_to.context("NATIVE_APP")
        except Exception as exc:
            logger.debug("Browser URL check failed: %s", exc)
        return None

    def _fallback_ocr_extraction(self) -> Optional[str]:
        """Use screenshot + OCR to find the offer link as last resort."""
        try:
            import pytesseract
            from PIL import Image
            import io
            import base64

            logger.info("Attempting OCR fallback for offer link extraction")
            screenshot_b64 = self.driver.get_screenshot_as_base64()
            img_data = base64.b64decode(screenshot_b64)
            img = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(img)
            link = self._extract_url(text)
            if link:
                logger.info("OCR found offer link")
                return link
        except Exception as exc:
            logger.warning("OCR fallback failed: %s", exc)
        return None

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract the offer URL from text using regex."""
        pattern = r'https://one\.google\.com/partner-eft-onboard/[^\s\'"<>]+'
        match = re.search(pattern, text)
        if match:
            return match.group(0).rstrip(".,;)")
        return None
