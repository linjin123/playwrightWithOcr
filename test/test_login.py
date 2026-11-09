import time

import pytest
from pages.login import LoginPage
from pages.home import HomePage
from common.base import BasePage

def test_login_success(page):
    browser = BasePage(page)
    browser.navigate("https://10.235.2.96:31080/")
    # page.wait_for_timeout(2000)
    # Tools.capture_baseline(page)
    browser.click_by_text("任务中心")
    browser.click_by_text("导入任务")