from playwright.sync_api import Playwright, sync_playwright
from config.config import BASE_URL, EMAIL, PASSWORD, HEADLESS


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=HEADLESS)
    context = browser.new_context(base_url=BASE_URL)
    page = context.new_page()
    page.goto("/login")
    page.get_by_role("button", name="microsoft Continue with").click()
    page.get_by_role("textbox", name="Enter your email, phone, or").fill(EMAIL)
    page.get_by_role("button", name="Next").click()
    page.locator("#i0118").wait_for(state="visible")
    page.locator("#i0118").fill(PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.goto("/")
    page.get_by_role("button", name="CREATE PROJECT").click()
    page.get_by_role("textbox", name="Project Name *").click()
    page.get_by_role("textbox", name="Project Name *").fill("Test-76788")
    page.get_by_role("textbox", name="Description *").click()
    page.get_by_role("textbox", name="Description *").fill("Test-98")
    page.get_by_role("textbox", name="Due Date *").click()
    page.get_by_text("23", exact=True).click()
    page.get_by_role("button", name="CREATE PROJECT").click()
    page.get_by_role("button", name="Collaborators").click()
    page.get_by_role("button", name="MANAGE").click()
    page.get_by_role("textbox", name="Search users to add...").click()
    page.get_by_role("textbox", name="Search users to add...").fill("gaurav")
    page.get_by_text("TPA Admin Gaurav Mane").click()
    page.get_by_role("button", name="SAVE").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
