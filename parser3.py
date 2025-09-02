import re
import csv

def extract_test_data(log_file):
    # 精确匹配每个测试块的完整模式
    pattern = re.compile(
        r'Run embedding with queries .*?, (\d+) users.*?'
        r'===== 请求统计结果 =====.*?'
        r'总请求数: (\d+).*?'
        r'成功率: ([\d.]+)%.*?'
        r'QPS: ([\d.]+).*?'
        r'总耗时: ([\d.]+) 秒.*?'
        r'===== First Chunk 统计 =====.*?'
        r'平均值: ([\d.]+)s.*?'
        r'中位数: ([\d.]+)s.*?'
        r'P90: ([\d.]+)s.*?'
        r'P95: ([\d.]+)s.*?'
        r'===== Question Length 统计 =====.*?'
        r'最小值: (\d+).*?'
        r'最大值: (\d+).*?'
        r'平均值: ([\d.]+)',
        re.DOTALL
    )

    test_data = []

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
        matches = pattern.finditer(content)

        for match in matches:
            test_data.append({
                'Users': int(match.group(1)),
                'TotalRequests': int(match.group(2)),
                'SuccessRate': float(match.group(3)),
                'QPS': float(match.group(4)),
                'TotalTime': float(match.group(5)),
                'AvgLatency': float(match.group(6)),
                'MedianLatency': float(match.group(7)),
                'P90Latency': float(match.group(8)),
                'P95Latency': float(match.group(9)),
                'MinLength': int(match.group(10)),
                'MaxLength': int(match.group(11)),
                'AvgLength': float(match.group(12))
            })

    return test_data

def write_raw_to_csv(test_data, output_file):
    headers = [
        'Users', 'TotalRequests', 'SuccessRate(%)', 'QPS', 'TotalTime(s)',
        'AvgLatency(s)', 'MedianLatency(s)', 'P90Latency(s)', 'P95Latency(s)',
        'MinLength', 'MaxLength', 'AvgLength'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(test_data)

if __name__ == "__main__":
    log_file = "tripe.log"  # 替换为实际日志路径
    output_csv = "raw_performance_data.csv"

    print("正在提取日志数据...")
    data = extract_test_data(log_file)

    if not data:
        print("错误：未找到有效测试数据")
    else:
        write_raw_to_csv(data, output_csv)
        print(f"找到 {len(data)} 条测试记录")
        print(f"原始数据已保存到 {output_csv}")
        print("\n示例数据：")
        print(f"用户数: {data[0]['Users']}, QPS: {data[0]['QPS']}, 平均延迟: {data[0]['AvgLatency']}s")
