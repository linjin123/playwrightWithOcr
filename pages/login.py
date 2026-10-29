from common.base import BasePage
from config import config
class LoginPage(BasePage):

    def login(self, username, password):
        self.navigate(config.URL)
        # 使用 Playwright 定位器（有文本标签时优先）
        self.click_by_text("登录")
        # self.page.fill("#username", username)
        # self.page.fill("#password", password)
        # 如果“提交”按钮无文本，可用 OCR 点击
        self.click_by_text("账号密码登录")        # 通过 OCR 定位
        # 或者通过传统选择器：self.page.click("button[type='submit']")