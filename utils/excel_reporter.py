import pandas as pd
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from pathlib import Path

def generate_excel_report(test_results, screenshot_paths):
    """
    test_results: list of dict，包含 '执行过程','预期结果','测试结果','截图路径' 等
    """
    df = pd.DataFrame(test_results)
    excel_file = "reports/test_report.xlsx"
    df.to_excel(excel_file, index=False, sheet_name="Sheet1")

    # 插入截图（假设截图列名为"截图"）
    wb = load_workbook(excel_file)
    ws = wb["Sheet1"]
    for idx, row in enumerate(test_results, start=2):  # 第1行是表头
        img_path = row.get('截图路径')
        if img_path and Path(img_path).exists():
            img = XLImage(img_path)
            img.width = 120
            img.height = 90
            cell = f"G{idx}"   # 假设截图在 G 列
            ws.add_image(img, cell)
    wb.save(excel_file)