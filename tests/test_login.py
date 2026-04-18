import allure
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from config.config import EMAIL, PASSWORD


@allure.feature("Authentication")
class TestLogin:

    @allure.story("Microsoft Login")
    @allure.title("Login with Microsoft and verify dashboard access")
    def test_login_with_microsoft(self, page):
        with allure.step("Navigate to login page"):
            login = LoginPage(page)
            login.goto()

        with allure.step("Login with Microsoft credentials"):
            login.login_with_microsoft(EMAIL, PASSWORD)

        with allure.step("Navigate to dashboard and verify access"):
            dashboard = DashboardPage(page)
            dashboard.goto()
            page.get_by_role("button", name="CREATE PROJECT").wait_for()
