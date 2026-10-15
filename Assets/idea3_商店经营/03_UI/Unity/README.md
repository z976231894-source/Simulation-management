# UI V2 - 用现有素材装配界面

本目录把 `03_UI` 里的 12 个面板切片、23 个图标、4 张场景底图和 18 张设计稿，
装配成 Unity 里可直接使用的 uGUI 预制体。不新增任何美术资源。

## 怎么跑

Unity 菜单 `Tools > ONE MORE DINER > UI V2 > Screens`，然后：

1. `1. Fix sprite import settings` —— 把设计包里 39 张 PNG 从默认纹理改成
   Sprite（Single / FullRect / 不压缩 / Alpha Is Transparency），并按
   `manifest.json` 的 nine_slice 写入九宫格边距。只改 `.meta` 导入设置，不动图片。
2. `2. Assemble prefabs` —— 产出 `Unity/Prefabs/`：18 个界面预制体
   （16 个正式界面 + 2 张设计板）和 `UI_V2_ScreenHost.prefab`
   （Canvas + CanvasScaler 1920×1080 / match 0.5）。

窗口里还有 `Preview in scene`（把某一屏摆进当前场景直接看）和 `Validate`。

## 数据怎么来的

```
Source/export_layout_for_unity.py     svg/*.svg  →  Layout/ui_layout.json
Editor/ManagementUiBuilder.cs         JSON + 现有素材 → Prefabs/*.prefab
Runtime/ManagementUiAssembler.cs      真正建层级的代码（Editor 和运行时共用）
Runtime/ManagementUiHost.cs           多屏切换（只有 Show/Next/Previous，不接管按键）
```

每个绘制项都指向现有素材：面板切片（Sliced）、图标、底图，或 Unity 内建的
`UI/Skin/Background.psd`（纯色块）、`UI/Skin/Knob.psd`（实心圆）。

圆角不是靠新增切片对齐的：`Image.pixelsPerUnitMultiplier` 会把九宫格边距按
`(面板圆角+3)/(设计圆角+3)` 缩放，所以 `panel_paper`(r24) 也能画出 r16 的圆角，
选片只按颜色和描边决定。229 个矩形用到了这个校正。

## 已知偏差（需要你接手的地方）

- **颜色**：tint 是乘法，只能压暗。333 个圆角矩形里有 38 个的设计色比所选面板底色更亮，
  会渲染得略暗（例如 #FFF9ED 用 panel_soft 底 → #E9EADB）。其余颜色按设计值精确还原。
- **渐变／棋盘**：12 处（1 个 hero 渐变 + 11 条顶部棋盘带）被压成单色块。
  要精确就得给它们做材质或贴图。
- **圆形**：14 个圆里有 13 个按实心圆画，描边丢失；1 个纯描边圆（主菜单徽章的 r70 内圈）
  无法用现有素材表达，已跳过并在日志里标出。
- **投影**：45 处用 uGUI `Shadow` 组件（硬边），设计稿是 20px 高斯模糊的软阴影。
- **文字**：工程里目前没有 TMP 字体资源（字体包已移到 `D:\AAAWork\UI_V2_work`），
  所以走 Unity 内建字体。把 `TextMesh Pro` 目录放回 `Assets/` 后会自动改用
  LiberationSans SDF；字距（letter-spacing）只在 TMP 路径生效。
  文字按设计基线 + 锚点 + 字体自身 ascent 摆放，与 SVG 可能有细微垂直位移。
- **不含交互**：所有 Graphic 都是 `raycastTarget = false`，没有 Button／事件／本地化／
  运行时数据绑定，这一层要按玩法接。
