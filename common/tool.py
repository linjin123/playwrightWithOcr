#已调试完，可以基本完美适配识别弹窗
from typing import Any, Dict, List, Optional
from playwright.sync_api import Page, sync_playwright

class Tools:

  def capture_baseline(
          page: Page,
          grid: int = 24,
          var_name: str = "__base"
  ):
    _JS_CAPTURE_BASELINE = r"""
      ({ G, varName}) => {
        const vw = innerWidth, vh = innerHeight, out = [];
        for (let i = 1; i < G; i++) for (let j = 1; j < G; j++)
          out.push(document.elementFromPoint(vw * i / G, vh * j / G));
        window[varName] = out;
      }
      """
    """
    采样页面视口 grid×grid 网格点上的元素，作为“基准”。

    对应原始 JS：
        window.__base = (() => { ... elementFromPoint ... })();
        console.log('基准已存，现在手动触发弹窗');

    :param page:      Playwright 的 Page 对象（sync / async 均可用，见文末说明）
    :param grid:      网格数，原代码是 24
    :param var_name:  在 window 上保存原始节点的变量名，默认 "__base"
    :param describe:  True 返回元素描述列表；False 只返回采样点数量
    :return:          元素描述列表（可序列化）或采样点数量
    """
    # 等待整个页面（包括图片、样式表等所有资源）加载完毕
    page.wait_for_load_state(state='networkidle')
    page.evaluate(
      _JS_CAPTURE_BASELINE,
      {"G": grid, "varName": var_name},
    )
    print("基准已存，现在手动触发弹窗")


  def diff_with_baseline(
            page: Page,
            grid: int = 24,
            var_name: str = "__base",
    ) -> "popup_selector":
    # 可选：弹窗出现后，对比基准找出“被新元素遮挡”的采样点 / 弹窗元素
    _JS_DIFF = r"""
      ({ G, baseVar }) => {
        const vw = innerWidth, vh = innerHeight, base = window.__base;
        if (!base) return console.warn('先跑第一步存基准');

        // ---- 1. 采样 + 差分 ----
        const changed = []; let k = 0;
        for (let i = 1; i < G; i++) for (let j = 1; j < G; j++) {
          const el = document.elementFromPoint(vw * i / G, vh * j / G);
          if (el !== base[k]) changed.push({ x: vw * i / G, y: vh * j / G, el });
          k++;
        }
        const ratio = changed.length / k;

        // ---- 2. 祖先链计数 ----
        const freq = new Map();
        for (const c of changed) {
          let cur = c.el;
          let depth = 0;
          while (cur && cur !== document.body && cur !== document.documentElement && depth < 10) {
            freq.set(cur, (freq.get(cur) || 0) + 1);
            cur = cur.parentElement;
            depth++;
          }
        }

        // ---- 3. 筛选候选 ----
        let candidates = [];

        for (const [el, hits] of freq.entries()) {
          if (!el.getBoundingClientRect) continue;
          const r = el.getBoundingClientRect();
          if (r.width < 10 || r.height < 10) continue; // 排除极小节点
      
          const cover = (r.width * r.height) / (vw * vh);
          const cls = el.className ? el.className.toString() : '';
          const tagName = el.tagName.toLowerCase();
          
          // 排除明显不是弹窗的全屏根节点
          if (cover > 0.99 || tagName === 'body' || tagName === 'html') continue;
      
          // 获取计算样式（适度牺牲一点点性能换取极度准确）
          const style = window.getComputedStyle(el);
          const zIndex = parseInt(style.zIndex) || 0;
          const position = style.position;
      
          // ======== 核心打分逻辑 ========
          let score = hits; // 基础分：命中的网格点数
          
          
          // 2. 层级与定位特征 (悬浮元素的标配)
          if (zIndex > 50) score += 300;
          if (position === 'fixed' || position === 'absolute') score += 200;
          
          // 3. 面积特征 (全屏遮罩或大面积弹窗)
          if (cover > 0.8) score += 100;
          // 4. 惩罚项：左侧固定导航栏 (贴左边且很高)
          const cx = r.left + r.width / 2;
          if (cx < vw * 0.2 && r.height > vh * 0.8) {
              score -= 1000;
          }
      
      
          candidates.push({ el, hits, cover, score, cls, r });
        }
        // 按得分从高到低排序
        candidates.sort((a, b) => b.score - a.score);
        
        let bestCandidate = candidates[0];
        let dialog = bestCandidate ? bestCandidate.el : null;
      
      
      
        const mask = candidates.find(c => c.cover >= 0.9 && c.score > 0)?.el || null;
        const isModal = !!dialog;
      
        // ---- 5. 输出结果 ----
        console.log(`变化率 ${changed.length}/${k} = ${(ratio * 100).toFixed(1)}%`);
        console.table(candidates.slice(0, 8).map(c => ({
          el: (c.cls || c.el.tagName).toString().slice(0, 40),
          hits: c.hits,
          cover: +c.cover.toFixed(2),
          score: c.score,
        })));
        
        console.log('mask  :', mask);
        console.log('dialog:', dialog);
        console.log('isModal:', isModal);

        //window.__diff2 = { changed, candidates, mask, dialog, ratio, isModal };

        if (!dialog) return null;
        const uniqueId = 'pw-popup-' + Date.now();
        dialog.setAttribute('data-pw-popup-id', uniqueId);
        
        // 返回一个标准的 CSS 选择器字符串
        return `[data-pw-popup-id="${uniqueId}"]`;
        
      }
      """
    # 等待整个页面（包括图片、样式表等所有资源）加载完毕
    page.wait_for_load_state(state='load')
    cssSelector = page.evaluate(_JS_DIFF, {"G": grid, "baseVar": var_name})
    # print(f"popup_selector1:{cssSelector}")
    return cssSelector


# if __name__ == "__main__":
#   with sync_playwright() as p:
#     browser = p.chromium.launch(headless=False)
#     page = browser.new_page(viewport={"width": 1280, "height": 800})
#
#     page.goto("https://tieba.baidu.com/", wait_until="domcontentloaded")
#     capture_baseline(page)
