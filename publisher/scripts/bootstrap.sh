#!/bin/bash

uid=$HOST_USER
gid=$HOST_USER_GROUP

if [[ "$uid" && "$gid" ]]; then
    groupadd -fg $gid host_user_group 
    useradd -oMN -u $uid -g $gid host_user
    sudo -u host_user "$@"
else
    "$@"
fi
