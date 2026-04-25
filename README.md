# drawio-to-visio

将 draw.io 流程图转换为 Microsoft Visio 可编辑的 SVG 格式。

## 问题背景

draw.io（现 diagrams.net）导出的 SVG 文件使用 `<foreignObject>` 元素嵌入 HTML 文本，Microsoft Visio 对此支持有限，导致导入后出现：
- 文字位置全部偏移
- 文本无法编辑

## 解决方案

本工具将 `foreignObject` 文本转换为标准 SVG `<text>` 元素，保留字体、字号、颜色、位置等样式信息，使 Visio 能够正确显示和编辑。

## 安装

### 依赖

- Python 3.7+
- lxml 库

```bash
pip install lxml
```

### draw.io

下载并安装 draw.io 桌面版：
- GitHub Releases: https://github.com/jgraph/drawio-desktop/releases

## 使用方法

### 1. 从 draw.io 导出 SVG

使用 draw.io CLI 导出：

```powershell
# Windows
& "C:\Program Files\draw.io\draw.io.exe" --export --format svg --output "output.svg" "input.drawio"
```

### 2. 运行修复脚本

```bash
python fix_svg_for_visio.py input.svg output-fixed.svg
```

或自动生成输出文件名（添加 `-fixed` 后缀）：

```bash
python fix_svg_for_visio.py input.svg
# 生成: input-fixed.svg
```

### 3. 导入 Visio

1. 打开 Microsoft Visio
2. 点击 **文件 → 打开**
3. 选择修复后的 SVG 文件
4. 保持默认转换选项，点击"确定"

**编辑提示**：导入后的 SVG 是一个组合对象，如需单独编辑某个元素：
- 右键点击图形 → **组合 → 取消组合**（或按 `Ctrl+Shift+U`）

## 技术细节

### 核心处理逻辑

1. 使用 `lxml` 解析 SVG XML（避免标准库 `xml.etree` 的 UTF-8 处理问题）
2. 遍历所有 `<switch>` 块中的 `<foreignObject>`
3. 提取文本内容、位置（x, y）、样式（字体、字号、颜色、对齐）
4. 创建 `<text>` 元素替换原 `<switch>` 块
5. 设置 `dominant-baseline="hanging"` 帮助 Visio 正确定位

### 位置计算

- **x**: margin-left + (width/2 for center alignment)
- **y**: padding-top
- **text-anchor**: start/center/end 对应 left/center/right 对齐

## 已知限制

- 复杂文本布局（多行、自动换行）可能无法完美还原
- 部分 CSS 样式（如 `light-dark()` 颜色函数）会被简化

## 替代方案

如果转换后仍有问题：

1. **PNG 底图法**：从 draw.io 导出 PNG，在 Visio 中作为底图，手动添加文本框
2. **Visio 重绘**：使用 Visio 原生形状重新绘制流程图

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。
