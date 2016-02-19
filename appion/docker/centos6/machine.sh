#!/bin/sh

#docker-machine create --driver virtualbox default
docker-machine start default
sleep 1

echo ''
echo 'eval $(docker-machine env default)'
