#!/bin/sh

for i in $(seq 1 32);
do
for j in $(seq 1 32);
do

python vprm_preprocessor_new.py --year 2023 --config ./config/preprocessor_config.yaml --n_cpus=60 --chunk_x=$i --chunk_y=$j

done
done

#for i in $(seq 15 32);
#do
#for j in $(seq 1 32);
#do

#python vprm_preprocessor_new_not_data.py --year 2023 --config ./config/preprocessor_config.yaml --n_cpus=60 --chunk_x=$i --chunk_y=$j

#done
#done

echo "FINISHED!!!!"

#echo "python vprm_preprocessor_new.py --year 2023 --config ./config/preprocessor_config.yaml --n_cpus=32 --chunk_x="$i "--chunk_y="$j
