import logging
import time
from typing import Optional

from appium import webdriver
from appium.options import AppiumOptions

logger = logging.getLogger(__name__)

APPIUM_SERVER_URL = "http://localhost:4723"


class AppiumClient:
    """Manages Appium connection to a Firebase Test Lab device via ADB."""

    def __init__(self, adb_host: str = "", adb_port: str = "5554"):
        self.adb_host = adb_host
        self.adb_port = adb_port

    def connect(self, retries: int = 3, wait: int = 10):
        """Connect to device via Appium with retry logic."""
        options = AppiumOptions()
        options.platform_name = "Android"
        options.automation_name = "UiAutomator2"
        options.set_capability("appPackage", "com.google.android.gm")
        options.set_capability("appActivity", ".ConversationListActivityGmail")
        options.set_capability("noReset", True)
        options.set_capability("fullReset", False)
        options.set_capability("autoGrantPermissions", True)
        options.set_capability("newCommandTimeout", 300)
        options.set_capability("androidDeviceSocket", "appiumfwd")

        if self.adb_host:
            options.set_capability("udid", f"{self.adb_host}:{self.adb_port}")

        last_exc = None
        for attempt in range(1, retries + 1):
            try:
                logger.info(
                    "Connecting to Appium (attempt %d/%d) - device %s:%s",
                    attempt,
                    retries,
                    self.adb_host,
                    self.adb_port,
                )
                driver = webdriver.Remote(APPIUM_SERVER_URL, options=options)
                logger.info("Appium connection established")
                return driver
            except Exception as exc:
                last_exc = exc
                logger.warning("Appium connection attempt %d failed: %s", attempt, exc)
                if attempt < retries:
                    time.sleep(wait)

        raise RuntimeError(f"Failed to connect to Appium after {retries} attempts: {last_exc}")
