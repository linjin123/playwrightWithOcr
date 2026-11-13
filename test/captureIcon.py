from common.base import BasePage
from config import config

def test_capture_icon(page):
    browser = BasePage(page)
    browser.navigate("https://10.235.2.96:31080/")
    page.wait_for_timeout(5000)
# 1. 找到那个按钮的定位器
    locator = page.locator("//*[contains(@class, 'el-table__inner-wrapper')]") # 比如 ".el-icon-more"

    # 2. 让 Playwright 截取这个元素的图，并直接保存作为未来的模板
    locator.screenshot(path="perfect_template.png")