#!/bin/bash
#set -x
#CONTAINER_NAME=tei-embedding-serving
CONTAINER_NAME=tei-embedding-serving
export DATA_PATH=/model/
COMPOSE_FILE=`pwd`/compose.yaml.hpu
#for model in bge-large-zh-v1.5;
#for model in bge-base-zh-v1.5 bge-large-zh-v1.5 bge-m3; 
#for model in  bge-m3; 
#for model in bge-base-zh-v1.5 ;
#for model in bge-base-zh-v1.5 bge-large-zh-v1.5 bge-m3 Qwen3-Embedding-0.6B Qwen3-Embedding-4B Qwen3-Embedding-8B;
for model in Qwen3-Embedding-0.6B Qwen3-Embedding-4B Qwen3-Embedding-8B;
#for model in Qwen3-Embedding-0.6B;
do
#for pool in cls:
for pool in cls mean last-token:
do

# delete docker
echo "Stopping and removing existing container..."
docker stop "$CONTAINER_NAME" >/dev/null 2>&1
docker rm "$CONTAINER_NAME" >/dev/null 2>&1
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "Error: Failed to remove container $CONTAINER_NAME"
            exit 1
fi
export EMBEDDING_MODEL_ID=/data/$model
export pooling=$pool
case $model in
	bge-base-zh-v1.5|bge-large-zh-v1.5)
		length=512
		files=(21_512.json)
                ;;
       bge-m3)
		length=8192
		files=(21_512.json 21_1024.json 21_4096.json 21_8192.json)
                ;;
       *)
		length=4096
		files=(21_512.json 21_1024.json 21_4096.json 21_8192.json)
                ;;
esac

export warmup_length=$length
docker-compose -f "$COMPOSE_FILE" up --build -d 2>&1
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
exit
echo "Conduct test now..."
mkdir -p embed_result
echo "model $model pooling $pool test" >> embed_result/mteb.log
source /home/test/tianfeng/mteb/mteb/ut/.env
#python3 /home/test/tianfeng/mteb/mteb/ut/benchmark.py 2>&1 | tee -a embed_result/mteb.log 
python3 /home/test/tianfeng/mteb/mteb/ut/full_benchmark.py -m openai/$model -t STSB 2>&1 | tee -a embed_result/mteb.log 

done
done
