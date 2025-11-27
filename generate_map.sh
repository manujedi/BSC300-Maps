#!/bin/bash

# If osmosis environment needs to be created, the below versions of the tools will be used
OSMOSIS_VERSION="0.49.2"
MAPSFORGE_VERSION="0.24.1"
# Used shared memory to improve performance (requires free RAM space)
TEMP_JAVA_DIR_PATH="/dev/shm/"

BIN_DIR=osmosis

# Initialize variables
input_map_file=""
output_map_file=""
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Check if both parameters are provided
if [[ -z "$input_map_file" || -z "$output_map_file" ]]; then
    echo "Error: Both -i (input map file) and -o (output map file) must be specified."
    echo "Usage: $0 -i <input_map_file> -o <output_map_file>"
    exit 2
fi

# Check if input file exists
if [ ! -f "$input_map_file" ]; then
    echo "Error: Input map file '$input_map_file' does not exist."
    exit 3
fi


# Check if binary files exist
if [ ! -d "${BIN_DIR}" ]; then

    TEMP_DIR=$(mktemp -d)

    # Delete the temporary directory
    trap 'rm -rf '"$TEMP_DIR"'' EXIT

    # Download latest Osmosis
    wget https://github.com/openstreetmap/osmosis/releases/download/${OSMOSIS_VERSION}/osmosis-${OSMOSIS_VERSION}.zip -O ${TEMP_DIR}/osmosis.zip
    unzip  ${TEMP_DIR}/osmosis.zip -d ${TEMP_DIR}/osmosis
    mv ${TEMP_DIR}/osmosis/osmosis*/ ${BIN_DIR}

    # Download latest MapsForge MapWriter plugin and place plugin in Osmosis plugins directory
    mkdir -p ${BIN_DIR}/bin/plugins
    wget https://repo1.maven.org/maven2/org/mapsforge/mapsforge-map-writer/${MAPSFORGE_VERSION}/mapsforge-map-writer-${MAPSFORGE_VERSION}-jar-with-dependencies.jar -P ${BIN_DIR}/bin/plugins/
fi

input_map_file="$(realpath ${input_map_file})"
output_map_file="$(realpath ${output_map_file}).map"

TEMP_JAVA_DIR=$(mktemp -d -p ${TEMP_JAVA_DIR_PATH})
trap 'rm -rf '"$TEMP_JAVA_DIR"'' EXIT
export JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=${TEMP_JAVA_DIR}"

(cd ${BIN_DIR}/bin && ./osmosis --rbf file="${input_map_file}" --tag-filter reject-ways amenity=* highway=* building=* natural=* landuse=* leisure=* shop=* waterway=* man_made=* railway=* tourism=* barrier=* boundary=* power=* historic=* emergency=* office=* craft=* healthcare=* aeroway=* route=* public_transport=* bridge=* tunnel=* addr:housenumber=* addr:street=* addr:city=* addr:postcode=* name=* ref=* surface=* access=* foot=* bicycle=* motor_vehicle=* oneway=* lit=* width=* maxspeed=* mountain_pass=* religion=* tracktype=* area=* sport=* piste=* admin_level=* aerialway=* lock=* roof=* military=* wood=* --tag-filter accept-relations natural=water place=islet --used-node --rbf file="${input_map_file}" --tag-filter accept-ways highway=* waterway=* landuse=* natural=* place=* --tag-filter accept-relations highway=* waterway=* landuse=* natural=* place=* --used-node --merge --mapfile-writer file="${output_map_file}" type=hd zoom-interval-conf=13,13,13,14,14,14 threads=4 tag-conf-file="${SCRIPT_PATH}/tag-igpsport.xml")
