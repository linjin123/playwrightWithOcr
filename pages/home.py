from common.base import BasePage

class HomePage(BasePage):
    def is_welcome_displayed(self):
        # 用 OCR 检测“欢迎你”文本是否存在
        self.page.url
        screenshot = self.page.screenshot()
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(screenshot))
        center = self.ocr.find_text_center(img, "欢迎你")
        return center is not None