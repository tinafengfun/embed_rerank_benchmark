#!/bin/bash

for model in bge-base-zh-v1.5 bge-large-zh-v1.5 bge-m3;
do
    for batch in 1 4 8 16 32 64;
    do
        echo "test model ${model}, batch $batch" | tee -a offline_result_1000.log
        numactl -C 56-87 python benchmark_embedding_bge_offline.py --batch $batch  --model /home/liuzhuan/rag/benchmark/embedding/${model} 2>&1 | tee -a offline_result_1000.log

        echo "complete test model ${model}, batch $batch" | tee -a offline_result_1000.log
done
done


