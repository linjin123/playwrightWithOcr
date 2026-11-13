import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image
from config.config import *
class paddleOCR:
    def __init__(self, lang='ch', use_angle_cls=True):
        self.ocr = PaddleOCR(
        use_textline_orientation=False, # 水平文字建议关掉，减少干扰
        lang='ch',
        enable_mkldnn=False,
        text_det_limit_side_len=99999,  # 强制不缩小图片
        text_det_limit_type="max",
        use_doc_unwarping=False,# 按最长边算
        text_det_box_thresh=0.7
        )

    def get_text_boxes(self,image):
        """
        接收 PIL Image 或 numpy array（BGR），返回 OCR 结果列表：
        [ [ [x1,y1], [x2,y2], [x3,y3], [x4,y4] ], (text, confidence) ], ... ]
        """
        boxes = []
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        result = self.ocr.predict(image)

        if not result or not result[0]:
            return []
        # 过滤掉空结果

        # PaddleOCR 2.x
        # for line in result[0]:
        #     if line:
        #         box, (text, confidence) = line
        #         boxes.append({
        #             'box': box,          # 四个角坐标
        #             'text': text,
        #             'confidence': confidence
        #         })
        # PaddleOCR 3.x
        if not isinstance(result[0], dict):
            return boxes
        texts = result[0].get("rec_texts", [])
        scores = result[0].get("rec_scores", [])
        rects = result[0].get("rec_boxes", [])  # 优先用矩形框
        polys = result[0].get("rec_polys") or result[0].get("dt_polys", [])  # 备用：四点坐标

        for i, text in enumerate(texts):
            score = float(scores[i]) if i < len(scores) else 0.0

            # 优先取 rec_boxes
            if i < len(rects):
                box = tuple(map(float, rects[i]))  # [x1, y1, x2, y2]
            # elif i < len(polys):
            #     points = polys[i]
            #     xs = [p[0] for p in points]
            #     ys = [p[1] for p in points]
            #     box = (min(xs), min(ys), max(xs), max(ys))
            else:
                continue
            # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # cv2.putText(img, "图标", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
            # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
            boxes.append({
                "text": text,
                "box": box,
                "confidence": score
            })

        return boxes

    def get_icon_boxes(self,iconName, img,templateImg,method):
        boxes = []
        h, w = templateImg.shape[:2]
        # 转灰度
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(templateImg, cv2.COLOR_BGR2GRAY)

        # 提取边缘 (Canny)
        img_edge = cv2.Canny(img_gray, 50, 150)
        template_edge = cv2.Canny(template_gray, 50, 150)

        # 匹配边缘图
        result = cv2.matchTemplate(img_edge, template_edge, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 原始截图识别，图标需配合captrueIcon.py截取图标后使用

        # result = cv2.matchTemplate(img, templateImg, method)  # 返回
        # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)


        # 根据匹配方法确定最佳匹配位置
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            # if min_val < 0.7:
            top_left = min_loc
            match_val = min_val
        else:
            # if max_val > 0.6:
            top_left = max_loc
            match_val = max_val
        if top_left is None:
            raise ValueError(f"识别不到图标坐标，match_val={match_val}")
        x1, y1 = top_left
        x2 = x1 + w
        y2 = y1 + h
        box = x1, y1, x2, y2
        # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # cv2.putText(img, "图标", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
        boxes.append({
            "text": iconName,
            "box": box,
            "confidence": match_val
        })
        return boxes

    def find_text_center(self, boxes, target_text, img=None,threshold=0.7):
        """在图像中查找指定文本，返回其中心坐标 (x, y) 或 None"""
        # boxes = self.get_text_boxes(image)
        for item in boxes:
            if target_text in item['text'] and item['confidence'] >= threshold:
                # 计算中心坐标（使用矩形的近似中心）PaddleOCR 2.x
                # xs = [p[0] for p in item['box']]
                # ys = [p[1] for p in item['box']]
                # cx = int((min(xs) + max(xs)) / 2)
                # cy = int((min(ys) + max(ys)) / 2)
                # 计算中心坐标（使用矩形的近似中心）PaddleOCR 3.x
                x1, y1, x2, y2 =item['box']
                # x1, y1, x2, y2 = map(int, item['box'])
                # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # cv2.putText(img, "图标", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
                # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
                # print(f"四坐标：{item['box']}")
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                return (cx, cy)
        return None

    def find_icon_center(self, boxes, iconName):
        """在图像中查找指定文本，返回其中心坐标 (x, y) 或 None"""
        # boxes = self.get_text_boxes(image)
        for item in boxes:
            if iconName in item['text']:
                # 计算中心坐标（使用矩形的近似中心）PaddleOCR 2.x
                # xs = [p[0] for p in item['box']]
                # ys = [p[1] for p in item['box']]
                # cx = int((min(xs) + max(xs)) / 2)
                # cy = int((min(ys) + max(ys)) / 2)
                # 计算中心坐标（使用矩形的近似中心）PaddleOCR 3.x
                x1, y1, x2, y2 =item['box']
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                return (cx, cy)
        return None


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


if __name__ == '__main__':
    paddleOCR().get_text_boxes()