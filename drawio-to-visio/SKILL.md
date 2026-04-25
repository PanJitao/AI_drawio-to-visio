---
name: drawio-to-visio
description: 将 draw.io 流程图导出为 Visio 兼容的 SVG 格式。draw.io 默认导出的 SVG 使用 foreignObject 渲染文本，Visio 无法正确解析导致文字位置偏移。本技能通过将 foreignObject 转换为标准 SVG text 元素，解决 Visio 导入时的文本显示问题。当用户需要将 draw.io 流程图导入 Microsoft Visio 编辑时使用。
---

# Draw.io to Visio SVG 转换

将 draw.io 流程图转换为 Visio 可编辑的 SVG 格式。

## 问题背景

draw.io 导出的 SVG 使用 `<foreignObject>` 元素嵌入 HTML 文本，Visio 对此支持有限，导致：
- 文字位置全部偏移
- 文本无法编辑

## 解决方案

将 `foreignObject` 文本转换为标准 SVG `<text>` 元素，保留字体、字号、颜色、位置等样式。

## 使用流程

### 步骤 1：定位 draw.io

**自动检测**（优先尝试）：
- 检查常见安装路径：
  - `C:\Program Files\draw.io\draw.io.exe`
  - `C:\Program Files (x86)\draw.io\draw.io.exe`
  - `D:\draw.io\ANZHUANG\draw.io.exe`
  - `%LOCALAPPDATA%\Programs\draw.io\draw.io.exe`

**若未找到，询问用户**：
> "请提供 draw.io 的安装路径，或告诉我您下载安装的位置。"

**若用户未安装**：
> "您需要先安装 draw.io。下载地址：https://github.com/jgraph/drawio-desktop/releases
> 请下载并安装后，告诉我安装位置，或我自己会尝试查找。"

用户安装后，重新执行自动检测。

### 步骤 2：导出 SVG

使用找到的 draw.io CLI 将 `.drawio` 文件导出为 SVG：

```powershell
& "<draw.io路径>" --export --format svg --output "<输出.svg>" "<输入.drawio>"
```

### 步骤 3：运行修复脚本

使用 `scripts/fix_svg_for_visio.py` 处理导出的 SVG：

```powershell
python "<skill路径>/scripts/fix_svg_for_visio.py" "<输入.svg>" "<输出-fixed.svg>"
```

### 步骤 4：指导用户导入 Visio

**操作步骤**：
1. 打开 Microsoft Visio
2. 点击 **文件 → 打开**
3. 选择修复后的 SVG 文件（如 `crm-sales-flow-fixed.svg`）
4. 在弹出的"转换"对话框中，选择适当的选项（通常保持默认）
5. 点击"确定"完成导入

**导入后编辑**：
- 导入后的 SVG 是一个**组合对象**（整体）
- 若需要单独微调某个元素：
  1. **右键**点击图形
  2. 选择 **组合 → 取消组合**（或按 `Ctrl+Shift+U`）
  3. 现在可以单独选中、移动、编辑各个元素

**导入后检查**：
- 文本是否正确显示
- 文字位置是否准确
- 是否可以编辑文本

**若仍有问题**：
- 尝试 **PNG 底图法**：导出 PNG 作为底图，手动添加文本框
- 或 **Visio 重绘**：使用 Visio 原生形状重新绘制

## 脚本说明

### `scripts/fix_svg_for_visio.py`

**功能**：解析 SVG，将 `<foreignObject>` 转换为 `<text>` 元素。

**依赖**：`lxml` 库（`pip install lxml`）

**处理方式**：
1. 解析 SVG XML（使用 lxml，避免标准库 xml.etree 的 UTF-8 问题）
2. 遍历所有 `<switch>` 块中的 `<foreignObject>`
3. 提取文本内容、位置（x, y）、样式（字体、字号、颜色、对齐）
4. 创建 `<text>` 元素替换原 `<switch>` 块
5. 设置 `dominant-baseline="hanging"` 帮助 Visio 定位

**位置计算**：
- x = margin-left + (width/2 for center alignment)
- y = padding-top
- text-anchor: start/center/end 对应 left/center/right 对齐

## 已知限制

- 复杂文本布局（多行、自动换行）可能无法完美还原
- 部分 CSS 样式（如 light-dark() 颜色函数）会被简化
