import pytest
from utils.excel_reporter import generate_excel_report

if __name__ == "__main__":
    # 执行测试
    pytest.main(["-v", "tests/", "--tb=short"])

    # 收集测试结果（需要从 pytest 结果中提取），此处只示例
    # 实际可用 pytest-json 等插件导出结果
    test_results = [
        {"执行过程": "...", "预期结果": "...", "测试结果": "通过", "截图路径": "screenshots/step1.png"}
    ]
    generate_excel_report(test_results, [])