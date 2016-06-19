#!/bin/bash

OSTYPE="`uname`"
# For OS X
if [ "$OSTYPE" == "Darwin" ]; then
    /Applications/Docker/Docker\ Quickstart\ Terminal.app/Contents/Resources/Scripts/start.sh << 'EOF'

    BLUE='\033[0;34m'
    NC='\033[0m'
    echo "Shutting down and deleting test containers on this machine..."
    echo -e "${BLUE}*** docker-compose down ***${NC}"
    docker-compose down
    echo
    DOCKER_IP=`docker-machine ip`
    echo "Deleting a static route to container's network(172.30.0.0/16)..."
    echo -e "${BLUE}*** sudo route -n delete 172.30.0.0/16 $DOCKER_IP ***${NC}"
    sudo route -n delete 172.30.0.0/16 $DOCKER_IP
    echo
    echo -e "${BLUE}*** docker ps ***${NC}"
    docker ps
    echo
    echo -e "${BLUE}*** DONE ***${NC}"
EOF

# For Linux
else
    BLUE='\033[0;34m'
    NC='\033[0m'
    echo "Shutting down and deleting test containers on this machine..."
    echo -e "${BLUE}*** docker-compose down ***${NC}"
    docker-compose down
    echo
    echo -e "${BLUE}*** docker ps ***${NC}"
    docker ps
    echo
    echo -e "${BLUE}*** DONE ***${NC}"
fi