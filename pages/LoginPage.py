import os
from selenium.webdriver.common.by import By
from pages.BasePage import BasePage


class LoginPage(BasePage):
    # Locators — priority: data-testid → aria-label → placeholder → CSS → XPath
    USERNAME_INPUT = (By.CSS_SELECTOR, 'input[type="email"], input[name="username"], input[placeholder*="email" i], input[placeholder*="username" i]')
    PASSWORD_INPUT = (By.CSS_SELECTOR, 'input[type="password"]')
    LOGIN_BUTTON   = (By.CSS_SELECTOR, 'button[type="submit"], button[aria-label*="sign in" i], button[aria-label*="login" i]')

    def open_login_page(self):
        self.open(os.environ["APP_URL"])

    def enter_username(self, username=None):
        self.type(self.USERNAME_INPUT, username or os.environ["APP_USERNAME"])

    def enter_password(self, password=None):
        self.type(self.PASSWORD_INPUT, password or os.environ["PASSWORD"])

    def click_login(self):
        self.click(self.LOGIN_BUTTON)

    def login(self, username=None, password=None):
        self.open_login_page()
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
