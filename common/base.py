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
from common.tool import Tools

class BasePage:
    def __init__(self, page: Page,redis_client=None, cache_ttl=3600):
        self.page = page
        self.ocr = paddleOCR()
        self.screenshot_dir = Path("screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.redis = config.redis
        # self.url = config.URL
        self.cache_ttl = cache_ttl
        self.state = {"container": None}

    def navigate(self,url):
        self.page.goto(url)
    def input_by_text(self,text):

        self._click_by_text(text)
        self.page.keyboard.insert_text(text)

    def click_by_icon(self, iconName,templatePath):
        Tools.capture_baseline(self.page)  # 前
        self._click_by_icon(iconName,templatePath, self.state["container"])
        self.state["container"] = Tools.diff_with_baseline(self.page)  # 后，结果留给下次
        print(f'popup_selector:{self.state["container"]}')
    def click_by_text(self,text):
          # 每次点击后更新，供下一次使用


        Tools.capture_baseline(self.page)  # 前
        self._click_by_text(text, self.state["container"])
        self.state["container"] = Tools.diff_with_baseline(self.page)  # 后，结果留给下次
        print(f'popup_selector:{self.state["container"]}')
        # _click.reset = lambda: state.update(container=None)
    def click_by_text_for_scroll(self,text):
          # 每次点击后更新，供下一次使用
        Tools.capture_baseline(self.page)  # 前
        self._click_by_text_for_scroll(text, self.state["container"])
        self.state["container"] = Tools.diff_with_baseline(self.page)  # 后，结果留给下次
        print(f'popup_selector:{self.state["container"]}')

    def _click_by_text_for_scroll(self, text,popup_selector=None, timeout=10, wait_before=0.5):
        """使用 OCR 点击包含特定文本的元素（无文本图标亦可通过图标特征文字辅助）,popup_selector为弹窗div属性"""
        # 等待页面稳定，networkidle 要求至少 500 毫秒内没有任何网络连接
        self.page.wait_for_load_state('networkidle')
        # 等待整个页面（包括图片、样式表等所有资源）加载完毕
        # self.page.wait_for_load_state(state='load')
        time.sleep(wait_before)
        #需要获取当前url
        # boxes = self._get_ocr_boxes_with_cache_for_scroll(popup_selector=popup_selector, force_refresh=False)
        #
        #
        # #在获取的文本内容画提取框，调试获取的文本
        # # self.screenshot(boxes,img_bgr,config.SCREENSHOTS_PATH)
        # image = self.page.screenshot(full_page=False)
        # img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        # center = self.ocr.find_text_center(boxes, text,img)
        # print(f'识别文本：{text}，坐标：{center}')
        # # 点击按钮
        # self._clickCenter(center, text)

        if popup_selector:
            popup = self.page.locator(popup_selector).locator(f"text={text}")
            popup.scroll_into_view_if_needed()
            popup.screenshot(path="perfect_template.png", animations="disabled")
            popup.click()
        else:
            popup = self.page.locator(f"text={text}")
            popup.scroll_into_view_if_needed()
            popup.screenshot(path="perfect_template.png", animations="disabled")
            popup.click()

    def _click_by_text(self, text,popup_selector=None, timeout=10, wait_before=0.5):
        """使用 OCR 点击包含特定文本的元素（无文本图标亦可通过图标特征文字辅助）,popup_selector为弹窗div属性"""
        # 等待页面稳定，networkidle 要求至少 500 毫秒内没有任何网络连接
        self.page.wait_for_load_state('networkidle')
        # 等待整个页面（包括图片、样式表等所有资源）加载完毕
        # self.page.wait_for_load_state(state='load')
        time.sleep(wait_before)
        # 判断有没有弹窗，有就点击弹窗
        # if popup_selector:
        #     boxes = self._get_popup_ocr_coords(self.page, self.page.get_by_role("dialog"))
        #     center = self.ocr.find_text_center(boxes, text)
        #     # 点击按钮
        #     self._clickCenter(center, text)
        #     print("点击弹窗")
        #需要获取当前url
        center = self._get_ocr_center_with_cache(text,popup_selector=popup_selector, force_refresh=False)


        #在获取的文本内容画提取框，调试获取的文本
        # self.screenshot(boxes,img_bgr,config.SCREENSHOTS_PATH)
        # image = self.page.screenshot(full_page=False)
        # img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        # center = self.ocr.find_text_center(boxes, text,img)
        print(f'识别文本：{text}，坐标：{center}')
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
    def _click_by_icon(self,iconName,templatePath=None,popup_selector=None,method=cv2.TM_CCOEFF_NORMED, timeout=10, wait_before=0.5):
        """使用 OCR 点击包含特定文本的元素（无文本图标亦可通过图标特征文字辅助）"""
        # 等待页面稳定
        # self.page.wait_for_load_state(state='load')
        self.page.wait_for_load_state(state='networkidle') #等待网络安静
        time.sleep(wait_before)

        center = self._get_icon_center_with_cache(popup_selector,iconName,templatePath,method, force_refresh=False)

        print(f'识别文本：{iconName}，坐标：{center}')
        #点击按钮
        self._clickCenter(center, iconName)



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

    def _get_cache_key(self, url,text,mark=None):
        """生成缓存的键，可以结合屏幕尺寸等"""
        raw_string = f"{url}{text}{mark}"
        # 简单使用 URL 的 MD5 作为键（避免过长）
        return f"{hashlib.md5(raw_string.encode()).hexdigest()}"

    def _get_ocr_center_with_cache(self,text,popup_selector,icon=False, force_refresh=False):
        """
        获取 OCR 结果，优先从 Redis 读取，若不存在则执行 OCR 并缓存。
        """
        # if self.redis is None:
        #     # 如果没有 Redis，直接走 OCR
        #     return self.ocr.get_text_boxes(img)

        url = self.page.url
        if popup_selector:
            cache_key = self._get_cache_key(url,text,"popup")
        else:
            cache_key = self._get_cache_key(url,text)


        if not force_refresh and self.redis:
            # 尝试从 Redis 获取
            cached = self.redis.get(cache_key)
            if cached:
                try:
                    data = pickle.loads(cached)
                    # 将 JSON 转换回 PaddleOCR 期望的格式？取决于后续使用方式。
                    # 如果后续只需坐标和文本，可以保留为列表字典格式，不转回原始格式。
                    # 这里假设返回的就是我们序列化后的格式，即 [{'box':..., 'text':..., 'confidence':...}]
                    return data
                except Exception as e:
                    print(f"缓存反序列化失败: {e}")


        # 3. 初始化截图变量与偏移量
        popup_x, popup_y = 0, 0
        dpr = self.page.evaluate("window.devicePixelRatio")  # 处理系统缩放
        # 判断是弹窗还是全屏，并截图
        if popup_selector:
            popup = self.page.locator(popup_selector)
            # 2. 获取弹窗的边界框 (CSS 像素)

            box = popup.bounding_box()
            if not box:
                raise Exception("无法获取弹窗位置")
            popup_x, popup_y = box["x"], box["y"]
            # 4. 截取弹窗的图
            screenshot_bytes = popup.screenshot(path="perfect_template.png",animations="disabled")
        else:
            screenshot_bytes = self.page.screenshot(full_page=False) # 截全屏
        # 5. 转为 OpenCV 图像
        img = cv2.imdecode(np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR)
        # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
        # 执行 OCR
        raw_result = self.ocr.get_text_boxes(img)  # 返回
        # print(f"raw_result:{raw_result}")
        #核心坐标转换（相对图像像素 -> 绝对视口 CSS 像素）
        for item in raw_result:
            x1, y1, x2, y2 = item["box"]

            # 除以 DPR 转回 CSS 尺寸，再加上弹窗的偏移量
            item["box"] = (
                popup_x + (x1 / dpr),
                popup_y + (y1 / dpr),
                popup_x + (x2 / dpr),
                popup_y + (y2 / dpr)
            )
        # # 序列化
        # serialized = self.orc.serialize_ocr_boxes(img)
        # 序列化存入 Redis
        center = self.ocr.find_icon_center(raw_result, text)
        self.redis.setex(cache_key, self.cache_ttl, pickle.dumps(center))
        return center

    # def _get_ocr_boxes_with_cache_for_scroll(self,popup_selector,icon=False, force_refresh=False):
    #     url = self.page.url
    #     if popup_selector:
    #         cache_key = popup_selector
    #     else:
    #         cache_key = self._get_cache_key(url)
    #
    #     if not force_refresh and self.redis:
    #         # 尝试从 Redis 获取
    #         cached = self.redis.get(cache_key)
    #         if cached:
    #             try:
    #                 data = json.loads(cached)
    #                 # 将 JSON 转换回 PaddleOCR 期望的格式？取决于后续使用方式。
    #                 # 如果后续只需坐标和文本，可以保留为列表字典格式，不转回原始格式。
    #                 # 这里假设返回的就是我们序列化后的格式，即 [{'box':..., 'text':..., 'confidence':...}]
    #                 return data
    #             except Exception as e:
    #                 print(f"缓存反序列化失败: {e}")
    #
    #     # 3. 初始化截图变量与偏移量
    #     popup_x, popup_y = 0, 0
    #     dpr = self.page.evaluate("window.devicePixelRatio")  # 处理系统缩放
    #     # 判断是弹窗还是全屏，并截图
    #     if popup_selector:
    #         popup = self.page.locator(popup_selector).locator(f"text={popup_selector}")
    #         popup.scroll_into_view_if_needed()
    #         popup.click()
    #     else:
    #         popup = self.page.locator(f"text={popup_selector}")
    #         popup.scroll_into_view_if_needed()
    #         popup.click()
    #     # 5. 转为 OpenCV 图像
    #     img = cv2.imdecode(np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR)
    #     # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
    #     # 执行 OCR
    #     raw_result = self.ocr.get_text_boxes(img)  # 返回
    #     print(f"raw_result:{raw_result}")
    #     # 核心坐标转换（相对图像像素 -> 绝对视口 CSS 像素）
    #     for item in raw_result:
    #         x1, y1, x2, y2 = item["box"]
    #
    #         # 除以 DPR 转回 CSS 尺寸，再加上弹窗的偏移量
    #         item["box"] = (
    #             popup_x + (x1 / dpr),
    #             popup_y + (y1 / dpr),
    #             popup_x + (x2 / dpr),
    #             popup_y + (y2 / dpr)
    #         )
    #     # # 序列化
    #     # serialized = self.orc.serialize_ocr_boxes(img)
    #     # 序列化存入 Redis
    #     if popup_selector:
    #         self.redis.setex(cache_key, self.cache_ttl, json.dumps(raw_result))
    #     else:
    #         self.redis.setex(cache_key, self.cache_ttl, json.dumps(raw_result))
    #     return raw_result
    def _get_icon_center_with_cache(self, popup_selector, iconName, templatePath, method,
                                   force_refresh=False):
        """
        获取 OCR 结果，优先从 Redis 读取，若不存在则执行 OCR 并缓存。缓存按键的唯一坐标
        """
        # if self.redis is None:
        #     # 如果没有 Redis，直接走 OCR
        #     return self.ocr.get_text_boxes(img)
        url = self.page.url
        if popup_selector:
            cache_key = self._get_cache_key(url,iconName,"popup")
        else:
            cache_key = self._get_cache_key(url,iconName,"icon")
        if not force_refresh and self.redis:
            # 尝试从 Redis 获取
            cached = self.redis.get(cache_key)
            if cached:
                try:
                    data = pickle.loads(cached)
                    # 将 JSON 转换回 PaddleOCR 期望的格式？取决于后续使用方式。
                    # 如果后续只需坐标和文本，可以保留为列表字典格式，不转回原始格式。
                    # 这里假设返回的就是我们序列化后的格式，即 [{'box':..., 'text':..., 'confidence':...}]
                    return data
                except Exception as e:
                    print(f"缓存反序列化失败: {e}")

        # 3. 初始化截图变量与偏移量
        popup_x, popup_y = 0, 0
        dpr = self.page.evaluate("window.devicePixelRatio")  # 处理系统缩放
        # 判断是弹窗还是全屏，并截图
        if popup_selector:
            popup = self.page.locator(popup_selector)
            # 2. 获取弹窗的边界框 (CSS 像素)
            box = popup.bounding_box()
            if not box:
                raise Exception("无法获取弹窗位置")
            popup_x, popup_y = box["x"], box["y"]
            # 4. 截取弹窗的图
            screenshot_bytes = popup.screenshot()

        else:
            screenshot_bytes = self.page.screenshot(full_page=False)  # 截全屏

            # locator = self.page.locator("//*[@class='iconify iconify--ep' and @data-icon='ep:grid']")
            # box = locator.bounding_box()
            # if box:
            #     print(f"网页真实逻辑尺寸: w={box['width']}, h={box['height']}")
            #     print(f"你的模板尺寸: w=26, h=28")
            #
            #     # 算出 X 和 Y 轴分别缩放了多少
            #     scale_x = box['width'] / 26
            #     scale_y = box['height'] / 28
            #     print(f"缩放比例: X轴 {scale_x} 倍, Y轴 {scale_y} 倍")
        # 转为 OpenCV 图像
        img = cv2.imdecode(np.frombuffer(screenshot_bytes, np.uint8), cv2.IMREAD_COLOR)
        # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
        templateImg = cv2.imdecode(np.fromfile(templatePath, np.uint8), cv2.IMREAD_COLOR)
        # 执行 cv2识别返回模板坐标
        raw_result = self.ocr.get_icon_boxes(iconName,img,templateImg,method)

        # 返回
        # print(f"raw_result:{raw_result}")
        # 核心坐标转换（相对图像像素 -> 绝对视口 CSS 像素）
        for item in raw_result:
            x1, y1, x2, y2 = item["box"]

            # 除以 DPR 转回 CSS 尺寸，再加上弹窗的偏移量
            item["box"] = (
                popup_x + (x1 / dpr),
                popup_y + (y1 / dpr),
                popup_x + (x2 / dpr),
                popup_y + (y2 / dpr)
            )
        # # 序列化
        # serialized = self.orc.serialize_ocr_boxes(img)
        # 序列化存入 Redis
        center = self.ocr.find_icon_center(raw_result, iconName)
        self.redis.setex(cache_key, self.cache_ttl, pickle.dumps(center))
        return center

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
            self._save_step_screenshot(f"click_{text}")
            raise Exception(f"未通过 OCR 找到icon: {text}")
