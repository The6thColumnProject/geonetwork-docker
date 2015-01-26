#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
image="$(basename $SCRIPT_DIR)"

usage() {
    cat<<EOF
Usage: $0 [options]

$(sed -n '1,/^[^#]/ {s/^# *description[: ]*//pI}' $0)
options:
$(sed -n '/^#OPTIONS START/,/#OPTIONS END/ {s/ *\([^)]\+\))[^#]\+#\(.*\)/\1\t: \2/p}' $0)
EOF
}

fullpath() {
    local path="$1"
    if [[ -d "$path" ]]; then
        echo "$(cd "$path"; pwd)"
    else
        echo "$(cd $(dirname "$path"); pwd)/$(basename "$path")"
    fi
}

image_name() {
    echo ${1:-"$(basename $SCRIPT_DIR)"}
}

#hostname -I does not work on OSX
get_local_ip() {
    local _ip _line
    while IFS=$': \t' read -a _line ;do
        [ -z "${_line%inet}" ] &&
           _ip=${_line[${#_line[1]}>4?1:2]} &&
           [ "${_ip#127.0.0.1}" ] && echo $_ip && return 0
      done< <(LANG=C /sbin/ifconfig)
}

local_env() {
    local _env
    export DOCKER_LOCALHOSTNAME=${DOCKER_LOCALHOSTNAME:-$(hostname -f)}
    export DOCKER_LOCALIP=${DOCKER_LOCALIP:-$(get_local_ip)}
    for v in $(env | sed -n '/^DOCKER_/p'); do
        DOCKER_EXTENDED_ENV="$DOCKER_EXTENDED_ENV -e $v "
    done
    export DOCKER_EXTENDED_ENV
}
