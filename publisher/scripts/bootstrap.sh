#!/bin/bash

uid=$HOST_USER
gid=$HOST_USER_GROUP

if [[ "$uid" && "$gid" ]]; then
    groupadd -fg $gid host_user_group 2>/dev/null 
    useradd -oMN -u $uid -g $gid host_user 2>/dev/null
    [[ ! -d /python-eggs ]] && mkdir /python-eggs && chown host_user python-eggs
    export PYTHON_EGG_CACHE=/python-eggs
    sudo -Eu host_user "$@"
else
    "$@"
fi
