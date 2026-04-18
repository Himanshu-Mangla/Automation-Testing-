import re
from pages.base_page import BasePage
from playwright.sync_api import expect


class LoginPage(BasePage):
    def goto(self):
        super().goto("/login")

    def login_with_microsoft(self, email: str, password: str):
        self.page.get_by_role("button", name="microsoft Continue with").click()
        self.page.get_by_role("textbox", name="Enter your email, phone, or").fill(email)
        self.page.get_by_role("button", name="Next").click()
        self.page.locator("#i0118").wait_for(state="visible")
        self.page.locator("#i0118").click()
        self.page.locator("#i0118").press_sequentially(password, delay=50)
        self.page.get_by_role("button", name="Sign in").click()

        try:
            self.page.get_by_role("button", name="No").click(timeout=15000)
        except Exception:
            pass

        self.page.wait_for_load_state("networkidle", timeout=60000)
        import os
        os.makedirs("screenshots", exist_ok=True)
        self.page.screenshot(path="screenshots/post_login_debug.png")
        print(f"\nPost-login URL: {self.page.url}")
