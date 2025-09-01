
import argparse
import concurrent.futures
import json
import random
import time
import requests
import numpy
import os
os.environ.pop("http_proxy", None)


with open("qa_pairs.json","r", encoding='utf8') as f:
    raw_dataset = json.load(f)
questions = []

for item in raw_dataset:
    q = item['question']
    questions.append(q)


questions_len = len(questions)

def conscruct_data(task,idx,chunks,rerank_chunks):
    rerank_chunks_len = len(rerank_chunks)
    if task == "tei_rerank":
        start_idx = idx % rerank_chunks_len
        # 获取连续的num_chunks个chunk（循环利用数据）
        texts = [
                   rerank_chunks[(start_idx + i) % rerank_chunks_len]
                   for i in range(chunks)
               ]

        sample = {"query": questions[idx%questions_len], "texts": texts}

    elif task == "mosec_embedding":
        sample = {"text": questions[idx%questions_len]}
    return sample



def send_single_request_zh(task, idx, queries, concurrency, url, chunks, rerank_chunks, data_zh=None):
    res = []
    headers = {"Content-Type": "application/json"}
    #query = random.choice(data_zh)
    #data ={"messages": query, "max_tokens": 128}
    #if task == "rag":
    #    data = {"messages": query, "max_tokens": 128}
    #elif task == "embedding":
    #    data = {"text": query}
    #elif task == "llm":
    #    data = {"query": query, "max_new_tokens": 128}
    data = conscruct_data(task,idx,chunks,rerank_chunks)
    # print(data)
    while idx < len(queries):

        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        end_time = time.time()
#        print(f"return {response.status_code}")
        if response.status_code == 200:
            res.append({"idx": idx, "start": start_time, "end": end_time, "status": 0})
        else:
            res.append({"idx": idx, "start": start_time, "end": end_time, "status": -1})

        idx += 1
        #print(f"{response.}")
    return res

query = "1"
def send_concurrency_requests_zh(task, request_url, num_queries, num_chunk, concurrency, rerank_chunks):
    if num_queries <= 0:
        num_queries = 1
    if concurrency <= 0:
        concurrency = 1

    #data_zh = []
    #file_path = './data.txt'
    #with open(file_path, 'r') as file:
    #    for line in file:
    #        data_zh.append(line.strip())

    responses = []
    stock_queries = [query for _ in range(num_queries)]
    test_start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            futures.append(executor.submit(
                send_single_request_zh,
                task=task,
                idx=i,
                queries=stock_queries,
                concurrency=concurrency,
                url=request_url,
                chunks=num_chunk,
                rerank_chunks=rerank_chunks,
                #data_zh=data_zh
            ))
        for future in concurrent.futures.as_completed(futures):
            responses = responses + future.result()
    test_end_time = time.time()

    print("=======================")

    for r in responses:
        if r["status"] == 0:
            r["total_time"] = r["end"] - r["start"]
            r["total_error"] = 0
        else:
            r["total_time"] = 0
            r["total_error"] = 1
        # print("query:", r["idx"], "    time taken:", r["total_time"])

    print("=======================")
    print(f"Total Concurrency: {concurrency}")
    print(f"Total Requests: {len(stock_queries)}")
    print(f"Total Test time: {test_end_time - test_start_time}")

    response_times = [r["total_time"] for r in responses]
    response_error = [r["total_error"] for r in responses]
    # print("responses===================", responses)

    avg_total = numpy.mean(response_times)
    print("avg total latency is ", avg_total, "s")

    # Calculate the P50 (median)
    p50_total = numpy.percentile(response_times, 50)
    print("P50 total latency is ", p50_total, "s")



    p90_total = numpy.percentile(response_times, 90)
    print("P90 total latency is ", p90_total, "s")


    # Calculate the P99
    p99_total = numpy.percentile(response_times, 99)
    print("P99 total latency is ", p99_total, "s")


    err_total = numpy.sum(response_error)
    print("Total error request is ", err_total)

    return avg_total, p50_total, p90_total, p99_total

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="并发HTTP请求测试工具",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # 必需参数组
    required = parser.add_argument_group('必需参数')
    required.add_argument(
        "--task",
        type=str,
        choices=["tei_rerank", "mosec_embedding", "llm"],
        default="tei_rerank",
        help="测试任务类型:\n"
             "  tei_rerank - 文本重排任务\n"
             "  mosec_embedding - 嵌入生成任务\n"
             "  llm - 大语言模型任务"
    )
    required.add_argument(
        "--url",
        type=str,
        required=True,
        help="服务端URL地址\n"
             "示例: http://localhost:8080/rerank"
    )

    # 请求配置组
    config = parser.add_argument_group('请求配置')
    config.add_argument(
        "--num-queries",
        type=int,
        default=1,
        help="总请求数量\n"
             "建议值: 10-1000 (根据服务能力调整)"
    )
    config.add_argument(
        "--num-chunk",
        type=int,
        default=1,
        help="每个请求包含的文本块数量\n"
             "仅对tei_rerank任务有效\n"
             "示例: 2 = 每个请求包含[chunk1, chunk2]"
    )
    config.add_argument(
        "--concurrency",
        type=int,
        default=1,
        choices=[1, 2, 4, 8, 16, 32, 64],
        help="并发连接数\n"
    )
    config.add_argument(
        "--dataset",
        type=str,
        default="token_len_500.json",
        help="data set file\n"
    )


    args = parser.parse_args()

    # 参数验证
    if args.num_queries <= 0:
        parser.error("--num-queries必须大于0")
    if args.num_chunk < 1:
        parser.error("--num-chunk必须大于等于1")

    return args


# python concurrent_bench.py --task tei_rerank --url http://192.168.123.103:18080/rerank --num-queries 1
if __name__ == "__main__":
    args = parse_args()
    with open(args.dataset,"r", encoding='utf8') as f:
        rerank_chunks = json.load(f)


    send_concurrency_requests_zh(args.task, args.url, args.num_queries, args.num_chunk, args.concurrency, rerank_chunks)
