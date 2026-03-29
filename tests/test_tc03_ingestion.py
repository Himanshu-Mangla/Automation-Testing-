"""
TC-03: Project Search & Navigation
Test Case ID : TC-03
Module       : Project Management

Steps:
  1. Login via saved Chrome profile (MFA bypass).
  2. Click the 'View All' button on the dashboard.
  3. Type 'Sanity' in the search box and verify every result contains 'Sanity'.
  4. Click the 'Sanity Test' project card.
  5. Click the MANAGE button for 'Synced Project Files'.
  6. Close the drawer using the X (cross) button.
  7. Re-open drawer via MANAGE.
  8. Close the drawer using the CANCEL button.
  9. Re-open drawer via MANAGE.
  10. Navigate into '07. Documents for testing' folder and select 6 specific files.
  11. Navigate into '03. Shell Rome project' folder and select '03. Shell Rome'.
  12. Click SYNC and wait (up to 10 min) for the sync process to fully complete.
  13. Check the Synced Project Files table and log all files with 'Failed' status.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

AUTH_DIR    = Path(__file__).parent.parent / "auth"
PROFILE_DIR = AUTH_DIR / "chrome_profile"
APP_URL     = os.getenv("APP_URL")
BASE_DOMAIN = APP_URL.split("/login")[0] if APP_URL and "/login" in APP_URL else APP_URL

SEARCH_TERM  = "Sanity"
PROJECT_NAME = "Sanity Test"


def _log(msg: str):
    print(f"\n[TC-03] {msg}")


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")

    raw    = ChromeDriverManager().install()
    exe    = os.path.join(os.path.dirname(raw), "chromedriver.exe")
    driver = webdriver.Chrome(
        service=Service(exe if os.path.isfile(exe) else raw),
        options=options,
    )
    driver.maximize_window()
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(0)
    return driver


def _w(driver: webdriver.Chrome, timeout: int = 60) -> WebDriverWait:
    """WebDriverWait with a generous default — no hard time limits."""
    return WebDriverWait(driver, timeout)


def _js_click(driver: webdriver.Chrome, el) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)


class TestTC03ProjectSearch:

    def test_project_search_and_navigation(self):
        driver = None
        try:
            # ── Step 1: Login via saved session ───────────────────────────────
            _log("Step 1 — Launching Chrome with saved session …")
            driver = _build_driver()
            time.sleep(2)

            driver.get(BASE_DOMAIN)
            time.sleep(2)

            # Wait until redirected to a non-login page (session restored)
            _w(driver).until(
                lambda d: BASE_DOMAIN in d.current_url
                and "login" not in d.current_url.lower()
            )
            time.sleep(2)
            _log(f"Logged in: {driver.current_url}")

            # ── Step 2: Click 'View All' button ───────────────────────────────
            _log("Step 2 — Clicking 'View All' button …")

            view_all_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//*["
                 "contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'view all')"
                 " and (self::button or self::a or self::span or @role='button')"
                 "]"
                )
            ))
            _js_click(driver, view_all_btn)
            time.sleep(2)
            _log("Clicked 'View All'.")

            # Wait for the projects page to load
            _w(driver).until(lambda d: "projects" in d.current_url.lower())
            time.sleep(2)
            _log(f"Project list page loaded: {driver.current_url}")

            # Wait for project cards to be present before searching
            _w(driver).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ant-card.project-card")
            ))
            time.sleep(2)

            # ── Step 3: Search for 'Sanity' ───────────────────────────────────
            _log(f"Step 3 — Typing '{SEARCH_TERM}' in search box …")

            search_box = _w(driver).until(EC.element_to_be_clickable(
                (By.XPATH, "//input[contains(@class,'ant-input') and @placeholder='Search...']")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_box)
            time.sleep(2)
            search_box.click()
            time.sleep(2)
            search_box.clear()
            time.sleep(2)
            search_box.send_keys(SEARCH_TERM)
            time.sleep(2)
            _log(f"Entered search term: '{SEARCH_TERM}'")

            # Wait for any loading spinner to clear
            _w(driver).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".ant-spin-spinning")) == 0
            )
            time.sleep(2)

            # ── Step 3a: Verify every result contains 'Sanity' ────────────────
            _log("Step 3a — Verifying search results all contain 'Sanity' …")

            # Wait until ALL visible project cards contain the search term
            # (confirms debounce + filter has fully applied)
            _w(driver).until(lambda d: (
                len([
                    c for c in d.find_elements(By.CSS_SELECTOR, ".ant-card.project-card")
                    if c.is_displayed()
                ]) > 0
                and all(
                    SEARCH_TERM.lower() in c.text.lower()
                    for c in d.find_elements(By.CSS_SELECTOR, ".ant-card.project-card")
                    if c.is_displayed()
                )
            ))
            time.sleep(2)

            # Collect the filtered cards for assertion
            project_cards   = driver.find_elements(By.CSS_SELECTOR, ".ant-card.project-card")
            visible_cards   = [c for c in project_cards if c.is_displayed()]
            _log(f"Found {len(visible_cards)} project card(s) after search filter.")

            mismatches = []
            for card in visible_cards:
                try:
                    header_text = card.find_element(By.CSS_SELECTOR, ".card-header").text.strip()
                except Exception:
                    header_text = card.text.strip()
                if SEARCH_TERM.lower() not in header_text.lower():
                    mismatches.append(header_text)

            assert not mismatches, (
                f"Results not matching '{SEARCH_TERM}': {mismatches}"
            )
            _log(f"All {len(visible_cards)} result(s) contain '{SEARCH_TERM}'. Search validation passed.")
            time.sleep(2)

            # ── Step 4: Click 'Sanity Test' project card ──────────────────────
            _log(f"Step 4 — Clicking '{PROJECT_NAME}' project card …")

            sanity_card = _w(driver).until(EC.element_to_be_clickable(
                (By.XPATH,
                 f"//div[contains(@class,'project-card')]"
                 f"[.//div[contains(@class,'card-header') and contains(normalize-space(.),'{PROJECT_NAME}')]]"
                )
            ))
            time.sleep(2)
            url_before = driver.current_url
            _js_click(driver, sanity_card)
            time.sleep(2)
            _log(f"Clicked '{PROJECT_NAME}' project card.")

            # Wait for navigation to project detail page
            _w(driver).until(lambda d: d.current_url != url_before)
            time.sleep(2)
            _log(f"Project detail page loaded: {driver.current_url}")

            # Confirm project name is visible on the detail page
            _w(driver).until(EC.visibility_of_element_located(
                (By.XPATH, f"//*[contains(normalize-space(.),'{PROJECT_NAME}')]")
            ))
            time.sleep(2)
            _log(f"'{PROJECT_NAME}' confirmed visible on detail page.")

            # ── Step 5: Click MANAGE button under 'Synced Project Files' ──────
            _log("Step 5 — Clicking MANAGE button for 'Synced Project Files' …")

            # Target the MANAGE button that is a descendant of the
            # section-head div containing 'Synced Project Files' text only.
            synced_manage_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//div[contains(@class,'section-head') and contains(normalize-space(.),'Synced Project Files')]"
                 "//button[normalize-space(.)='MANAGE']"
                )
            ))
            time.sleep(2)
            _js_click(driver, synced_manage_btn)
            time.sleep(2)
            _log("Clicked 'Synced Project Files' MANAGE button.")

            # Wait for the 'Select Sources' drawer to open
            # ant-drawer-open is on div.ant-drawer (outer); source-drawer is on div.ant-drawer-content (inner)
            _w(driver).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open")
            ))
            time.sleep(2)
            _log("'Select Sources' drawer opened successfully.")

            # ── Step 6: Click the cross (X) button on the drawer ──────────────
            _log("Step 6 — Clicking the cross (X) button on the Select Sources drawer …")

            cross_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open div.source-drawer button.close-btn")
            ))
            time.sleep(2)
            _js_click(driver, cross_btn)
            time.sleep(2)
            _log("Clicked cross (X) button.")

            # Wait for drawer to close (ant-drawer-open class removed)
            _w(driver).until(lambda d:
                len(d.find_elements(By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open")) == 0
            )
            time.sleep(2)
            _log("Drawer closed via X.")

            # ── Step 7: Click MANAGE button again ─────────────────────────────
            _log("Step 7 — Clicking 'Synced Project Files' MANAGE button again …")

            synced_manage_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//div[contains(@class,'section-head') and contains(normalize-space(.),'Synced Project Files')]"
                 "//button[normalize-space(.)='MANAGE']"
                )
            ))
            time.sleep(2)
            _js_click(driver, synced_manage_btn)
            time.sleep(2)
            _log("Clicked MANAGE button.")

            # Wait for the drawer to open again
            _w(driver).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open")
            ))
            time.sleep(2)
            _log("'Select Sources' drawer re-opened.")

            # ── Step 8: Click the Cancel button on the drawer ─────────────────
            _log("Step 8 — Clicking the CANCEL button on the Select Sources drawer …")

            cancel_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "div.ant-drawer.ant-drawer-open div.drawer-footer button.ant-btn-default")
            ))
            time.sleep(2)
            _js_click(driver, cancel_btn)
            time.sleep(2)
            _log("Clicked CANCEL button.")

            # Wait for drawer to close
            _w(driver).until(lambda d:
                len(d.find_elements(By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open")) == 0
            )
            time.sleep(2)
            _log("Drawer closed via CANCEL.")

            # ── Step 9: Click MANAGE button one more time ─────────────────────
            _log("Step 9 — Clicking 'Synced Project Files' MANAGE button one more time …")

            synced_manage_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//div[contains(@class,'section-head') and contains(normalize-space(.),'Synced Project Files')]"
                 "//button[normalize-space(.)='MANAGE']"
                )
            ))
            time.sleep(2)
            _js_click(driver, synced_manage_btn)
            time.sleep(2)
            _log("Clicked MANAGE button.")

            # Wait for the drawer to open
            _w(driver).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open")
            ))
            time.sleep(2)
            _log("'Select Sources' drawer opened successfully.")

            # ── Step 10: Navigate into folder and select 6 files ──────────────
            _log("Step 10 — Navigating into '07. Documents for testing' folder …")

            TARGET_FILES = [
                "ACS Occupation by Sex and Earnings 2023.xlsx",
                "EA3 Update Mar 26.jpg",
                "B2B R1 Human Rights Policy.docx",
                "Louisiana GDP 2024.xlsx",
                "Mississippi Infrastructure Report Card 2024.pdf",
                "North Carolina Mining Logging 2022.pptx",
            ]

            # Click the folder title (div.file-title inside the row) using ActionChains
            folder_title = _w(driver).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'ant-drawer-open')]"
                 "//tr[contains(@class,'ant-table-row') and "
                 "contains(normalize-space(.),'07. Documents for testing')]"
                 "//div[contains(@class,'file-title')]"
                )
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", folder_title)
            time.sleep(2)
            ActionChains(driver).move_to_element(folder_title).click().perform()
            time.sleep(2)

            # Wait for breadcrumb to show the folder name
            _w(driver).until(lambda d:
                "07. Documents for testing" in
                d.find_element(By.CSS_SELECTOR,
                    "div.ant-drawer.ant-drawer-open .breadcrumb-files"
                ).text
            )
            time.sleep(2)
            _log("Inside '07. Documents for testing' folder.")

            # Select each of the 6 target files by clicking their checkbox
            for filename in TARGET_FILES:
                _log(f"  Selecting: {filename}")

                checkbox = _w(driver).until(EC.presence_of_element_located(
                    (By.XPATH,
                     f"//div[contains(@class,'ant-drawer-open')]"
                     f"//tr[contains(@class,'ant-table-row') and "
                     f"contains(normalize-space(.),'{filename}')]"
                     f"//input[@type='checkbox']"
                    )
                ))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
                time.sleep(2)

                # Click via the visible ant-checkbox span (Ant Design pattern)
                ant_checkbox = checkbox.find_element(
                    By.XPATH, "./ancestor::span[contains(@class,'ant-checkbox')]"
                )
                ActionChains(driver).move_to_element(ant_checkbox).click().perform()
                time.sleep(2)

                # Verify the checkbox is now checked
                _w(driver).until(lambda d, cb=checkbox: cb.get_attribute("checked") is not None
                    or "ant-checkbox-checked" in (
                        d.execute_script(
                            "return arguments[0].closest('.ant-checkbox').className;", cb
                        ) or ""
                    )
                )
                _log(f"  Checked: {filename}")

            _log("All 6 files selected successfully.")
            time.sleep(2)

            # ── Step 11: Navigate into Shell Rome project and select Shell Rome ─
            _log("Step 11 — Navigating into '03. Shell Rome project' folder …")

            shell_folder_title = _w(driver).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'ant-drawer-open')]"
                 "//tr[contains(@class,'ant-table-row') and "
                 "contains(normalize-space(.),'03. Shell Rome project')]"
                 "//div[contains(@class,'file-title')]"
                )
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", shell_folder_title)
            time.sleep(2)
            ActionChains(driver).move_to_element(shell_folder_title).click().perform()
            time.sleep(2)

            # Wait for breadcrumb to confirm navigation into Shell Rome project
            _w(driver).until(lambda d:
                "03. Shell Rome project" in
                d.find_element(By.CSS_SELECTOR,
                    "div.ant-drawer.ant-drawer-open .breadcrumb-files"
                ).text
            )
            time.sleep(2)
            _log("Inside '03. Shell Rome project' folder.")

            # Select checkbox of '03. Shell Rome'
            _log("  Selecting: 03. Shell Rome")

            shell_checkbox = _w(driver).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'ant-drawer-open')]"
                 "//tr[contains(@class,'ant-table-row')]"
                 "[.//span[contains(@class,'file-title-text') and normalize-space(.)='03. Shell Rome']]"
                 "//input[@type='checkbox']"
                )
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", shell_checkbox)
            time.sleep(2)

            ant_checkbox = shell_checkbox.find_element(
                By.XPATH, "./ancestor::span[contains(@class,'ant-checkbox')]"
            )
            ActionChains(driver).move_to_element(ant_checkbox).click().perform()
            time.sleep(2)

            # Verify checkbox is checked
            _w(driver).until(lambda d, cb=shell_checkbox:
                "ant-checkbox-checked" in (
                    d.execute_script(
                        "return arguments[0].closest('.ant-checkbox').className;", cb
                    ) or ""
                )
            )
            _log("  Checked: 03. Shell Rome")
            time.sleep(2)

            # ── Step 12: Click SYNC and wait for sync to fully complete ────────
            _log("Step 12 — Clicking SYNC button …")

            sync_btn = _w(driver).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "div.ant-drawer.ant-drawer-open div.drawer-footer button.ant-btn-primary")
            ))
            time.sleep(2)
            _js_click(driver, sync_btn)
            time.sleep(2)
            _log("Clicked SYNC. Waiting for sync to complete …")

            # Drawer closes immediately after SYNC — wait for it
            _w(driver).until(lambda d:
                len(d.find_elements(By.CSS_SELECTOR, "div.ant-drawer.ant-drawer-open")) == 0
            )
            time.sleep(2)

            # Wait for sync to complete — poll every 10s, log progress, timeout 30 min
            _log("Waiting for sync to complete (up to 30 minutes) …")
            sync_done  = False
            elapsed    = 0
            max_wait   = 1800  # 30 minutes

            while elapsed < max_wait:
                time.sleep(10)
                elapsed += 10

                containers = driver.find_elements(
                    By.CSS_SELECTOR, "div.sync-files div.file-processing-container"
                )
                spinner_visible = any(c.is_displayed() for c in containers)
                table_rows      = driver.find_elements(
                    By.CSS_SELECTOR, "div.sync-files .ant-table-row"
                )
                rows_visible = any(r.is_displayed() for r in table_rows)

                if elapsed % 30 == 0:
                    _log(f"  [{elapsed}s] spinner={spinner_visible} table_rows={len(table_rows)}")

                if rows_visible or not spinner_visible:
                    sync_done = True
                    break

            assert sync_done, f"Sync did not complete within {max_wait // 60} minutes."
            time.sleep(2)
            _log("Sync completed — table loaded.")

            # Wait for the synced files table rows to be present
            _w(driver).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.sync-files .ant-table-row")
            ))
            time.sleep(2)
            _log("Synced Project Files table confirmed.")

            # ── Step 13: Collect all files with 'Failed' status ───────────────
            _log("Step 13 — Checking Status column for failed files …")

            synced_rows = driver.find_elements(
                By.CSS_SELECTOR, "div.sync-files .ant-table-row"
            )
            failed_files = []

            for row in synced_rows:
                if not row.is_displayed():
                    continue
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                row_text = row.text.strip()

                # Check if 'Failed' appears in the row text
                if "failed" in row_text.lower():
                    # Extract the file title from the first non-checkbox cell
                    title = ""
                    for cell in cells:
                        cell_text = cell.text.strip()
                        if cell_text and cell_text.lower() != "failed":
                            title = cell_text
                            break
                    if title:
                        failed_files.append(title)

            if failed_files:
                _log(f"Files with 'Failed' status ({len(failed_files)}):")
                for f in failed_files:
                    _log(f"  - {f}")
            else:
                _log("No files with 'Failed' status found — all synced successfully.")

            _log("TC-03 Completed Successfully.")

        except Exception as exc:
            _log(f"Test failed: {exc}")
            raise

        finally:
            if driver:
                time.sleep(3)
                driver.quit()
