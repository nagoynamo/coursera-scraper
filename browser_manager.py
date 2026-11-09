from __future__ import annotations

import os
import sys
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService


# Env vars that tell the dynamic loader / GTK / GIO where to find libraries and
# modules. When this scraper is launched from a terminal inside snap-packaged
# software (e.g. VS Code installed as a snap), the shell inherits versions of
# these pointing into the snap's private library set — things like
# GIO_MODULE_DIR=~/snap/code/common/.cache/gio-modules. A real system browser
# then follows them into the snap, loads a module built against the snap's old
# glibc, and dies with "symbol lookup error: .../libpthread.so.0: undefined
# symbol __libc_pthread_init". geckodriver/chromedriver only see the child exit
# with status 127. We strip these vars — but only when their value actually
# points at /snap or ~/snap — so on a normal machine this changes nothing.
_SNAP_LOADER_VARS = (
    "GIO_MODULE_DIR",
    "GTK_PATH",
    "GTK_EXE_PREFIX",
    "GTK_IM_MODULE_FILE",
    "GDK_PIXBUF_MODULE_FILE",
    "GDK_PIXBUF_MODULEDIR",
    "GSETTINGS_SCHEMA_DIR",
    "LOCPATH",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
)


def _clean_env() -> dict[str, str]:
    """Copy the current environment, dropping snap-loader vars that would make a
    system browser load libraries from a snap sandbox and crash on launch."""
    env = dict(os.environ)
    snap_roots = ("/snap/", os.path.expanduser("~/snap/"))
    for var in _SNAP_LOADER_VARS:
        val = env.get(var)
        if val and any(part.startswith(snap_roots) for part in val.split(os.pathsep)):
            env.pop(var, None)
    return env


class Browser(Enum):
    CHROME = "chrome"
    CHROMIUM = "chromium"
    EDGE = "edge"
    FIREFOX = "firefox"


# Auto-selection priority order
PRIORITY: list[Browser] = [Browser.CHROME, Browser.EDGE, Browser.CHROMIUM, Browser.FIREFOX]

_COMMON_PATHS: dict[Browser, dict[str, list[str]]] = {
    Browser.CHROME: {
        "linux": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/snap/bin/google-chrome",
            "/usr/local/bin/google-chrome",
        ],
        "darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
        "win32": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
    },
    Browser.CHROMIUM: {
        "linux": [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
        ],
        "darwin": ["/Applications/Chromium.app/Contents/MacOS/Chromium"],
        "win32": [r"C:\Program Files\Chromium\Application\chrome.exe"],
    },
    Browser.EDGE: {
        "linux": [
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable",
            "/opt/microsoft/msedge/msedge",
        ],
        "darwin": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
        "win32": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
    },
    Browser.FIREFOX: {
        "linux": [
            "/usr/bin/firefox",
            "/snap/bin/firefox",
            "/usr/lib/firefox/firefox",
        ],
        "darwin": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        "win32": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
    },
}

_PATH_NAMES: dict[Browser, list[str]] = {
    Browser.CHROME:   ["google-chrome", "google-chrome-stable", "chrome"],
    Browser.CHROMIUM: ["chromium", "chromium-browser"],
    Browser.EDGE:     ["microsoft-edge", "microsoft-edge-stable", "msedge"],
    Browser.FIREFOX:  ["firefox"],
}


def _find_executable(browser: Browser) -> Optional[str]:
    platform = "win32" if sys.platform == "win32" else ("darwin" if sys.platform == "darwin" else "linux")

    for path in _COMMON_PATHS.get(browser, {}).get(platform, []):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    for name in _PATH_NAMES.get(browser, []):
        found = shutil.which(name)
        if found:
            return found

    return None


class BrowserManager:
    def detect_browsers(self) -> list[Browser]:
        """Return all installed browsers."""
        return [b for b in Browser if _find_executable(b) is not None]

    def get_default_browser(self) -> Optional[Browser]:
        """Return highest-priority available browser."""
        available = self.detect_browsers()
        for b in PRIORITY:
            if b in available:
                return b
        return None

    def create_driver(
        self,
        browser: Browser,
        headless: bool = False,
        profile_dir: Optional[Path] = None,
        optimize: bool = False,
    ) -> webdriver.Remote:
        """Create a Selenium WebDriver. Uses Selenium Manager for automatic driver downloads.

        profile_dir: persistent profile path — Chrome/Edge auto-save cookies there.
        optimize: disable images/GPU/notifications for faster scraping.
        """
        if browser in (Browser.CHROME, Browser.CHROMIUM):
            opts = ChromeOptions()
            opts.page_load_strategy = "eager"
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            opts.add_argument("--window-size=1280,900")
            opts.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
            if headless:
                opts.add_argument("--headless=new")
            if optimize or headless:
                opts.add_argument("--blink-settings=imagesEnabled=false")
                opts.add_argument("--disable-notifications")
                opts.add_argument("--disable-gpu")
                opts.add_argument("--log-level=3")
                opts.add_argument("--disable-extensions")
            if profile_dir:
                profile_dir.mkdir(parents=True, exist_ok=True)
                opts.add_argument(f"--user-data-dir={profile_dir}")
                opts.add_argument("--profile-directory=Default")
            if browser == Browser.CHROMIUM:
                exe = _find_executable(Browser.CHROMIUM)
                if exe:
                    opts.binary_location = exe
            driver = webdriver.Chrome(options=opts, service=ChromeService(env=_clean_env()))

        elif browser == Browser.EDGE:
            opts = EdgeOptions()
            opts.page_load_strategy = "eager"
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            opts.add_argument("--window-size=1280,900")
            if headless:
                opts.add_argument("--headless=new")
            if optimize or headless:
                opts.add_argument("--blink-settings=imagesEnabled=false")
                opts.add_argument("--disable-notifications")
                opts.add_argument("--disable-gpu")
                opts.add_argument("--log-level=3")
            if profile_dir:
                profile_dir.mkdir(parents=True, exist_ok=True)
                opts.add_argument(f"--user-data-dir={profile_dir}")
                opts.add_argument("--profile-directory=Default")
            driver = webdriver.Edge(options=opts, service=EdgeService(env=_clean_env()))

        elif browser == Browser.FIREFOX:
            opts = FirefoxOptions()
            opts.page_load_strategy = "eager"
            if headless:
                opts.add_argument("--headless")
            if optimize or headless:
                opts.set_preference("permissions.default.image", 2)
                opts.set_preference("dom.webnotifications.enabled", False)
            if profile_dir:
                profile_dir.mkdir(parents=True, exist_ok=True)
                opts.add_argument("-profile")
                opts.add_argument(str(profile_dir))
            driver = webdriver.Firefox(options=opts, service=FirefoxService(env=_clean_env()))

        else:
            raise ValueError(f"Unsupported browser: {browser}")

        if browser in (Browser.CHROME, Browser.CHROMIUM, Browser.EDGE):
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
            )

        return driver
