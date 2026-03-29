import os
import sys
import time
import pytest
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


# ── WebDriver fixture ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def driver():
    chrome_options = Options()

    if os.getenv("HEADLESS", "false").lower() == "true":
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
    else:
        chrome_options.add_argument("--start-maximized")

    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    raw_path   = ChromeDriverManager().install()
    driver_dir = os.path.dirname(raw_path)
    driver_exe = os.path.join(driver_dir, "chromedriver.exe")
    if not os.path.isfile(driver_exe):
        driver_exe = raw_path

    service = Service(driver_exe)
    drv = webdriver.Chrome(service=service, options=chrome_options)
    drv.set_page_load_timeout(30)
    drv.implicitly_wait(0)

    yield drv
    drv.quit()


# ── Screenshot on failure ──────────────────────────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()

    if call.when == "call" and call.excinfo is not None:
        drv = item.funcargs.get("driver")
        if drv:
            os.makedirs("screenshots", exist_ok=True)
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"screenshots/{item.name}_{ts}.png"
            try:
                drv.save_screenshot(path)
            except Exception:
                pass


# ── Report metadata ────────────────────────────────────────────────────────

# Register test case metadata here as new test scripts are added.
# key = stem of the test file (e.g. "test_login")
_TEST_CASE_META: dict = {
    "test_tc01_tc02_login_project_creation": {
        "order":       1,
        "name":        "TC-01 + TC-02 - Login & Project Creation",
        "description": "Login via SSO (MFA bypass) then create a new project in the same session.",
    },
    "test_tc03_ingestion": {
        "order":       2,
        "name":        "TC-03 - Ingestion",
        "description": "Search for 'Sanity' project, navigate to project detail, and sync project files.",
    },
}

_session_results: dict = {}
_session_start:   float = 0.0


def pytest_sessionstart(session):
    global _session_start
    _session_start = time.time()


def pytest_runtest_logreport(report):
    if report.when != "call":
        return
    parts      = report.nodeid.split("::")
    module_key = Path(parts[0]).stem
    test_name  = parts[-1]

    _session_results.setdefault(module_key, []).append({
        "name":     test_name,
        "passed":   report.passed,
        "duration": round(getattr(report, "duration", 0.0), 2),
    })


def pytest_sessionfinish(session, exitstatus):
    ts    = datetime.now()
    fname = f"UAT_Report_{ts.strftime('%Y-%m-%d_%H-%M-%S')}.html"
    os.makedirs("reports", exist_ok=True)
    out   = os.path.join("reports", fname)
    _write_report(out, ts)
    print(f"\n\n  [OK]  UAT Report  ->  {out}\n")


# ── HTML Report ────────────────────────────────────────────────────────────

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#eef1f6;color:#333;min-height:100vh}
header{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);color:#fff;padding:28px 44px;display:flex;align-items:center;gap:18px}
.logo{font-size:2.2em;font-weight:900;letter-spacing:-1px;color:#e94560}
.hdr-title h1{font-size:1.5em;font-weight:700;margin:0}
.hdr-title p{font-size:.85em;color:#9ab;margin-top:4px}
.kpi-bar{display:flex;gap:14px;padding:24px 44px;flex-wrap:wrap}
.kpi{background:#fff;border-radius:10px;padding:18px 32px;min-width:130px;box-shadow:0 2px 8px rgba(0,0,0,.09);text-align:center}
.kpi .num{font-size:2.2em;font-weight:800;line-height:1}
.kpi .lbl{font-size:.75em;color:#999;margin-top:5px;text-transform:uppercase;letter-spacing:.07em}
.kpi.total .num{color:#0c5460}
.kpi.passed .num{color:#155724}
.kpi.failed .num{color:#721c24}
.kpi.duration .num{color:#856404}
.sec-lbl{padding:6px 44px 4px;font-size:.78em;text-transform:uppercase;letter-spacing:.1em;color:#888;font-weight:600}
.tbl-wrap{margin:0 44px 40px;border-radius:14px;overflow:hidden;box-shadow:0 2px 14px rgba(0,0,0,.11)}
table{width:100%;border-collapse:collapse;background:#fff}
thead tr{background:#1a1a2e}
th{color:#fff;padding:13px 16px;text-align:left;font-size:.76em;text-transform:uppercase;letter-spacing:.08em;white-space:nowrap}
td{padding:14px 16px;border-bottom:1px solid #f0f2f5;vertical-align:middle;font-size:.9em}
tr:last-child > td{border-bottom:none}
.pass-row{background:#f5fffb}
.fail-row{background:#fff5f5}
.pill{display:inline-block;padding:4px 16px;border-radius:20px;font-weight:700;font-size:.8em;letter-spacing:.04em}
.pill-pass{background:#d4edda;color:#155724}
.pill-fail{background:#f8d7da;color:#721c24}
footer{text-align:center;padding:18px;font-size:.78em;color:#aaa}
"""


def _fmt_dur(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m = int(seconds) // 60
    s = seconds - m * 60
    return f"{m}m {s:.0f}s"


def _case_row_html(idx: int, meta: dict, tests: list) -> str:
    total    = len(tests)
    failed   = sum(1 for t in tests if not t["passed"])
    ok       = failed == 0 and total > 0
    row_cls  = "pass-row" if ok else "fail-row"
    pill_cls = "pill-pass" if ok else "pill-fail"
    pill_txt = "PASS" if ok else "FAIL"

    return (
        f'<tr class="{row_cls}">'
        f'<td style="color:#aaa;font-weight:600">{idx}</td>'
        f'<td style="font-weight:700;font-size:.95em">{meta["name"]}</td>'
        f'<td style="color:#555">{meta["description"]}</td>'
        f'<td><span class="pill {pill_cls}">{pill_txt}</span></td>'
        f'</tr>'
    )


def _write_report(path: str, ts: datetime) -> None:
    total_duration = time.time() - _session_start

    ordered = sorted(
        _TEST_CASE_META.items(),
        key=lambda kv: kv[1].get("order", 99),
    )

    case_rows_html = ""
    total_cases  = len(ordered)
    passed_cases = 0
    failed_cases = 0

    for idx, (key, meta) in enumerate(ordered, 1):
        tests  = _session_results.get(key, [])
        failed = sum(1 for t in tests if not t["passed"])
        if failed == 0 and tests:
            passed_cases += 1
        else:
            failed_cases += 1
        case_rows_html += _case_row_html(idx, meta, tests)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ERM UAT Report – {ts.strftime('%Y-%m-%d %H:%M:%S')}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div class="logo">ERM</div>
  <div class="hdr-title">
    <h1>UAT Automation Report</h1>
    <p>{ts.strftime('%A, %B %d %Y  &nbsp;·&nbsp;  %H:%M:%S')}</p>
  </div>
</header>
<div class="kpi-bar">
  <div class="kpi total"><div class="num">{total_cases}</div><div class="lbl">Test Cases</div></div>
  <div class="kpi passed"><div class="num">{passed_cases}</div><div class="lbl">Passed</div></div>
  <div class="kpi failed"><div class="num">{failed_cases}</div><div class="lbl">Failed</div></div>
  <div class="kpi duration"><div class="num">{_fmt_dur(total_duration)}</div><div class="lbl">Duration</div></div>
</div>
<div class="sec-lbl">Test Case Results</div>
<div class="tbl-wrap">
  <table>
    <thead>
      <tr><th>#</th><th>Test Case</th><th>Description</th><th>Status</th></tr>
    </thead>
    <tbody>
      {case_rows_html}
    </tbody>
  </table>
</div>
<footer>ERM UAT Automation &nbsp;·&nbsp; {ts.strftime('%Y-%m-%d %H:%M:%S')}</footer>
</body>
</html>"""

    Path(path).write_text(html, encoding="utf-8")
