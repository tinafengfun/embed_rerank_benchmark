#!/bin/bash

SCRIPT_HOME=$(cd $(dirname ${BASH_SOURCE[0]}); pwd )

if [ $# -lt 1 ]; then
  echo "Missing statistics data file!"
  echo "Usage: $0 <stat_data.csv>"
  exit
fi

awk -F, 'BEGIN { cnt=err=0 }  { if ($6==200) cnt++; else err++; } END { print "SUCCESS:" cnt; print "FAILED:" err}' $1
echo -e "\nDistribution:"
awk -F, '{print $4 }' $1  | sort -n | uniq -c | awk -f ${SCRIPT_HOME}/calc_p99.awk

count_n=$(awk 'END { print NR }' $1 | tr -d '\n')
start_tm=$(awk -F, '{print $7 }' $1  | sort -n | head -1 | tr -d '\r' | tr -d '\n')
end_tm=$(awk -F, '{print $8 }' $1  | sort -n | tail -1 | tr -d '\r' | tr -d '\n')

tps=$(echo "scale=2; ${count_n}/(${end_tm}-${start_tm})" | bc)
echo -e "\nTPS: ${tps}"
