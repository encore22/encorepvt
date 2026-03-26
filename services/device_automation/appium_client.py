import logging
import time
from typing import Optional

from appium import webdriver
from appium.options.android import UiAutomator2Options

logger = logging.getLogger(__name__)

APPIUM_SERVER_URL = "http://localhost:4723"


class AppiumClient:
    """Manages Appium connection to a Firebase Test Lab device via ADB."""

    def __init__(self, adb_host: str = "", adb_port: str = "5554"):
        self.adb_host = adb_host
        self.adb_port = adb_port

    def connect(self, retries: int = 3, wait: int = 10):
        """Connect to device via Appium with retry logic."""
        options = UiAutomator2Options()
        options.app_package = "com.google.android.gm"
        options.app_activity = ".ConversationListActivityGmail"
        options.no_reset = True
        options.full_reset = False
        options.auto_grant_permissions = True
        options.new_command_timeout = 300
        options.android_device_socket = "appiumfwd"

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
