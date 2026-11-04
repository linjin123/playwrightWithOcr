import os
import time
from pathlib import Path
from playwright.sync_api import Page, expect
from common.paddleOCR import paddleOCR
import json
import hashlib
from config import config
import pickle
import cv2
import numpy as np
from PIL import Image


class BasePage:
    def __init__(self, page: Page,redis_client=None, cache_ttl=3600):
        self.page = page
        self.ocr = paddleOCR()
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.redis = config.redis
        # self.url = config.URL
        self.cache_ttl = cache_ttl

    def navigate(self,url):
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
        img_bgr = cv2.imdecode(np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR)
        # 判断有没有弹窗，有就点击弹窗
        if self.page.get_by_role("dialog").is_visible() or len(self.page.context.pages) > 1:
            boxes = self._get_popup_ocr_coords(self.page, self.page.get_by_role("dialog"))
            center = self.ocr.find_text_center(boxes, text)
            # 点击按钮
            self._clickCenter(center, text)
            print("点击弹窗")
        #需要获取当前url
        boxes = self._get_ocr_boxes_with_cache(img,text, force_refresh=False)


        #在获取的文本内容画提取框，调试获取的文本
        self.screenshot(boxes,img_bgr,config.SCREENSHOTS_PATH)

        center = self.ocr.find_text_center(boxes, text)
        # 点击按钮
        self._clickCenter(center, text)

    def screenshot(self,boxes,img,output_dir="output"):
        if img is None:
            raise FileNotFoundError(f"图片numpy读取失败")

        h, w = img.shape[:2]
        # annotated = img.copy()
        for i, item in enumerate(boxes):
            x1, y1, x2, y2 = item["box"]
            # 边界保护，防止越界
            x1 = max(0, min(int(x1), w - 1))
            y1 = max(0, min(int(y1), h - 1))
            x2 = max(0, min(int(x2), w))
            y2 = max(0, min(int(y2), h))
            if x2 <= x1 or y2 <= y1 or len(item["text"]) >= 10:
                continue



            # 1. 在整图上画框
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 2. 裁剪并保存
            # crop = img[y1:y2, x1:x2]
            text = item["text"].replace("/", "_").replace("\\", "_")
            cv2.putText(img, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
            # 文件名去掉非法字符，只保留前 30 字符
            # safe_text = "".join(c for c in text if c.isalnum() or c in "._- ")[:30]
            # crop_name = f"{i:03d}_{text}.png"
            # cv2.imwrite(os.path.join(output_dir, crop_name), crop)

            # 3. 在整图上标注文本（可选，中文需额外处理）
            # cv2.putText 不支持中文，见文末说明

            # 保存带框的整图
        annotated_path = os.path.join(output_dir, "annotated.png")
        cv2.imwrite(annotated_path, img)
        print(f"带框整图已保存: {annotated_path}")
        print(f"共裁剪 {len(boxes)} 个文本区域到: {output_dir}/")
    def click_by_icon(self, text, timeout=10, wait_before=0.5):
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
        image = self._get_icon_boxes_with_cache(text)
        center = self.ocr.find_img_center(img,image)
        #点击按钮
        self._clickCenter(center, text)



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

    def _get_ocr_boxes_with_cache(self,img,text, force_refresh=False):
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
        raw_result = self.ocr.get_text_boxes(img)  # 返回
        # # 序列化
        # serialized = self.orc.serialize_ocr_boxes(img)
        # 序列化存入 Redis
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(raw_result))
        return raw_result

    def _get_icon_boxes_with_cache(self,text):
        # 读取 bytes
        template_bytes = self.redis.get(text)
        # 反序列化为 numpy 数组
        template = pickle.loads(template_bytes)
        return template

    def _get_popup_ocr_coords(self,page, popup_selector):
        popup = page.locator(popup_selector)
        bbox = popup.bounding_box()
        if not bbox:
            return []
        popup_x, popup_y = bbox["x"], bbox["y"]

        # 3. 获取设备像素比 (处理 Windows 125% / 150% 缩放或 Mac 视网膜屏)
        dpr = page.evaluate("window.devicePixelRatio")

        # 4. 仅对弹窗元素截图
        screenshot_bytes = popup.screenshot()

        # 5. 转为 OpenCV 图像
        img = cv2.imdecode(np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR)

        # 6. OCR 识别弹窗内容
        result = self.ocr.predict(img)
        res = result[0]
        texts = res.get("rec_texts", [])
        polys = res.get("dt_polys") or res.get("rec_polys", [])

        results = []
        for i, text in enumerate(texts):
            if i >= len(polys):
                continue

            points = polys[i]
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]

            # 这里的 x1, y1, x2, y2 是相对于弹窗截图的【物理像素】
            x1, y1 = min(xs), min(ys)
            x2, y2 = max(xs), max(ys)

            # 7. 坐标映射：物理像素 -> CSS 像素 -> 视口绝对坐标
            # (除以 DPR 转回 CSS 尺寸，再加上弹窗的偏移)
            css_x1 = x1 / dpr
            css_y1 = y1 / dpr
            css_x2 = x2 / dpr
            css_y2 = y2 / dpr

            abs_x1 = popup_x + css_x1
            abs_y1 = popup_y + css_y1
            abs_x2 = popup_x + css_x2
            abs_y2 = popup_y + css_y2

            # 计算中心点坐标（用于点击）
            center_x = (abs_x1 + abs_x2) / 2
            center_y = (abs_y1 + abs_y2) / 2

            results.append({
                "text": text,
                "abs_box": (abs_x1, abs_y1, abs_x2, abs_y2),
                "center": (center_x, center_y)
            })

        return results

    def _clickCenter(self,center,text):
        if center:
            x, y = center
            # 点击坐标（注意视口偏移）
            self.page.mouse.click(x, y)
            self._save_step_screenshot(f"click_{text}")
            return True
        else:
            raise Exception(f"未通过 OCR 找到icon: {text}")
