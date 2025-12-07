#!/bin/bash

# If osmosis environment needs to be created, the below versions of the tools will be used
OSMOSIS_VERSION="0.49.2"
MAPSFORGE_VERSION="0.25.0"
# Used shared memory to improve performance (requires free RAM space)
TEMP_JAVA_DIR_PATH="/dev/shm/"

BIN_DIR=osmosis

TEMP_DIR="./tmp/"
mkdir -p ${TEMP_DIR}

# Download latest Osmosis
wget https://github.com/openstreetmap/osmosis/releases/download/${OSMOSIS_VERSION}/osmosis-${OSMOSIS_VERSION}.zip -O ${TEMP_DIR}/osmosis.zip
unzip  ${TEMP_DIR}/osmosis.zip -d ${TEMP_DIR}/osmosis
mv ${TEMP_DIR}/osmosis/osmosis*/ ${BIN_DIR}

# Download latest MapsForge MapWriter plugin and place plugin in Osmosis plugins directory
mkdir -p ${BIN_DIR}/bin/plugins
wget https://repo1.maven.org/maven2/org/mapsforge/mapsforge-map-writer/${MAPSFORGE_VERSION}/mapsforge-map-writer-${MAPSFORGE_VERSION}-jar-with-dependencies.jar -P ${BIN_DIR}/bin/plugins/

