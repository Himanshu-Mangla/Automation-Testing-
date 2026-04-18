from pages.base_page import BasePage


class DashboardPage(BasePage):
    def goto(self):
        super().goto("/")

    def create_project(self, name: str, description: str, due_date_text: str):
        self.page.get_by_role("button", name="CREATE PROJECT").wait_for()
        self.page.get_by_role("button", name="CREATE PROJECT").click()
        self.page.get_by_role("textbox", name="Project Name *").fill(name)
        self.page.get_by_role("textbox", name="Description *").fill(description)
        self.page.get_by_role("textbox", name="Due Date *").click()
        self.page.get_by_text(due_date_text).click()
        self.page.get_by_role("button", name="CREATE PROJECT").click()
        self.page.wait_for_load_state("networkidle")

    def add_collaborator(self, search_text: str, full_name: str):
        self.page.get_by_role("button", name="Collaborators").click()
        self.page.get_by_role("button", name="MANAGE").click()
        self.page.get_by_role("textbox", name="Search users to add...").fill(search_text)
        self.page.get_by_text(full_name).nth(1).click()
        self.page.get_by_role("button", name="SAVE").click()
        self.page.wait_for_load_state("networkidle")
