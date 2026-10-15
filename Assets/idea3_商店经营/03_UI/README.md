# One More Diner · UI Management V2

这是独立的 UI 设计交付包，未修改任何游戏运行代码，也未覆盖 ui_management_v1。

- 双击 `index.html` 浏览 16 张流程稿、2 张设计板；点击缩略图可放大，方向键切换。
- `svg/`：1920×1080 原生可编辑 SVG，文案仍是 text 节点，背景为已有场景截图。
- `html/`：每屏可离线打开的内联 SVG 预览；`gallery.css` 为图库界面样式。
- `screens/`：与 SVG 对应的全分辨率 PNG。
- `assets/panels/`：12 个透明底纯背景面板／按钮／徽标，SVG 与 PNG 对应。
- `assets/icons/`：23 个透明底 64×64 原生矢量图标，SVG 与 PNG 对应。
- `manifest.json`：清单、尺寸、颜色和真实九宫格切片边距。
- `docs/`：流程、英文文案 CSV、技术交接。
- `qa/`：渲染与本地图库验证记录。
- `management_ui_v2_overview.png`：全套 18 张画布的联系表。

界面中所有文案为英文。用 Georgia Bold 和 Arial 系统字体，不复制或分发字体文件。PNG 用已安装的 Edge 生成，浏览器配置与临时文件均在本包 tmp/（D 盘）。

复现：运行 `idea3/tools/build_ui_management_v2.py`，然后运行本包 `render.cjs`，再运行一次生成器制作联系表。`render.cjs` 使用已安装 Edge 和 bundled Playwright，所有可写路径明确位于 D 盘。设计稿控制仅为示意，不承诺已经接入游戏。
