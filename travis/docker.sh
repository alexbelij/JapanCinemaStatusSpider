#!/bin/bash

set -e

# Build docker image
sudo docker build --rm=true --file docker/crawler/Dockerfile --tag=gas1121/japancinemastatusspider:crawler-test .
sudo docker build --rm=true --file docker/scheduler/Dockerfile --tag=gas1121/japancinemastatusspider:scheduler-test .

# create tempory dir to store combined coverage data
mkdir -p coverage/crawler
mkdir -p coverage/scheduler
sudo chown -R travis:travis coverage

# start target service for testing
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs
sleep 10

# install package for test
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler pip install coverage

# run tests
sudo docker-compose -f travis/docker-compose.test.yml exec scheduler ./run_tests.sh
# get coverage data from container
sudo docker cp $(sudo docker-compose -f travis/docker-compose.test.yml ps -q scheduler):/app/.coverage coverage/scheduler
# change path in coverage data
sudo sed -i 's#/app#'"$PWD"'/scheduler#g' coverage/scheduler/.coverage
# combine coverage data
pip install coverage coveralls
cd coverage && coverage combine scheduler/.coverage
sudo mv .coverage ..
cd ..
sudo chown travis:travis .coverage
# send coverage report
coveralls

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# remove 'test' images
sudo docker rmi gas1121/japancinemastatusspider:crawler-test
sudo docker rmi gas1121/japancinemastatusspider:scheduler-test
