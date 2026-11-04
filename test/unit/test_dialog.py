import pytest
from pages.login import LoginPage
from pages.home import HomePage
from common.base import BasePage
from common.tool import Tools


def test_dialog(page):
    browser = BasePage(page)
    browser.navigate("https://tieba.baidu.com/")
    Tools.capture_baseline(page)
    browser.click_by_text("登录")
    Tools.diff_with_baseline(page)