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
top_left = None
match_val = None
method = cv2.TM_CCOEFF_NORMED
text = "一级目录按钮"
img = cv2.imdecode(np.fromfile(r"C:\Users\linjin\PycharmProjects\playwrightWithOcr\modelPage\page.png", np.uint8), cv2.IMREAD_COLOR)
templateImg = cv2.imdecode(np.fromfile(r"C:\Users\linjin\PycharmProjects\playwrightWithOcr\modelPage\一级目录按钮.png", np.uint8), cv2.IMREAD_COLOR)
boxes = []
h, w = templateImg.shape[:2]
result = cv2.matchTemplate(img, templateImg, method)  # 返回
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
# 根据匹配方法确定最佳匹配位置
if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
    if min_val < 0.7:
        top_left = min_loc
        match_val = min_val
else:
    if max_val > 0.6:
        top_left = max_loc
        match_val = max_val
x1, y1 = top_left
x2 = x1 + w
y2 = y1 + h
# box = x1, y1, x2, y2
# boxes.append({
#     "text": iconName,
#     "box": box,
#     "confidence": match_val
# })
# return boxes
cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
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