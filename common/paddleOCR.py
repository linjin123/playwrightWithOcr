import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image
from config.config import *
class paddleOCR:
    def __init__(self, lang='ch', use_angle_cls=True):
        self.ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, show_log=False)

    def get_text_boxes(self, image):
        """
        接收 PIL Image 或 numpy array（BGR），返回 OCR 结果列表：
        [ [ [x1,y1], [x2,y2], [x3,y3], [x4,y4] ], (text, confidence) ], ... ]
        """
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        result = self.ocr.ocr(image, cls=True)
        if not result or not result[0]:
            return []
        # 过滤掉空结果
        boxes = []
        for line in result[0]:
            if line:
                box, (text, confidence) = line
                boxes.append({
                    'box': box,          # 四个角坐标
                    'text': text,
                    'confidence': confidence
                })
        return boxes

    def find_text_center(self, boxes, target_text, threshold=0.7):
        """在图像中查找指定文本，返回其中心坐标 (x, y) 或 None"""
        # boxes = self.get_text_boxes(image)
        for item in boxes:
            if target_text in item['text'] and item['confidence'] >= threshold:
                # 计算中心坐标（使用矩形的近似中心）
                xs = [p[0] for p in item['box']]
                ys = [p[1] for p in item['box']]
                cx = int((min(xs) + max(xs)) / 2)
                cy = int((min(ys) + max(ys)) / 2)
                return (cx, cy)
        return None

    def find_img_center(self,img, template_path=TEMPLATE_PATH, method=cv2.TM_CCOEFF_NORMED, threshold=0.8, debug=True):
        # 3. 截图并让模型预测
        boxes = []
        # 4. 遍历所有检测到的图标
        # img = cv2.imread(img)
        print(f"路径: {template_path}")
        template = cv2.imread(template_path)  # 小图（图标）
        if img is None or template is None:
            print("图片读取失败，请检查路径")
            return

        h, w = template.shape[:2]  # 模板的高度和宽度

        # 2. 执行模板匹配
        result = cv2.matchTemplate(img, template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 3. 根据匹配方法确定最佳匹配位置
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            # 平方差匹配：值越小越好
            top_left = min_loc
            match_val = min_val
        else:
            # 相关系数匹配：值越大越好
            top_left = max_loc
            match_val = max_val
        x1, y1 = top_left
        x2 = x1 + w
        y2 = y1 + h
        # boxes.append([x, y, x + w, y + h])
        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
        return (center_x,center_y)

    def serialize_ocr_boxes(ocr_result):
        """
        将 OCR 结果转换为可 JSON 序列化的格式。
        ocr_result 是 PaddleOCR 返回的列表：
        [ [[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence) ], ... ]
        """
        serializable = []
        for line in ocr_result:
            if not line:
                continue
            box, (text, confidence) = line
            # 将坐标数组转换为普通列表
            box_list = [[int(x), int(y)] for x, y in box]
            serializable.append({
                'box': box_list,
                'text': text,
                'confidence': confidence
            })
        return serializable