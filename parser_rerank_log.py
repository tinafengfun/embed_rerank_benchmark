import re
import csv
import os

def extract_log_data(log_file_path):
    # 匹配每个测试块的模式
    block_pattern = re.compile(
        r'=+\n=+\n'
        r'Total Concurrency: (\d+)\n'
        r'Total Requests: (\d+)\n'
        r'Total Test time: ([\d.]+)\n'
        r'avg total latency is  ([\d.]+) s\n'
        r'P50 total latency is  ([\d.]+) s\n'
        r'P90 total latency is  ([\d.]+) s\n'
        r'P99 total latency is  ([\d.]+) s\n'
        r'Total error request is  (\d+)',
        re.MULTILINE
    )

    data = []

    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_content = file.read()
        matches = block_pattern.findall(log_content)

        for match in matches:
            data.append({
                'Concurrency': match[0],
                'TotalRequests': match[1],
                'TotalTestTime': match[2],
                'AvgTotalLatency': match[3],
                'P50TotalLatency': match[4],
                'P90TotalLatency': match[5],
                'P99TotalLatency': match[6],
                'TotalErrorRequest': match[7]
            })

    return data

def save_to_csv(data, output_file_path):
    if not data:
        print("没有提取到数据")
        return

    fieldnames = [
        'Concurrency', 'TotalRequests', 'TotalTestTime',
        'AvgTotalLatency', 'P50TotalLatency', 'P90TotalLatency',
        'P99TotalLatency', 'TotalErrorRequest'
    ]

    with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"成功保存 {len(data)} 条记录到 {output_file_path}")

if __name__ == "__main__":
    # 配置路径
    log_file = "rerank.log"  # 替换为您的日志文件路径
    output_csv = "log_results1.csv"

    # 提取并保存数据
    extracted_data = extract_log_data(log_file)
    save_to_csv(extracted_data, output_csv)

    # 显示提取的数据
    if extracted_data:
        print("\n提取的数据:")
        for i, item in enumerate(extracted_data[:3]):  # 显示前3条作为示例
            print(f"记录 {i+1}:")
            for key, value in item.items():
                print(f"  {key}: {value}")
