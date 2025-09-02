#!/bin/bash  
# run_stress.sh  
# 循环调用stress.sh脚本  
  
# 设定循环次数  
COUNT=0
  
# 开始循环  
for ((i=0;i<=$COUNT;i++))  
do  
    wrk=`echo "scale=0; 2^6" | bc`
    echo "Running stress test wrk: $wrk..."  
    # 调用stress.sh脚本  

    ./stress.sh embedding $wrk
    # 等待20秒  
    sleep 5  
done  