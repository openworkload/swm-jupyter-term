#!/usr/bin/env bash
#
# SPDX-FileCopyrightText: © 2021 Taras Shapovalov
# SPDX-License-Identifier: BSD-3-Clause
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# This script is used for running JupyterHub with Sky Port enabled in a container

set +x

DOMAIN=openworkload.org
NETWORK=skyportnet

CONTAINER_NAME=jupyterhub
IMAGE_NAME=skyport-jupyterhub
USER_API_PORT=8000

RUNNING=$(docker inspect -f '{{.State.Running}}' ${CONTAINER_NAME} 2>/dev/null)
NOT_RUNNING=$?

if docker network inspect "${NETWORK}" >/dev/null 2>&1; then
    echo "Docker network '${NETWORK}' already exists"
else
    docker network create "${NETWORK}" >/dev/null
    echo "Created docker network '${NETWORK}'"
fi

if [ "$NOT_RUNNING" != "0" ]; then
    docker run\
        --publish $USER_API_PORT:$USER_API_PORT\
        --volume $HOME/.swm:/root/.swm\
        --name $CONTAINER_NAME\
        --hostname $CONTAINER_NAME\
        --network-alias $CONTAINER_NAME\
        --domainname $DOMAIN\
        --workdir ${PWD}\
        --tty\
        --interactive\
        --network $NETWORK\
        -e SKYPORT_USER=$(id -u -n)\
        -e SKYPORT_USER_ID=$(id -u)\
        ${IMAGE_NAME}

elif [[ ${RUNNING} = "false" ]]; then
    docker start ${CONTAINER_NAME}
fi

exit 0
