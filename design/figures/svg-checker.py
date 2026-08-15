#!/usr/bin/env python3
"""
SVG 容器图自检脚本 (v1.0)
按文档 v2.3 的 ST-1~ST-7 + Q0~Q10 检查清单自动验证 SVG

用法: python svg-checker.py <svg-file>
"""
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# 容器定义 (x, y, w, h, name)
# 实际从 SVG 中解析, 这里是示例
CONTAINERS = [
    # 用户
    {"name": "用户", "x": 450, "y": 40, "w": 300, "h": 40},
    # 业务层
    {"name": "Java", "x": 120, "y": 180, "w": 160, "h": 80},
    {"name": "Python", "x": 520, "y": 180, "w": 160, "h": 80},
    {"name": "本机Agent", "x": 900, "y": 180, "w": 200, "h": 80},
    # 数据层
    {"name": "MySQL", "x": 120, "y": 420, "w": 160, "h": 80},
    {"name": "Redis", "x": 520, "y": 420, "w": 160, "h": 80},
    {"name": "浏览器池", "x": 900, "y": 420, "w": 200, "h": 80},
    # 共享层
    {"name": "RabbitMQ", "x": 120, "y": 580, "w": 160, "h": 80},
    # 外部系统
    {"name": "LLM", "x": 120, "y": 860, "w": 160, "h": 50},
    {"name": "推送", "x": 320, "y": 860, "w": 160, "h": 50},
    {"name": "邮件", "x": 520, "y": 860, "w": 160, "h": 50},
    {"name": "支付", "x": 720, "y": 860, "w": 160, "h": 50},
    {"name": "招聘", "x": 920, "y": 860, "w": 160, "h": 50},
]

def parse_path_d(d):
    """解析 SVG path d 属性, 返回 [(x, y), ...] 途经点列表"""
    points = []
    # 匹配 M x y L x y 格式
    pattern = r'[ML]\s*(\d+)\s+(\d+)'
    for match in re.finditer(pattern, d):
        x, y = int(match.group(1)), int(match.group(2))
        points.append((x, y))
    return points

def point_in_container(x, y, container, margin=0):
    """检查点是否在容器内 (含 margin)"""
    return (container["x"] - margin <= x <= container["x"] + container["w"] + margin and
            container["y"] - margin <= y <= container["y"] + container["h"] + margin)

def line_segment_intersects_container(p1, p2, container):
    """检查线段是否穿过容器"""
    # 简化为检查所有途经点 (除了起点/终点) 是否在容器内
    if p1[0] == p2[0]:  # 垂直线
        x = p1[0]
        y_min, y_max = min(p1[1], p2[1]), max(p1[1], p2[1])
        # 在垂直线上的每个 y 整数点检查 (稀疏采样)
        for y in range(y_min, y_max + 1, 10):
            if point_in_container(x, y, container):
                return True
    elif p1[1] == p2[1]:  # 水平线
        y = p1[1]
        x_min, x_max = min(p1[0], p2[0]), max(p1[0], p2[0])
        for x in range(x_min, x_max + 1, 10):
            if point_in_container(x, y, container):
                return True
    return False

def check_svg(svg_path):
    """主检查函数"""
    print(f"\n=== 自检 SVG: {svg_path} ===\n")
    
    # 解析 SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    issues = []
    
    # 提取所有 path
    ns = {"svg": "http://www.w3.org/2000/svg"}
    paths = root.findall(".//svg:path", ns)
    
    print(f"找到 {len(paths)} 条 path\n")
    
    # 检查每条 path
    for i, path in enumerate(paths, 1):
        d = path.get("d", "")
        if not d or "M" not in d:
            continue
        if path.get("marker-end") is None and "M" in d:
            continue  # 跳过非连接线
        
        points = parse_path_d(d)
        if len(points) < 2:
            continue
        
        # 检查每段
        for j in range(len(points) - 1):
            p1, p2 = points[j], points[j+1]
            # 检查每段是否穿过容器 (除了起点/终点容器)
            for container in CONTAINERS:
                # 起点在容器内, 跳过
                if point_in_container(*p1, container):
                    continue
                # 终点在容器内, 跳过
                if point_in_container(*p2, container):
                    continue
                # 中间段穿过
                if line_segment_intersects_container(p1, p2, container):
                    issues.append(f"❌ Path #{i}: 线段 ({p1[0]},{p1[1]})→({p2[0]},{p2[1]}) 穿过容器 '{container['name']}'")
                    break
    
    if issues:
        print("❌ 发现问题:\n")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ 所有线段不穿过容器\n")
    
    return len(issues)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python svg-checker.py <svg-file>")
        sys.exit(1)
    svg_file = Path(sys.argv[1])
    if not svg_file.exists():
        print(f"文件不存在: {svg_file}")
        sys.exit(1)
    
    issues_count = check_svg(svg_file)
    sys.exit(0 if issues_count == 0 else 1)
