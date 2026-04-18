from playwright.sync_api import sync_playwright
from config.config import BASE_URL, EMAIL

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(base_url=BASE_URL)
    page = context.new_page()

    page.goto("/login")
    page.get_by_role("button", name="microsoft Continue with").click()
    page.get_by_role("textbox", name="Enter your email, phone, or").fill(EMAIL)
    page.get_by_role("button", name="Next").click()

    print("Complete MFA in the browser, then press Enter here...")
    input()

    context.storage_state(path="auth_state.json")
    print("Auth state saved to auth_state.json")

    browser.close()
