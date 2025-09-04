# Directory Structure

```
.
├── 21_1024.json
├── 21_2048.json
├── 21_4096.json
├── 21_512.json
├── 21_8192.json
├── 21st_strip.txt
├── batch_benchmark.sh
├── compose.yaml.hpu
├── compose.yaml.rerank.hpu
├── data_set_split
│   ├── 21_4096.json
│   ├── 21_8192.json
│   ├── deepseek_python_20250620_f85e50.py
│   ├── tokenize_split.py
│   └── tripe.txt1
├── embedding
│   ├── compose.yaml
│   └── compose.yaml.full
├── loop_hpu.sh
├── loop_mteb.sh
├── loop_rerank_hpu.sh
├── loop_rerank.sh
├── offline
│   ├── benchmark_embedding_bge_offline.py
│   ├── benchmark_embedding_offline.py
│   ├── debug.log
│   ├── loop_offline.sh
├── README.md
├── rerank_bench
│   ├── 21st_strip.txt
│   ├── concurrent_bench.py
│   ├── data_parser.py
│   ├── qa_pairs.json
│   ├── token_len_1000.json
│   └── token_len_500.json
├── stress_benchmark.py
└── stress.sh
```

## Gaudi Benchmark

### Steps:
0.prepare data file by spliting dataset with model tokenizer (optional) 
1. Start service by docker-compose
2. Stress the API with different concurrency and prompt length

#### data file split
Embedding spliter: data_set_split:tokenize_split.py 
dataset: 21st_strip.txt

#### docker compose installation
Please use the following commnad to update docker-compose for test

```
sudo curl -L "https://github.com/docker/compose/releases/download/v2.39.2/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

#### update compose.yaml.hpu for test
update the device id for your setup
HABANA_VISIBLE_DEVICES: 0 


#### update loop_hpu.sh env and kickstart test
Variables need to update in loop_hpu.sh

``` 
#update for local model path
export DATA_PATH=/mnt/disk1/models --- update for local model path
# update for model in test
for model in bge-base-zh-v1.5 bge-large-zh-v1.5 bge-m3 Qwen3-Embedding-0.6B Qwen3-Embedding-4B Qwen3-Embedding-8B gte-modernbert-base; 

# dataset for test
#change files=(21_512.json) for your usage
case $model in
        bge-base-zh-v1.5|bge-large-zh-v1.5)
                length=512
                files=(21_512.json)
                ;;
       bge-m3)
                length=2048
                files=(21_512.json 21_1024.json 21_4096.json 21_8192.json)
                ;;
       *)
                length=4096
                files=(21_4096.json 21_8192.json)
                ;;
esac
# concurrency config 
for user in 1 4 8 16 32 64;

```
in intel env, please unset proxy to kickstart test
unset http_proxy
unset https_proxy
unset HTTPS_PROXY
unset HTTP_PROXY

test result is under embed_resut

### Reference Scripts:
- For embedding benchmark: `loop_hpu.sh`
- For rerank benchmark: `loop_hpu_rerank.sh`

### Known Issues:
For far embedding and rerank service can't work on the same node simultaneously due to the docker-compose.yaml file setup on network.




---

## Xeon Benchmark

### How to Test

1. Pull docker and setup service (TEI)
   ```bash
   cd ./embedding
   update .env 
   docker compose up --build -d 
   ```

2. Make sure API works
   ```bash
   curl -v http://10.239.241.85:32582/v1/embeddings -X POST \
     -d '{"input":"What is Deep Learning?"}' \
     -H 'Content-Type: application/json'
   ```

### Embedding Performance Benchmarking

#### CPU:
Please refer to `loop.sh`, `stress.sh` and `stress_benchmark.py`

Sample usage:
```bash
for user in 1 4 8 16 32 48 64; do
    bash stress.sh embedding $user 2>&1 | tee -a xeon_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
done
```



### Rerank Performance Benchmarking

Please refer to `loop_rerank.sh` and `./rerank_bench` for details.

Basic usage:
```bash
cd rerank_bench/
for user in 1 4 8 16 32 48 64; do
    python concurrent_bench.py --task tei_rerank \
        --url http://127.0.0.1:12003/rerank \
        --num-chunk 5 \
        --num-queries 1000 \
        --concurrency $user \
        --dataset token_len_500.json \
        2>&1 | tee -a xeon_500_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
        
    python concurrent_bench.py --task tei_rerank \
        --url http://127.0.0.1:12003/rerank \
        --num-chunk 5 \
        --num-queries 1000 \
        --concurrency $user \
        --dataset token_len_1000.json \
        2>&1 | tee -a xeon_1000_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
done
```

### Concurrent Benchmark Tool Usage

```bash
cd rerank_bench

# Basic test
python concurrent_bench.py --task tei_rerank \
    --url http://192.168.123.103:18080/rerank \
    --num-queries 1

# Help information
python concurrent_bench.py -h
```

```
usage: concurrent_bench.py [-h] [--task {tei_rerank,mosec_embedding,llm}] --url URL [--num-queries NUM_QUERIES] [--num-chunk NUM_CHUNK] [--concurrency {1,2,4,8,16,32,64}]

并发HTTP请求测试工具

options:
  -h, --help            show this help message and exit

必需参数:
  --task {tei_rerank,mosec_embedding,llm}
                        测试任务类型: tei_rerank - 文本重排任务 mosec_embedding - 嵌入生成任务 llm - 大语言模型任务 (default: tei_rerank)
  --url URL             服务端URL地址 示例: http://localhost:8080/rerank (default: None)

请求配置:
  --num-queries NUM_QUERIES
                        总请求数量 (default: 1)
  --num-chunk NUM_CHUNK
                        每个请求包含的文本块数量 仅对tei_rerank任务有效 示例: 2 = 每个请求包含[chunk1, chunk2] (default: 1)
  --concurrency {1,2,4,8,16,32,64}
                        并发连接数 (default: 1)
```
