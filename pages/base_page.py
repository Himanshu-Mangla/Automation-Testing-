from playwright.sync_api import Page
from config.config import TIMEOUT


class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.page.set_default_timeout(TIMEOUT)

    def goto(self, path: str = "/"):
        self.page.goto(path)
        self.page.wait_for_load_state("networkidle")

    def take_screenshot(self, name: str):
        self.page.screenshot(path=f"screenshots/{name}.png")
