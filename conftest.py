import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from playwright.sync_api import sync_playwright
from config.config import BASE_URL, HEADLESS, SLOW_MO


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser):
    auth_file = os.path.join(os.path.dirname(__file__), "auth_state.json")
    kwargs = {"base_url": BASE_URL}
    if os.path.exists(auth_file):
        kwargs["storage_state"] = auth_file
    context = browser.new_context(**kwargs)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context, request):
    page = context.new_page()
    yield page
    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        import os
        os.makedirs("screenshots", exist_ok=True)
        page.screenshot(path=f"screenshots/{request.node.name}.png")
        print(f"\nFailed on URL: {page.url}")
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
