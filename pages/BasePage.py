import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)

    def _pause(self):
        """2-second gap between every action."""
        time.sleep(2)

    def open(self, url):
        self.driver.get(url)
        self._pause()

    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()
        self._pause()

    def type(self, locator, text):
        el = self.wait.until(EC.visibility_of_element_located(locator))
        el.clear()
        el.send_keys(text)
        self._pause()

    def get_text(self, locator):
        el = self.wait.until(EC.visibility_of_element_located(locator))
        self._pause()
        return el.text

    def is_visible(self, locator, timeout=15):
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            self._pause()
            return True
        except Exception:
            return False

    def wait_for_url_contains(self, partial_url, timeout=30):
        WebDriverWait(self.driver, timeout).until(EC.url_contains(partial_url))
        self._pause()
