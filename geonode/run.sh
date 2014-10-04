#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
image="$(basename $SCRIPT_DIR)"

usage() {
    cat<<EOF
Usage: $0 [options]

options:
$(sed -n '/^#OPTIONS START/,/#OPTIONS END/ {s/ *\([^)]\+\))[^#]\+#\(.*\)/\1\t: \2/p}' $0)
EOF
}

#defaults
container_dir=/tmp/$image

#OPTIONS START
while getopts 'hdic:' opt; do
    case "$opt" in
        c) container_dir="$OPTARG";;   #defines the directory for the container files
        d) debug=1;;            #turns debugging on
        i) interactive=1;;      #starts a shell in the container
        h) usage; exit 0;;      #shows this help
        *) echo "Unknown option $opt"; usage; exit 1;;
    esac
done
#OPTIONS END

[[ -d "$container_dir" ]] || mkdir -p "$container_dir"


((debug)) && cat <<EOF
container_dir=$container_dir
EOF

if ((interactive)); then
    docker run -ti --rm -v "$container_dir:/container_data" $image /bin/bash
else
    docker run -d -v "$container_dir:/container_data" $image /container/boot
fi
