from PIL import Image, ImageDraw
import numpy as np, cv2
from paddleocr import PaddleOCR

# 造一张干净的大字中文图，排除"小字/背景"干扰
# test = Image.new("RGB", (600, 120), "white")
# result = ocr.ocr(image_path, cls=True)
# ImageDraw.Draw(test).text((20, 40), "中文测试ABC123", fill="black")
# test_np = cv2.cvtColor(np.array(test), cv2.COLOR_RGB2BGR)
# ocr = PaddleOCR(use_textline_orientation=True, lang='ch',enable_mkldnn=False)
ocr = PaddleOCR(
    use_textline_orientation=False, # 水平文字建议关掉，减少干扰
    lang='ch',
    enable_mkldnn=False,
    text_det_limit_side_len=99999,  # 强制不缩小图片
    text_det_limit_type="max",
    use_doc_unwarping=False,# 按最长边算
    text_det_box_thresh=0.7
)
boxes = []
img = cv2.imdecode(np.fromfile(r"C:\Users\linjin\Pictures\test.png", dtype=np.uint8), cv2.IMREAD_COLOR)
result = ocr.predict(img)
texts = result[0].get("rec_texts", [])
scores = result[0].get("rec_scores", [])
rects = result[0].get("rec_boxes", [])  # 优先用矩形框
polys = result[0].get("rec_polys") or result[0].get("dt_polys", [])  # 备用：四点坐标

for i, text in enumerate(texts):
    if i >= len(polys):
        continue
    score = float(scores[i]) if i < len(scores) else 0.0
    # points = polys[i]
    # if isinstance(points[0], (int, float, np.floating, np.integer)):
    #     points = np.array(points).reshape(-1, 2)
    # 优先取 rec_boxes
    # if i < len(rects):
    box = tuple(map(float, rects[i]))  # [x1, y1, x2, y2]


    # xs = [p[0] for p in points]
    # ys = [p[1] for p in points]
    # box = (min(xs), min(ys), max(xs), max(ys))

    boxes.append({
        "text": text,
        "box": box,
        "confidence": score
    })
# print(f"框内容：{boxes}")
for i, item in enumerate(boxes):
    x1, y1, x2, y2 = map(int, item["box"])
    # 边界保护，防止越界
    # x1 = max(0, min(int(x1), w - 1))
    # y1 = max(0, min(int(y1), h - 1))
    # x2 = max(0, min(int(x2), w))
    # y2 = max(0, min(int(y2), h))
    if x2 <= x1 or y2 <= y1 or item['confidence'] <= 0.7 or len(item["text"]) >= 10:
        continue

    # 1. 在整图上画框

    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # 2. 裁剪并保存
    crop = img[y1:y2, x1:x2]
    text = item["text"].replace("/", "_").replace("\\", "_")
    cv2.putText(img, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
    print(f"中文内容为：{text}")
    # Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
    # 文件名去掉非法字符，只保留前 30 字符
    # safe_text = "".join(c for c in text if c.isalnum() or c in "._- ")[:30]
    # crop_name = f"{i:03d}_{text}.png"
    # cv2.imwrite(os.path.join(output_dir, crop_name), crop)

    # 3. 在整图上标注文本（可选，中文需额外处理）
    # cv2.putText 不支持中文，见文末说明

    # 保存带框的整图
# annotated_path = os.path.join(output_dir, "annotated.png")
Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).show()
# cv2.imwrite(annotated_path, img)
# print("TEST rec_texts:", res['rec_texts'])
print("ocr.lang:", getattr(ocr, 'lang', 'N/A'))