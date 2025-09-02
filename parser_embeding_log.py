import re
import csv

def extract_log_data(log_file_path):
    # 定义匹配模式
    pattern = re.compile(
        r'Run embedding with queries .*?, (\d+) users.*?'
        r'===== 请求统计结果 =====.*?'
        r'总请求数: (\d+).*?'
        r'成功率: ([\d.]+)%.*?'
        r'错误率: ([\d.]+)%.*?'
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

    data = []

    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_content = file.read()
        matches = pattern.finditer(log_content)

        for match in matches:
            data.append({
                'Users': int(match.group(1)),
                'TotalRequests': int(match.group(2)),
                'SuccessRate': float(match.group(3)),
                'ErrorRate': float(match.group(4)),
                'QPS': float(match.group(5)),
                'TotalTime': float(match.group(6)),
                'AvgLatency': float(match.group(7)),
                'MedianLatency': float(match.group(8)),
                'P90Latency': float(match.group(9)),
                'P95Latency': float(match.group(10)),
                'MinLength': int(match.group(11)),
                'MaxLength': int(match.group(12)),
                'AvgLength': float(match.group(13))
            })
    print(f"log {data}")

    return data

def save_to_csv(data, output_file_path):
    if not data:
        print("没有数据可保存")
        return

    # 使用第一个字典的键作为表头
    fieldnames = list(data[0].keys())

    with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    input_log_file = "tripe.txt1"  # 替换为你的日志文件路径
    output_csv_file = "extracted_data.csv"

    print(f"正在处理日志文件: {input_log_file}")
    extracted_data = extract_log_data(input_log_file)

    if not extracted_data:
        print("未找到匹配的数据模式，请检查日志格式。")
    else:
        save_to_csv(extracted_data, output_csv_file)
        print(f"成功提取 {len(extracted_data)} 条记录")
        print(f"数据已保存到: {output_csv_file}")
        print("\n示例数据:")
        for key, value in extracted_data[0].items():
            print(f"{key}: {value}")
