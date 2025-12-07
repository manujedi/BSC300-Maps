#!/bin/bash

# Used shared memory to improve performance (requires free RAM space)
TEMP_JAVA_DIR_PATH="/dev/shm/"

BIN_DIR=osmosis

# Initialize variables
input_map_file=""
output_map_file=""

# Parse command-line options
while getopts "i:o:" opt; do
    case $opt in
	i) input_map_file="$OPTARG" ;;
	o) output_map_file="$OPTARG" ;;
	*)
	    echo "Usage: $0 -i <input_map_file> -o <output_map_file>"
	    echo "The input map file should be in the .pbf format (e.g. downloaded from https://download.geofabrik.de/)".
	    exit 1
	    ;;
    esac
done

input_map_file="$(realpath ${input_map_file})"
output_map_file="$(realpath ${output_map_file}).map"
tag_file="$(realpath tag-igpsport.xml)"

TEMP_JAVA_DIR=$(mktemp -d -p ${TEMP_JAVA_DIR_PATH})
trap 'rm -rf '"$TEMP_JAVA_DIR"'' EXIT
export JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=${TEMP_JAVA_DIR}"

(cd ${BIN_DIR}/bin && ./osmosis --rbf file="${input_map_file}" --tag-filter reject-ways amenity=* highway=* building=* natural=* landuse=* leisure=* shop=* waterway=* man_made=* railway=* tourism=* barrier=* boundary=* power=* historic=* emergency=* office=* craft=* healthcare=* aeroway=* route=* public_transport=* bridge=* tunnel=* addr:housenumber=* addr:street=* addr:city=* addr:postcode=* name=* ref=* surface=* access=* foot=* bicycle=* motor_vehicle=* oneway=* lit=* width=* maxspeed=* mountain_pass=* religion=* tracktype=* area=* sport=* piste=* admin_level=* aerialway=* lock=* roof=* military=* wood=* --tag-filter accept-relations natural=water place=islet --used-node --rbf file="${input_map_file}" --tag-filter accept-ways highway=* waterway=* landuse=* natural=* place=* --tag-filter accept-relations highway=* waterway=* landuse=* natural=* place=* --used-node --merge --mapfile-writer file="${output_map_file}" type=hd zoom-interval-conf=13,13,13,14,14,14 threads=4 tag-conf-file="${tag_file}")
