#!/bin/sh

docker kill `docker ps | grep -v PORTS | awk '{print $1}'`

docker ps
