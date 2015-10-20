#!/bin/sh

docker exec -t -i `docker ps | grep -v PORTS | awk '{print $1}'` bash
