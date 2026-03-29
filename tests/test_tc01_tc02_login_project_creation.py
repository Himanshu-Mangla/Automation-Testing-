"""
TC-01 + TC-02: Login and Project Creation (merged)
Test Case ID : TC-01 / TC-02
Module       : Authentication + Project Management

Steps:
  TC-01 — Login
    1. Check for existing cookie session stamp.
    2. Launch Chrome with persistent profile.
    3. If session valid  → verify dashboard loads (MFA bypassed).
       If session invalid → perform manual SSO + MFA login and save session.

  TC-02 — Project Creation (continues in the same browser)
    1. Click Create Project button.
    2. Close modal via X.
    3. Open again → close via Cancel.
    4. Open again → fill all fields and submit.
    5. Verify project was created successfully.
"""

import os
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────
AUTH_DIR         = Path(__file__).parent.parent / "auth"
COOKIES_FILE     = AUTH_DIR / "auth_cookies.json"
PROFILE_DIR      = AUTH_DIR / "chrome_profile"
COOKIE_MAX_AGE_H = 24 * 90  # 90 days

APP_URL     = os.getenv("APP_URL")
USERNAME    = os.getenv("APP_USERNAME")
PASSWORD    = os.getenv("PASSWORD")
BASE_DOMAIN = APP_URL.split("/login")[0] if APP_URL and "/login" in APP_URL else APP_URL

# CI detection — GitHub Actions sets CI=true automatically
CI_MODE = os.getenv("CI", "false").lower() == "true"

MFA_WAIT_S = 300
MFA_POLL_S = 5

PROJECT_NAME        = "Sanity Test"
PROJECT_DESCRIPTION = "This is a testing description"
COUNTRY             = "India"
STATE               = "Haryana"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _log(tag, msg):
    print(f"\n[{tag}] {msg}")


def _build_driver() -> webdriver.Chrome:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    options = Options()

    if CI_MODE:
        # Headless mode for GitHub Actions (no display, no persistent profile)
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        _log("TC-01", "CI mode — headless Chrome, no profile directory.")
    else:
        # Local mode — persistent profile for MFA bypass
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        options.add_argument("--start-maximized")
        options.add_argument(f"--user-data-dir={PROFILE_DIR}")

    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    raw = ChromeDriverManager().install()
    exe = os.path.join(os.path.dirname(raw), "chromedriver.exe")
    if not os.path.isfile(exe):
        exe = raw
    driver = webdriver.Chrome(service=Service(exe), options=options)
    if not CI_MODE:
        driver.maximize_window()
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(0)
    return driver


def _w(driver, t=30):
    return WebDriverWait(driver, t)


def _js_click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", el)
    time.sleep(2)


# ── TC-01: Session helpers ────────────────────────────────────────────────────

def _session_stamp_valid() -> bool:
    if not COOKIES_FILE.exists() or not PROFILE_DIR.exists():
        _log("TC-01", "No saved session found → first-time login required.")
        return False
    try:
        data     = json.loads(COOKIES_FILE.read_text(encoding="utf-8"))
        saved_at = datetime.fromisoformat(data["savedAt"])
        age      = datetime.now() - saved_at
        if age < timedelta(hours=COOKIE_MAX_AGE_H):
            remaining = timedelta(hours=COOKIE_MAX_AGE_H) - age
            _log("TC-01", f"Session stamp valid (expires in {remaining.days}d {remaining.seconds//3600}h).")
            return True
        _log("TC-01", "Session stamp expired → re-login required.")
        return False
    except Exception as exc:
        _log("TC-01", f"Session stamp unreadable ({exc}) → first-time login required.")
        return False


def _is_on_dashboard(driver) -> bool:
    driver.get(BASE_DOMAIN)
    time.sleep(2)
    try:
        _w(driver, 10).until(lambda d: d.current_url != BASE_DOMAIN)
    except Exception:
        pass
    time.sleep(2)
    current = driver.current_url
    if BASE_DOMAIN in current and "login" not in current.lower():
        _log("TC-01", f"Dashboard loaded — MFA bypassed. URL: {current}")
        return True
    _log("TC-01", f"Not on dashboard — redirected to: {current}")
    return False


def _do_manual_login(driver):
    wait = _w(driver, 30)
    driver.get(APP_URL)
    time.sleep(2)
    _log("TC-01", "First-time login — please complete SSO + MFA in the browser.")

    sso_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH,
         "//*["
         "contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'microsoft') or "
         "contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sso') or "
         "contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'microsoft') or "
         "contains(translate(@data-testid,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'sso')"
         "]")
    ))
    sso_button.click(); time.sleep(2)

    email_input = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, 'input[name="loginfmt"], input[type="email"], input[id="i0116"]')
    ))
    email_input.clear(); email_input.send_keys(USERNAME); time.sleep(2)

    next_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'input[id="idSIButton9"], button[id="idSIButton9"], input[type="submit"]')
    ))
    next_btn.click(); time.sleep(2)

    password_input = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, 'input[name="passwd"], input[type="password"], input[id="i0118"]')
    ))
    password_input.clear(); password_input.send_keys(PASSWORD); time.sleep(2)

    signin_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, 'input[id="idSIButton9"], button[id="idSIButton9"], input[type="submit"]')
    ))
    signin_btn.click(); time.sleep(2)

    print("\n" + "=" * 70)
    print("  ACTION REQUIRED — APPROVE MFA ON YOUR AUTHENTICATOR APP")
    print(f"  Waiting up to {MFA_WAIT_S} seconds …")
    print("=" * 70)

    mfa_approved = False
    kmsi_clicked = False
    elapsed      = 0

    while elapsed < MFA_WAIT_S:
        current_url = driver.current_url
        if BASE_DOMAIN in current_url and "login" not in current_url.lower():
            mfa_approved = True
            _log("TC-01", f"MFA approved — redirected to: {current_url}")
            break
        on_ms = "login.microsoftonline.com" in current_url or "login.microsoft.com" in current_url
        if on_ms and not kmsi_clicked:
            try:
                page_src = driver.page_source.lower()
                if "stay signed in" in page_src or "kmsi" in current_url.lower():
                    kmsi_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'input[id="idSIButton9"], button[id="idSIButton9"]')
                        )
                    )
                    kmsi_btn.click(); kmsi_clicked = True
                    _log("TC-01", "Clicked Yes on 'Stay signed in?' prompt.")
                    try:
                        WebDriverWait(driver, 20).until(
                            lambda d: "login.microsoftonline.com" not in d.current_url
                        )
                    except Exception:
                        pass
                    time.sleep(2); continue
            except Exception:
                pass
        time.sleep(MFA_POLL_S); elapsed += MFA_POLL_S

    assert mfa_approved, f"MFA not approved within {MFA_WAIT_S}s. URL: {driver.current_url}"
    time.sleep(2)
    assert "login" not in driver.current_url.lower(), f"Expected dashboard but got: {driver.current_url}"
    _log("TC-01", f"Login successful. URL: {driver.current_url}")


def _save_session(driver):
    cookies       = driver.get_cookies()
    local_storage = {}
    try:
        keys = driver.execute_script("return Object.keys(localStorage);") or []
        for key in keys:
            val = driver.execute_script("return localStorage.getItem(arguments[0]);", key)
            if val is not None:
                local_storage[key] = val
    except Exception:
        pass
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    COOKIES_FILE.write_text(
        json.dumps({"savedAt": datetime.now().isoformat(), "cookies": cookies, "localStorage": local_storage}, indent=2),
        encoding="utf-8",
    )
    _log("TC-01", f"Session saved ({len(cookies)} cookies). Future runs will skip MFA.")


def _delete_session():
    if COOKIES_FILE.exists():
        os.remove(COOKIES_FILE)
    if PROFILE_DIR.exists():
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    _log("TC-01", "Stale session deleted — fresh login required.")


def _ci_login(driver):
    """
    CI mode login: injects session cookies exported from a local run.
    Requires SESSION_COOKIES GitHub Secret — a JSON string of the saved
    auth_cookies.json file produced after a successful local MFA login.
    """
    cookies_json = os.getenv("SESSION_COOKIES", "").strip()
    if not cookies_json:
        raise Exception(
            "CI mode: SESSION_COOKIES environment variable is not set.\n"
            "Run export_session.py locally after a successful login, then add\n"
            "the output as a GitHub Secret named SESSION_COOKIES."
        )

    try:
        data         = json.loads(cookies_json)
        cookies      = data.get("cookies", []) if isinstance(data, dict) else data
        local_storage = data.get("localStorage", {}) if isinstance(data, dict) else {}
    except json.JSONDecodeError as exc:
        raise Exception(f"CI mode: SESSION_COOKIES is not valid JSON — {exc}")

    # Must visit the domain before setting cookies
    driver.get(BASE_DOMAIN)
    time.sleep(2)

    # Inject each cookie (strip fields Selenium does not accept)
    injected = 0
    for cookie in cookies:
        try:
            clean = {k: v for k, v in cookie.items()
                     if k in ("name", "value", "domain", "path", "secure", "httpOnly", "expiry")}
            driver.add_cookie(clean)
            injected += 1
        except Exception:
            pass
    _log("TC-01", f"Injected {injected}/{len(cookies)} cookies.")

    # Restore localStorage tokens (JWT etc.)
    for key, val in local_storage.items():
        try:
            driver.execute_script("localStorage.setItem(arguments[0], arguments[1]);", key, val)
        except Exception:
            pass

    # Reload so the app picks up the session
    driver.refresh()
    time.sleep(3)

    current = driver.current_url
    if "login" in current.lower():
        raise Exception(
            f"CI cookie injection failed — still on login page: {current}\n"
            "Cookies may have expired. Re-run export_session.py locally and update the GitHub Secret."
        )
    _log("TC-01", f"CI session restored. URL: {current}")


# ── TC-02: Project creation helpers ──────────────────────────────────────────

def _modal_open(driver):
    try:
        return driver.find_element(
            By.XPATH, "//*[@role='dialog' or contains(@class,'ant-modal-wrap')]"
        ).is_displayed()
    except Exception:
        return False


def _create_btn(driver):
    return _w(driver).until(EC.element_to_be_clickable(
        (By.XPATH,
         "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'create project')]")
    ))


def _close_x(driver):
    btn = _w(driver).until(EC.presence_of_element_located(
        (By.XPATH,
         "//*[contains(@class,'ant-modal')]//button[contains(@class,'ant-modal-close') or contains(@aria-label,'lose')]")
    ))
    _js_click(driver, btn)
    _log("TC-02", "Closed via X.")


def _close_cancel(driver):
    btn = _w(driver).until(EC.presence_of_element_located(
        (By.XPATH,
         "//*[contains(@class,'ant-modal')]//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'cancel')]")
    ))
    _js_click(driver, btn)
    _log("TC-02", "Closed via Cancel.")


def _pick_today(driver, field_id):
    wrapper = _w(driver).until(EC.presence_of_element_located(
        (By.XPATH, f"//input[@id='{field_id}']/ancestor::*[contains(@class,'ant-picker')][1]")
    ))
    _js_click(driver, wrapper)
    time.sleep(1)
    btns = [b for b in driver.find_elements(By.CSS_SELECTOR, "a.ant-picker-now-btn,button.ant-picker-now-btn") if b.is_displayed()]
    if btns:
        _js_click(driver, btns[-1])
        _log("TC-02", f"Set '{field_id}' → today.")
        return
    cells = [c for c in driver.find_elements(By.CSS_SELECTOR, "td.ant-picker-cell-today .ant-picker-cell-inner") if c.is_displayed()]
    if cells:
        _js_click(driver, cells[-1])
        _log("TC-02", f"Set '{field_id}' → today (cell).")
        return
    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    time.sleep(1)


def _ant_select(driver, field_id, option_text, wait_enabled=True):
    search_input = _w(driver).until(EC.presence_of_element_located((By.ID, field_id)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_input)
    time.sleep(1)

    if wait_enabled:
        try:
            _w(driver, 15).until(lambda d: "ant-select-disabled" not in (
                d.execute_script("return arguments[0].closest('.ant-select').className;", search_input) or ""
            ))
        except Exception:
            pass
        time.sleep(1)

    selector = driver.execute_script(
        "return arguments[0].closest('.ant-select').querySelector('.ant-select-selector');",
        search_input
    )
    ActionChains(driver).move_to_element(selector).click().perform()
    time.sleep(2)

    dropdown_visible_xpath = (
        "//div[contains(@class,'ant-select-dropdown') "
        "and not(contains(@class,'ant-select-dropdown-hidden'))]"
    )
    try:
        _w(driver, 15).until(EC.presence_of_element_located((By.XPATH, dropdown_visible_xpath)))
    except Exception:
        pass
    time.sleep(1)

    option_xpath = (
        f"{dropdown_visible_xpath}"
        f"//div[contains(@class,'ant-select-item-option-content') and normalize-space(.)='{option_text}']"
    )

    wrapper_class = driver.execute_script(
        "return arguments[0].closest('.ant-select').className;", search_input
    ) or ""

    if "ant-select-show-search" in wrapper_class:
        ActionChains(driver).send_keys(option_text).perform()
        time.sleep(4)
        option = _w(driver, 30).until(EC.presence_of_element_located((By.XPATH, option_xpath)))
        _js_click(driver, option)
    else:
        for _ in range(40):
            try:
                opts    = driver.find_elements(By.XPATH, option_xpath)
                visible = [o for o in opts if o.is_displayed()]
                if visible:
                    _js_click(driver, visible[0])
                    _log("TC-02", f"Selected '{option_text}' from '{field_id}'.")
                    return
            except Exception:
                pass
            driver.execute_script("""
                var dd = document.querySelector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)');
                if (dd) { var h = dd.querySelector('.rc-virtual-list-holder'); if (h) h.scrollTop += arguments[0]; }
            """, 150)
            time.sleep(0.3)
        raise Exception(f"Option '{option_text}' not found in '{field_id}' after scrolling")

    _log("TC-02", f"Selected '{option_text}' from '{field_id}'.")


# ── Merged Test ───────────────────────────────────────────────────────────────

class TestTC01TC02LoginAndProjectCreation:

    def test_login_and_project_creation(self):
        driver = None
        try:

            # ════════════════════════════════════════════════════════
            #  TC-01: LOGIN
            # ════════════════════════════════════════════════════════

            _log("TC-01", f"Step 1 — Mode: {'CI (cookie injection)' if CI_MODE else 'Local (Chrome profile)'}")

            _log("TC-01", "Step 2 — Launching Chrome …")
            driver = _build_driver()
            time.sleep(2)

            if CI_MODE:
                # ── CI path: inject cookies from SESSION_COOKIES secret ──────
                _log("TC-01", "Step 3 — Restoring session from SESSION_COOKIES secret …")
                _ci_login(driver)
            else:
                # ── Local path: Chrome persistent profile / MFA bypass ───────
                stamp_valid = _session_stamp_valid()
                if stamp_valid:
                    _log("TC-01", "Step 3 — Verifying session via persistent profile …")
                    on_dashboard = _is_on_dashboard(driver)
                    if on_dashboard:
                        _log("TC-01", "Session restored successfully — MFA bypassed.")
                    else:
                        _log("TC-01", "Session rejected — performing fresh login …")
                        driver.quit(); driver = None
                        _delete_session()
                        driver = _build_driver(); time.sleep(2)
                        _do_manual_login(driver)
                        _save_session(driver)
                else:
                    _log("TC-01", "Step 3 — Starting manual SSO login …")
                    _do_manual_login(driver)
                    _log("TC-01", "Step 4 — Saving session …")
                    _save_session(driver)

            assert "login" not in driver.current_url.lower(), \
                f"Expected dashboard after login but got: {driver.current_url}"
            _log("TC-01", f"Login complete. URL: {driver.current_url}")
            time.sleep(2)

            # ════════════════════════════════════════════════════════
            #  TC-02: PROJECT CREATION (same browser session)
            # ════════════════════════════════════════════════════════

            _log("TC-02", "Step 1 — Clicking Create Project …")
            _js_click(driver, _create_btn(driver))
            _w(driver).until(lambda d: _modal_open(d))
            _log("TC-02", "Modal opened.")

            _log("TC-02", "Step 2 — Closing via X …")
            _close_x(driver)
            _w(driver).until(lambda d: not _modal_open(d))
            time.sleep(2)

            _log("TC-02", "Step 3 — Opening again …")
            _js_click(driver, _create_btn(driver))
            _w(driver).until(lambda d: _modal_open(d))
            _log("TC-02", "Step 4 — Clicking Cancel …")
            _close_cancel(driver)
            _w(driver).until(lambda d: not _modal_open(d))
            time.sleep(2)

            _log("TC-02", "Step 5 — Opening to fill form …")
            _js_click(driver, _create_btn(driver))
            _w(driver).until(lambda d: _modal_open(d))
            time.sleep(2)

            # Project Name
            f = _w(driver).until(EC.visibility_of_element_located((By.ID, "createProject_name")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", f)
            f.clear(); f.send_keys(PROJECT_NAME); time.sleep(2)
            _log("TC-02", f"Project Name: {PROJECT_NAME}")

            # Description
            f = _w(driver).until(EC.visibility_of_element_located((By.ID, "createProject_description")))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", f)
            f.clear(); f.send_keys(PROJECT_DESCRIPTION); time.sleep(2)
            _log("TC-02", "Description entered.")

            # Dates
            _pick_today(driver, "createProject_impactAssessmentDueDate")
            _pick_today(driver, "createProject_startDate")
            _pick_today(driver, "createProject_endDate")

            # Country & State
            _ant_select(driver, "createProject_country", COUNTRY)
            time.sleep(3)
            _ant_select(driver, "createProject_stateRegion", STATE, wait_enabled=True)
            time.sleep(2)
            _log("TC-02", "All fields filled.")

            _log("TC-02", "Step 6 — Submitting …")
            submit = _w(driver).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//*[contains(@class,'ant-modal')]//button[@type='submit' or "
                 "contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'create project')]")
            ))
            _js_click(driver, submit)
            time.sleep(2)

            # Verify creation
            success = False
            try:
                _w(driver, 15).until(lambda d: not _modal_open(d))
                success = True
                _log("TC-02", "Modal closed — project created successfully.")
            except Exception:
                pass

            if not success:
                try:
                    t = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                        (By.XPATH,
                         "//*[contains(@class,'ant-message') or contains(@class,'ant-notification')]"
                         "[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success') or "
                         "contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'created')]")
                    ))
                    _log("TC-02", f"Toast: {t.text}"); success = True
                except Exception:
                    pass

            if not success:
                try:
                    WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                        (By.XPATH, f"//*[contains(normalize-space(.),'{PROJECT_NAME}')]")
                    ))
                    success = True
                    _log("TC-02", f"'{PROJECT_NAME}' visible on page.")
                except Exception:
                    pass

            assert success, f"Project creation not verified. URL: {driver.current_url}"
            _log("TC-02", "TC-01 + TC-02 Completed Successfully.")

        except Exception as exc:
            _log("ERROR", f"Test failed: {exc}")
            raise
        finally:
            if driver:
                time.sleep(3)
                driver.quit()
