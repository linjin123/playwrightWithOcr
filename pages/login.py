from common.base import BasePage
from config.config import *
class LoginPage(BasePage):

    def login(self, username, password):
        self.navigate(URL)
        # 使用 Playwright 定位器（有文本标签时优先）
        self.page.fill("#username", username)
        self.page.fill("#password", password)
        # 如果“提交”按钮无文本，可用 OCR 点击
        self.click_by_text("提交")        # 通过 OCR 定位
        # 或者通过传统选择器：self.page.click("button[type='submit']")