#!/bin/bash
CONTAINER_NAME=tei-reranking-serving
export DATA_PATH=/home/liuzhuan/rag/benchmark/embedding/
COMPOSE_FILE=/home/liuzhuan/rag/benchmark_gaudi/compose.yaml

for model in bge-reranker-base bge-reranker-large bge-reranker-v2-m3;
do
# delete docker
echo "Stopping and removing existing container..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1
docker rm "$CONTAINER_NAME" >/dev/null 2>&1
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Error: Failed to remove container $CONTAINER_NAME"
            exit 1
fi
export RERANK_MODEL_ID=/data/$model
docker compose -f "$COMPOSE_FILE" up --build -d >/dev/null 2>&1
echo "Waiting for container to initialize..."
sleep 60
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Error: Container failed to start"
    docker logs "$CONTAINER_NAME"
    exit 1
fi
status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME")
if [[ $status != "healthy" ]];then

    echo "Error: Container healthy error"
    docker logs "$CONTAINER_NAME"
    exit 1
fi
echo "Conduct test now..."

cd rerank_bench/
#for user in 1;
for user in 1 4 8 16 32 48 64;
do

    python concurrent_bench.py --task tei_rerank  --url http://127.0.0.1:12003/rerank --num-chunk 5 \
        --num-queries 1000 --concurrency $user --dataset token_len_500.json \
        2>&1 | tee -a xeon_500_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
    python concurrent_bench.py --task tei_rerank  --url http://127.0.0.1:12003/rerank --num-chunk 5 \
        --num-queries 1000 --concurrency $user --dataset token_len_1000.json \
        2>&1 | tee -a xeon_1000_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
done
cd ../.
done
