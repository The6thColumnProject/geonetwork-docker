#!/bin/bash

uid=$HOST_USER
gid=$HOST_USER_GROUP

if [[ "$uid" && "$gid" ]]; then
    groupadd -fg $gid host_user_group 
    useradd -oMN -u $uid -g $gid host_user
    mkdir /python-eggs && chown host_user python-eggs
    export PYTHON_EGG_CACHE=/python-eggs
    sudo -Eu host_user "$@"
else
    "$@"
fi
