#!/bin/bash
#set -x
#CONTAINER_NAME=tei-embedding-serving
unset http_proxy
unset https_proxy
unset HTTPS_PROXY
unset HTTP_PROXY
CONTAINER_NAME=tei-embedding-serving
export DATA_PATH=/mnt/disk1/models
COMPOSE_FILE=`pwd`/compose.yaml.hpu
export host_ip=127.0.0.1
for model in bge-base-zh-v1.5 bge-large-zh-v1.5 bge-m3 Qwen3-Embedding-0.6B Qwen3-Embedding-4B Qwen3-Embedding-8B gte-modernbert-base;
#for model in gte-modernbert-base;
do
# delete docker
echo "Stopping and removing existing container..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1
docker rm "$CONTAINER_NAME" >/dev/null 2>&1
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Error: Failed to remove container $CONTAINER_NAME"
            exit 1
fi
export H_model=$model                                               
export EMBEDDING_MODEL_ID=/data/$model
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

export warmup_length=$length
docker-compose -f "$COMPOSE_FILE" up --build -d >/dev/null 2>&1
echo "Waiting for container to initialize..."
sleep 20
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Error: Container failed to start"
    docker logs "$CONTAINER_NAME"
    exit 1
fi
#status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME")
#if [[ $status != "healthy" ]];then

#    echo "Error: Container healthy error"
#    docker logs "$CONTAINER_NAME"
#    exit 1
#fi
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
mkdir -p embed_result
for file in "${files[@]}"; do 
for user in 1 4 8 16 32 64;
#for user in 1;
do
    echo "----start test $model $file $user"
    prefix=$(basename "$file" .json)
    bash stress.sh embedding $user $file json 2>&1 | tee -a embed_result/1_hpu_${model}_${prefix}_${user}_$(date '+%Y%m%d_%H%M%S').log
    bash stress.sh embedding $user $file json 2>&1 | tee -a embed_result/hpu_${model}_${prefix}_${user}_$(date '+%Y%m%d_%H%M%S').log
done
done
done
