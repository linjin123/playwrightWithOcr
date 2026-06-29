import pytest
from pages.login import LoginPage
from pages.home import HomePage

def test_login_success(page):
    login_page = LoginPage(page)
    login_page.login("admin", "123456")

    # 验证登录成功，使用 OCR 检查“欢迎你”是否出现
    home_page = HomePage(page)
    assert home_page.is_welcome_displayed()  # 在 HomePage 中实现 OCR 检查

    # 可额外截图
    login_page.take_screenshot("login_result")