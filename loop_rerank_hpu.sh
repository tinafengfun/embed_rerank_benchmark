#!/bin/bash
unset http_proxy
unset https_proxy
unset HTTPS_PROXY
unset HTTP_PROXY
CONTAINER_NAME=tei-reranking-serving
export DATA_PATH=/mnt/disk1/models
COMPOSE_FILE=`pwd`/compose.yaml.rerank.hpu

#for model in  gte-reranker-modernbert-base;
for model in bge-reranker-base bge-reranker-large bge-reranker-v2-m3 gte-reranker-modernbert-base;
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
case $model in
	bge-reranker-base|bge-reranker-large)
		length=512
		files=(21_512.json)
                ;;
      bge-reranker-v2-m3)
		length=1024
		files=(21_512.json 21_1024.json 21_4096.json 21_8192.json)
                ;;
       *)
		length=2048
		files=(21_512.json 21_1024.json 21_4096.json 21_8192.json)
                ;;
esac

export warmup_length=$length
docker-compose -f "$COMPOSE_FILE" up --build -d >/dev/null 2>&1
echo "Waiting for container to initialize..."
sleep 20 
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Error: Container failed to start"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

while true; do

    docker logs "$CONTAINER_NAME" 2>/dev/null | grep "Ready" 
    if [ "$?" -eq 0 ]; then
	echo "docker is ready exit the loop."
	break
    fi
    echo "within loop"
    sleep 30
done

echo "Conduct test now..."

cd rerank_bench/
#for user in 64;
for user in 1 4 8 16 32 64;
do

    python3 concurrent_bench.py --task tei_rerank  --url http://127.0.0.1:12007/rerank --num-chunk 5 \
        --num-queries 600 --concurrency $user --dataset token_len_500.json \
        2>&1 | tee -a hpu_500_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
    python3 concurrent_bench.py --task tei_rerank  --url http://127.0.0.1:12007/rerank --num-chunk 5 \
        --num-queries 600 --concurrency $user --dataset token_len_1000.json \
        2>&1 | tee -a hpu_1000_${model}_${user}_$(date '+%Y%m%d_%H%M%S').log
done
cd ../.
done
