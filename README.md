**Director structure**

├── 21st_strip.txt  [H3C dataset]
├── batch_benchmark.sh [Benchmark bash entry]
├── calc_p99.awk
├── calc_result.sh  [legacy scripts]
├── embedding [embedding model]
├── stress_benchmark.py [benchmark scripts]
├── stress.sh [Benchmark bash entry]



**Gaudi benchmark** 
1. steps:
start service by docker-compose, then stress the API with different concurrency and prompt length.
2. Reference scripts
For embedding benchmark
loop_hpu.sh
For rerank benchmark
loop_hpu_rerank.sh
3. Know issues

for far embedding and rerank service can't work on the same node simutaneousely. This is due to the docker-compose.yaml file setup on network.

 


**Xeon benchmark** 

How to test
1. Pull docker and setup service (TEI)
cd ./embedding
update .env 
docker compose up --build -d 

2. Make sure API works

'''
 bash
 curl -v http://10.239.241.85:32582/v1/embeddings  -X POST  -d '{"input":"What is Deep Learning?"}'             -H 'Content-Type: application/json'
'''


3. Embedding Performance benchmarking
please refer to loop.sh, stress.sh and  stress_benchmark.py
sample like this.

'''
for user in 1 4 8 16 32 48 64;
 do
      bash stress.sh embedding $user 2>&1 | tee -a xeon_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
done
'''



Rerank Performance benchmarking

please refer to loop_rerank.sh and ./rerank_bench for detail. 
A basic usage

'''
 cd rerank_bench/
   for user in 1 4 8 16 32 48 64;
    do

         python concurrent_bench.py --task tei_rerank  --url http://127.0.0.1:12003/rerank --num-chunk 5 \
                  --num-queries 1000 --concurrency $user --dataset token_len_500.json \
                           2>&1 | tee -a xeon_500_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
         python concurrent_bench.py --task tei_rerank  --url http://127.0.0.1:12003/rerank --num-chunk 5 \
                  --num-queries 1000 --concurrency $user --dataset token_len_1000.json \
                           2>&1 | tee -a xeon_1000_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
    done
'''

'''
cd rerank_bench
python concurrent_bench.py --task tei_rerank --url http://192.168.123.103:18080/rerank --num-queries 1
 python concurrent_bench.py -h
 usage: concurrent_bench.py [-h] [--task {tei_rerank,mosec_embedding,llm}] --url URL [--num-queries NUM_QUERIES] [--num-chunk NUM_CHUNK] [--concurrency {1,2,4,8,16,32,64}]

 并发HTTP请求测试工具

 options:
   -h, --help            show this help message and exit

   必需参数:
     --task {tei_rerank,mosec_embedding,llm} 测试任务类型: tei_rerank - 文本重排任务 mosec_embedding - 嵌入生成任务 llm - 大语言模型任务 (default: tei_rerank)
     --url URL             服务端URL地址 示例: http://localhost:8080/rerank (default: None)
     请求配置:
     --num-queries NUM_QUERIES
     总请求数量  (default: 1)
     --num-chunk NUM_CHUNK
     每个请求包含的文本块数量 仅对tei_rerank任务有效 示例: 2 = 每个请求包含[chunk1, chunk2] (default: 1)
     --concurrency {1,2,4,8,16,32,64}
     并发连接数 (default: 1)
'''



