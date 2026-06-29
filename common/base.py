import time
from pathlib import Path
from playwright.sync_api import Page, expect
from common.paddleOCR import paddleOCR
import json
import hashlib
from config.config import *


class BasePage:
    def __init__(self, page: Page,redis_client=None, cache_ttl=3600):
        self.page = page
        self.ocr = paddleOCR()
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.redis = redis()
        self.cache_ttl = cache_ttl

    def navigate(self, url):
        self.page.goto(url)

    def click_by_text(self, text, timeout=10, wait_before=0.5):
        """使用 OCR 点击包含特定文本的元素（无文本图标亦可通过图标特征文字辅助）"""
        # 等待页面稳定
        self.page.wait_for_load_state('networkidle')
        time.sleep(wait_before)
        # 截图

        screenshot_bytes = self.page.screenshot(full_page=False)
        # 转为 PIL Image
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(screenshot_bytes))
        boxes = self.get_ocr_boxes_with_cache(img,text, force_refresh=False)
        center = self.ocr.find_text_center(boxes, text)
        if center:
            x, y = center
            # 点击坐标（注意视口偏移）
            self.page.mouse.click(x, y)
            self._save_step_screenshot(f"click_{text}")
            return True
        else:
            raise Exception(f"未通过 OCR 找到文本: {text}")

    def click_by_coordinate(self, x, y):
        self.page.mouse.click(x, y)

    def fill_input(self, selector, text):
        self.page.fill(selector, text)

    def _save_step_screenshot(self, step_name):
        """保存当前页面截图，供报告使用"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = self.screenshot_dir / f"{step_name}_{timestamp}.png"
        self.page.screenshot(path=str(filename))
        return filename

    def take_screenshot(self, name="screenshot"):
        return self._save_step_screenshot(name)

    def _get_cache_key(self, url):
        """生成缓存的键，可以结合屏幕尺寸等"""
        # 简单使用 URL 的 MD5 作为键（避免过长）
        return f"ocr_cache:{hashlib.md5(url.encode()).hexdigest()}"

    def get_ocr_boxes_with_cache(self,img,text, force_refresh=False):
        """
        获取 OCR 结果，优先从 Redis 读取，若不存在则执行 OCR 并缓存。
        """
        if self.redis is None:
            # 如果没有 Redis，直接走 OCR
            return self.ocr.get_text_boxes(img)

        url = self.page.url
        cache_key = self._get_cache_key(url)

        if not force_refresh:
            # 尝试从 Redis 获取
            cached = self.redis.get(cache_key)
            if cached:
                try:
                    data = json.loads(cached)
                    # 将 JSON 转换回 PaddleOCR 期望的格式？取决于后续使用方式。
                    # 如果后续只需坐标和文本，可以保留为列表字典格式，不转回原始格式。
                    # 这里假设返回的就是我们序列化后的格式，即 [{'box':..., 'text':..., 'confidence':...}]
                    return data
                except Exception as e:
                    print(f"缓存反序列化失败: {e}")

        # 执行 OCR
        raw_result = self.ocr.get_text_boxes(img)  # 假设返回原始格式
        # 序列化
        serialized = self.orc.serialize_ocr_boxes(raw_result)
        # 存入 Redis
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(serialized))
        return serialized