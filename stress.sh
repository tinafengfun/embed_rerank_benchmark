#!/bin/bash

SCRIPT_HOME=$(cd $(dirname ${BASH_SOURCE[0]}); pwd )
unset http_proxy
unset https_proxy
EMBEDDING_ENDPOINT=127.0.0.1:12003
#EMBEDDING_ENDPOINT=10.239.241.85:32582
RERANKING_ENDPOINT=127.0.0.1:30090
EMBEDDING_QUERIES=/home/liuzhuan/rag/benchmark/21st_strip.txt
RERANKING_QUERIES=/u01/project/rag/benchmark/reranking/rerank_queries.jsonl

THIS_CPU_LIST=58-65
OPEA_NAMESPACE=opea-xim

BENCHMARK_DURATION=5m
BENCHMAKR_USERS=$2
EMBEDDING_QUERIES=$3
BENCHMAKR_FILE_FORMAT=$4
BENCHMARK_ENDPOINT=$RERANKING_ENDPOINT
BENCHMARK_QUERIES=$RERANKING_QUERIES

BENCHMARK=${1:-"reranking"}
if [ "${BENCHMARK}" == "reranking" ]; then
  BENCHMARK_ENDPOINT=$RERANKING_ENDPOINT
  BENCHMARK_QUERIES=$RERANKING_QUERIES
elif [ "${BENCHMARK}" == "embedding" ]; then
  BENCHMARK_ENDPOINT=$EMBEDDING_ENDPOINT
  BENCHMARK_QUERIES=$EMBEDDING_QUERIES
else
  echo "Unsupported benchmark ${BENCHMARK}"
  exit
fi

echo "Run ${BENCHMARK} with queries ${BENCHMARK_QUERIES}, ${BENCHMAKR_USERS} users..."

#BENCHMARK=tei_embedding
#NOW=$(date -Iseconds)
NOW=$(date +%m%d-%H%M)

HF_ENDPOINT=https://hf-mirror.com taskset -c ${THIS_CPU_LIST} python3 stress_benchmark.py -c ${BENCHMAKR_USERS}  -d ${BENCHMARK_DURATION} -t ${BENCHMARK} -s ${BENCHMARK_ENDPOINT} -u 1s -f ${BENCHMARK_QUERIES} -j ${BENCHMAKR_FILE_FORMAT} -m /model/bge-m3 &
BENCHMARK_PID=$!

RUNNING=1
while [[ $RUNNING -gt 0 ]]; do
  RUNNING=$(ps -A | grep $BENCHMARK_PID -c)
  sleep 15
  #kubectl top pods -n $OPEA_NAMESPACE | tee -a cpu_${BENCHMARK}_${NOW}_c-${BENCHMAKR_USERS}.txt
done
