#!/bin/bash

OSTYPE="`uname`"
# For OS X
if [ "$OSTYPE" == "Darwin" ]; then
    /Applications/Docker/Docker\ Quickstart\ Terminal.app/Contents/Resources/Scripts/start.sh << 'EOF'
    BLUE='\033[0;34m'
    NC='\033[0m'
    echo "Deploying test docker containers on your local machine ..."
    echo -e "${BLUE}*** docker-compose up -d ***${NC}"
    docker-compose up -d
    echo
    echo "Configuring a static route to container's network(172.30.0.0/16)"
    echo
    DOCKER_IP=`docker-machine ip`
    echo -e "${BLUE}*** sudo route -n add 172.30.0.0/16 $DOCKER_IP ***${NC}"
    sudo route -n add 172.30.0.0/16 $DOCKER_IP
    echo
    echo -e "${BLUE}*** docker ps ***${NC}"
    docker ps
    echo
    echo -e "${BLUE}*** DONE ***${NC}"
    echo
    python run.py
EOF

# For Linux
else
    BLUE='\033[0;34m'
    NC='\033[0m'
    echo "Deploying test docker containers on your local machine ..."
    echo -e "${BLUE}*** docker-compose up -d ***${NC}"
    docker-compose up -d
    echo
    echo -e "${BLUE}*** docker ps ***${NC}"
    docker ps
    echo
    echo -e "${BLUE}*** DONE ***${NC}"
    echo
    python run.py
fi

##################################################
# Command for adding a container for testing
# docker run -itdP --privileged -h vm11 --name=vm11 --net mgmtappforlinuxmachines_mynetwork --ip 172.30.0.101 yugokato/ubuntu_template /bin/bash
# * network name changes depnd on the name of the program directory. You can check the network name with 'docker network ls' command.

# Command for stopping a container
# docker stop <container_name>

# Command for re-starting a container
# docker start <container_name>