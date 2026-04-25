#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 draw.io 导出的 SVG 文件，将 foreignObject 文本转换为 Visio 兼容的 <text> 元素。
使用 lxml 库确保 UTF-8 中文编码正确。

用法:
    python fix_svg_for_visio.py <input.svg> [output.svg]
    
    若未指定 output.svg，则生成 <input>-fixed.svg
"""

import re
import sys
import os
from lxml import etree


def parse_color(raw):
    """解析颜色，处理 light-dark() 等 CSS 函数"""
    if not raw:
        return '#000000'
    # 处理 light-dark(#color1, #color2) 取第一个
    m = re.search(r'light-dark\(\s*(#[0-9a-fA-F]{3,6})\s*,', raw)
    if m:
        return m.group(1)
    # 普通颜色值
    m = re.search(r'(#[0-9a-fA-F]{3,6})', raw)
    if m:
        return m.group(1)
    return '#000000'


def extract_text_info(switch_el, nsmap):
    """
    从 <switch> 元素中提取文本信息。
    返回 dict 或 None（如果没有 foreignObject）。
    """
    svg_ns = nsmap.get('svg', 'http://www.w3.org/2000/svg')
    xhtml_ns = 'http://www.w3.org/1999/xhtml'
    
    fo = switch_el.find('.//{%s}foreignObject' % svg_ns)
    if fo is None:
        return None

    # 获取 div 元素
    outer_div = fo.find('.//{%s}div' % xhtml_ns)
    if outer_div is None:
        return None

    outer_style = outer_div.get('style', '')

    # 提取位置信息
    padding_top = 0
    margin_left = 0
    width_val = 0

    m = re.search(r'padding-top:\s*(\d+)px', outer_style)
    if m:
        padding_top = int(m.group(1))

    m = re.search(r'margin-left:\s*(\d+)px', outer_style)
    if m:
        margin_left = int(m.group(1))

    m = re.search(r'width:\s*(\d+)px', outer_style)
    if m:
        width_val = int(m.group(1))

    # 找最内层的 div（包含文本）
    inner_div = outer_div.find('.//{%s}div' % xhtml_ns)
    if inner_div is None:
        return None

    # 跳过 font-size: 0 的中间层
    inner_style = inner_div.get('style', '')
    if 'font-size: 0' in inner_style or 'font-size:0' in inner_style:
        deeper = inner_div.find('.//{%s}div' % xhtml_ns)
        if deeper is not None:
            inner_div = deeper
            inner_style = inner_div.get('style', '')

    # 提取文本样式
    font_size = '12px'
    font_family = 'Helvetica'
    font_weight = 'normal'
    color = '#000000'
    text_align = 'center'

    m = re.search(r'font-size:\s*(\d+px)', inner_style)
    if m:
        font_size = m.group(1)

    m = re.search(r'font-family:\s*([^;"]+)', inner_style)
    if m:
        font_family = m.group(1).strip().split(',')[0].strip()

    m = re.search(r'font-weight:\s*(\w+)', inner_style)
    if m:
        font_weight = m.group(1)

    m = re.search(r'color:\s*([^;"]+)', inner_style)
    if m:
        color = parse_color(m.group(1))

    m = re.search(r'text-align:\s*(\w+)', inner_style)
    if m:
        text_align = m.group(1)

    # 获取文本内容
    text = ''.join(inner_div.itertext()).strip()

    if not text:
        return None

    # 确定文本锚点
    text_anchor = 'middle'
    if text_align == 'left':
        text_anchor = 'start'
    elif text_align == 'right':
        text_anchor = 'end'

    # 计算实际 x 坐标
    if text_anchor == 'middle' and width_val > 0:
        x = margin_left + width_val / 2
    elif text_anchor == 'end' and width_val > 0:
        x = margin_left + width_val
    else:
        x = margin_left

    y = padding_top

    return {
        'text': text,
        'x': x,
        'y': y,
        'font_size': font_size,
        'font_family': font_family,
        'font_weight': font_weight,
        'color': color,
        'text_anchor': text_anchor,
    }


def fix_svg(input_path, output_path):
    """修复 SVG 文件"""
    
    # 读取原始 SVG
    with open(input_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # 解析 XML
    parser = etree.XMLParser(remove_blank_text=False, encoding='utf-8')
    tree = etree.fromstring(svg_content.encode('utf-8'), parser)
    root = tree

    # 定义命名空间
    nsmap = {'svg': 'http://www.w3.org/2000/svg'}
    svg_ns = nsmap['svg']

    # 找到所有 switch 元素
    switches = root.findall('.//{%s}switch' % svg_ns)
    print(f"Found {len(switches)} switch elements")

    converted = 0
    for switch in switches:
        info = extract_text_info(switch, nsmap)
        if info is None:
            continue

        # 获取 switch 的父元素
        parent = switch.getparent()

        # 创建新的 <text> 元素
        text_el = etree.SubElement(parent, '{%s}text' % svg_ns)
        text_el.text = info['text']
        text_el.set('x', str(info['x']))
        text_el.set('y', str(info['y']))
        text_el.set('font-size', info['font_size'])
        text_el.set('font-family', info['font_family'])
        text_el.set('font-weight', info['font_weight'])
        text_el.set('fill', info['color'])
        text_el.set('text-anchor', info['text_anchor'])
        text_el.set('pointer-events', 'none')
        text_el.set('dominant-baseline', 'hanging')

        # 删除原来的 switch 元素
        parent.remove(switch)
        converted += 1

    print(f"Converted {converted} text elements")

    # 序列化输出
    result = etree.tostring(
        root, 
        encoding='utf-8', 
        xml_declaration=True,
        doctype='<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
        pretty_print=False
    )

    # 写入文件
    with open(output_path, 'wb') as f:
        f.write(result)

    print(f"Fixed SVG written to: {output_path}")
    return converted


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_svg_for_visio.py <input.svg> [output.svg]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # 自动生成输出路径
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}-fixed{ext}"
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    fix_svg(input_path, output_path)


if __name__ == '__main__':
    main()
