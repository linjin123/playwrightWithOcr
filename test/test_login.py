import time

import pytest
from pages.login import LoginPage
from pages.home import HomePage
from common.base import BasePage
from config import config

def test_login_success(page):
    browser = BasePage(page)
    browser.navigate("https://10.235.2.96:31080/")
    page.wait_for_timeout(5000)
    # Tools.capture_baseline(page)

    browser.click_by_icon("一级目录按钮",f"{config.TEMPLATE_PATH}/一级目录按钮.png")
    browser.click_by_text("智能运维")
    # browser.page.get_by_text("任务中心", exact=True).click()
    browser.click_by_text("终端管理")