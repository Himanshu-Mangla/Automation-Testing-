from playwright.sync_api import Page


def wait_and_click(page: Page, locator, timeout: int = 60000):
    locator.wait_for(timeout=timeout)
    locator.click()


def take_screenshot(page: Page, name: str):
    page.screenshot(path=f"screenshots/{name}.png")
