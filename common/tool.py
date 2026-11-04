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

        // ---- 2. 祖先链计数（核心改动）----
        const freq = new Map();
        for (const c of changed) {
          let cur = c.el;
          while (cur && cur !== document.body && cur !== document.documentElement) {
            freq.set(cur, (freq.get(cur) || 0) + 1);
            cur = cur.parentElement;
          }
        }

        // ---- 3. 筛选候选 ----
        const candidates = [...freq.entries()]
          .filter(([, n]) => n < changed.length)      // 排除包含所有点的根容器（如 #app）
          .map(([el, n]) => {
            const r = el.getBoundingClientRect();
            const cover = (r.width * r.height) / (vw * vh);
            const cx = r.left + r.width / 2;
            const cy = r.top + r.height / 2;
            const centered = Math.abs(cx - vw / 2) < vw * 0.25
                          && Math.abs(cy - vh / 2) < vh * 0.25;
            const interactive = el.querySelectorAll(
              'button,input,textarea,select,[role=button],[tabindex],a[href]'
            ).length;
            const hasText = (el.innerText || '').trim().length > 0;
            return { el, n, cover, centered, interactive, hasText };
          })
          .filter(c => c.cover > 0.03 && c.cover < 0.98);   // 排除过大/过小

        // ---- 4. 分类 ----
        const mask = candidates
          .filter(c => c.cover >= 0.9)
          .sort((a, b) => b.n - a.n)[0]?.el || null;

        const dialog = candidates
          .filter(c => c.centered && (c.interactive >= 1 || c.hasText))
          .sort((a, b) => b.n - a.n)[0]?.el || null;

        const isModal = !!(mask || dialog);

        // ---- 5. 输出 ----
        # console.log(`变化率 ${changed.length}/${k} = ${(ratio * 100).toFixed(1)}%`);
        console.table(candidates.slice(0, 8).map(c => ({
          el: (c.el.className || c.el.tagName).toString().slice(0, 45),
          hits: c.n,
          cover: +c.cover.toFixed(2),
          centered: c.centered,
          interactive: c.interactive,
          hasText: c.hasText,
        })));
        console.log('mask  :', mask);
        console.log('dialog:', dialog);
        console.log('isModal:', isModal);

        # window.__diff2 = { changed, candidates, mask, dialog, ratio, isModal };

        return dialog;
        
      }
      """
    return page.evaluate(_JS_DIFF, {"G": grid, "baseVar": var_name})
    print(f"dialog div:{str(page.evaluate(_JS_DIFF, {"G": grid, "baseVar": var_name}))}")

# if __name__ == "__main__":
#   with sync_playwright() as p:
#     browser = p.chromium.launch(headless=False)
#     page = browser.new_page(viewport={"width": 1280, "height": 800})
#
#     page.goto("https://tieba.baidu.com/", wait_until="domcontentloaded")
#     capture_baseline(page)
