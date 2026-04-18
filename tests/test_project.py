import allure
import pytest
from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from test_data.data import PROJECT
from config.config import EMAIL, PASSWORD


@allure.feature("Project Management")
class TestProject:

    @allure.story("Create Project")
    @allure.title("Create a new project and add a collaborator")
    def test_create_project_and_add_collaborator(self, page):
        with allure.step("Login with Microsoft"):
            login = LoginPage(page)
            login.goto()
            login.login_with_microsoft(EMAIL, PASSWORD)

        with allure.step("Navigate to dashboard"):
            dashboard = DashboardPage(page)
            dashboard.goto()

        with allure.step("Create project"):
            dashboard.create_project(
                name=PROJECT["name"],
                description=PROJECT["description"],
                due_date_text=PROJECT["due_date_text"],
            )

        with allure.step("Add collaborator"):
            dashboard.add_collaborator(
                search_text=PROJECT["collaborator_search"],
                full_name=PROJECT["collaborator_full_name"],
            )
