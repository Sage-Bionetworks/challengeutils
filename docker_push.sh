#!/bin/bash
echo $DOCKER_PASSWORD | docker login --username $DOCKER_USERNAME --password-stdin docker.synapse.org
docker build . -t docker.synapse.org/syn18058986/challengeutils:$TRAVIS_BRANCH
docker push docker.synapse.org/syn18058986/challengeutils