#!/bin/sh

#rm -fvr /Users/vosslab/.docker/machine/machines/default
#docker-machine create --virtualbox-disk-size 35000 --driver virtualbox default
docker-machine start default
sleep 1

echo ''
echo 'eval $(docker-machine env default)'
