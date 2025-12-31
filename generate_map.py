#!/usr/bin/env python3

import ctypes
import math
import os
import argparse
import subprocess
import pprint
import numpy as np
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

# config
bin_dir = "osmosis/bin"
tag_file = "tag-igpsport.xml"
# cmd = './osmosis --rbf file={input_map_file} --mapfile-writer file={output_map_file} type=hd zoom-interval-conf=13,13,13,14,14,14 threads=4 tag-conf-file={tag_file}'

# cmd = ('./osmosis --rbf file={input_map_file} '
#        '--tag-filter reject-ways amenity=* highway=* building=* natural=* landuse=* leisure=* shop=* waterway=* man_made=* railway=* tourism=* barrier=* boundary=* power=* historic=* emergency=* office=* craft=* healthcare=* aeroway=* route=* public_transport=* bridge=* tunnel=* addr:housenumber=* addr:street=* addr:city=* addr:postcode=* name=* ref=* surface=* access=* foot=* bicycle=* motor_vehicle=* oneway=* lit=* width=* maxspeed=* mountain_pass=* religion=* tracktype=* area=* sport=* piste=* admin_level=* aerialway=* lock=* roof=* military=* wood=* --tag-filter accept-relations natural=water place=islet '
#        '--used-node '
#        '--rbf file={input_map_file} --tag-filter accept-ways highway=* waterway=* landuse=* natural=* place=* '
#        '--tag-filter accept-relations highway=* waterway=* landuse=* natural=* place=* '
#        '--used-node '
#        '--merge '
#        '--mapfile-writer file={output_map_file} type=hd zoom-interval-conf=13,13,13,14,14,14 threads=4 tag-conf-file={tag_file}')

cmd = (
    './osmosis --rbf file={input_map_file} workers=4 '
    '--tag-filter accept-ways highway=* waterway=* landuse=* natural=* place=* '
    '--tag-filter accept-relations highway=* waterway=* landuse=* natural=* place=* '
    '--used-node '
    '--mapfile-writer file={output_map_file} type=hd zoom-interval-conf=13,13,13,14,14,14 threads=4 tag-conf-file={tag_file}'
)

if not os.path.isdir(bin_dir):
    print("setup osmosis first")
    exit(1)

# parser
parser = argparse.ArgumentParser(
    description="Usage: -i <input_map_file> -c <country> -s <state>"
)
parser.add_argument("-i", required=True, type=str, help="input map file")
parser.add_argument("-c", required=True, type=str, help="country (e.g. 'DE')")
parser.add_argument("-s", required=True, type=str, help="state (e.g. 0000)")
args = parser.parse_args()

# paths
try:
    result = urlparse(args.i)
    if all([result.scheme, result.netloc]):
        # should be a URL
        input_map_file = args.i
    else:
        raise "Not a URL"
except:
    # probably a file if not an URL
    input_map_file = os.path.realpath(args.i)
tag_file = os.path.realpath(tag_file)
tmp_map_file = os.path.realpath("tmp.map")
bin_dir = os.path.realpath(bin_dir)

# make sure tmp is not in ram
temp_dir = Path("tmp").mkdir(parents=True, exist_ok=True)
os.environ["JAVA_TOOL_OPTIONS"] = "-Djava.io.tmpdir=" + os.path.realpath("tmp")
os.environ["_JAVA_OPTIONS"] = "-Xmx8g"

# run
cmd = cmd.format(
    input_map_file=input_map_file, output_map_file=tmp_map_file, tag_file=tag_file
)
print("running" + cmd)
process = subprocess.run(cmd.split(" "), cwd=bin_dir)

if process.returncode != 0:
    exit(process.returncode)

class MapsForgeHeader:
    magic_byte: str
    header_size: int
    file_version: int
    file_size: int
    date_of_creation: datetime
    minLat: int
    minLon: int
    maxLat: int
    maxLon: int
    tile_size: int
    projection: str
    flags: int
    mapStartLat: int
    mapStartLon: int
    start_zoom_level: int
    language: str
    comment: str
    created_by: str
    poiTags: list
    wayTags: list
    zoom_interval_configs: list


def parseMapsForgeHeader(file: Path) -> MapsForgeHeader:

    def parseVBEU(data: bytes):
        idx = 0
        value = 0
        while data[idx] & 0x80:
            value += (data[idx] & 0x7F) << (7 * idx)
            idx += 1
        value += (data[idx] & 0x7F) << (7 * idx)
        idx += 1

        return value, idx

    def parseVBES(data: bytes):
        idx = 0
        value = 0
        while data[idx] & 0x80:
            value += (data[idx] & 0x7F) << (7 * idx)
            idx += 1
        value += (data[idx] & 0x3F) << (7 * idx)
        value *= -1 if data[idx] & 0x40 else 1
        idx += 1

        return value, idx

    data = open(file, "rb").read(2000)
    header = MapsForgeHeader()
    idx = 0
    header.magic_byte = data[idx : idx + 20]
    idx += 20
    header.header_size = int.from_bytes(data[idx : idx + 4])
    idx += 4

    assert header.header_size < 1900, "didn't read enough bytes"

    header.file_version = int.from_bytes(data[idx : idx + 4])
    idx += 4
    header.file_size = int.from_bytes(data[idx : idx + 8])
    idx += 8
    header.date_of_creation = datetime.fromtimestamp(
        int.from_bytes(data[idx : idx + 8]) / 1000
    )
    idx += 8
    header.minLat = int.from_bytes(data[idx : idx + 4], signed=True) / 10**6
    idx += 4
    header.minLon = int.from_bytes(data[idx : idx + 4], signed=True) / 10**6
    idx += 4
    header.maxLat = int.from_bytes(data[idx : idx + 4], signed=True) / 10**6
    idx += 4
    header.maxLon = int.from_bytes(data[idx : idx + 4], signed=True) / 10**6
    idx += 4
    header.tile_size = int.from_bytes(data[idx : idx + 2])
    idx += 2

    strlen, used_bytes = parseVBEU(data[idx:])
    idx += used_bytes
    header.projection = data[idx : idx + strlen]
    idx += strlen

    flags = data[idx]
    header.flags = flags
    idx += 1

    if flags & 0x40:
        header.mapStartLat = int.from_bytes(data[idx : idx + 4], signed=True) / 10**6
        idx += 4
        header.mapStartLon = int.from_bytes(data[idx : idx + 4], signed=True) / 10**6
        idx += 4

    if flags & 0x20:
        header.start_zoom_level = int.from_bytes(data[idx : idx + 1])
        idx += 1

    if flags & 0x10:
        strlen, used_bytes = parseVBEU(data[idx:])
        idx += used_bytes
        header.language = data[idx : idx + strlen]
        idx += strlen

    if flags & 0x08:
        strlen, used_bytes = parseVBEU(data[idx:])
        idx += used_bytes
        header.comment = data[idx : idx + strlen]
        idx += strlen

    if flags & 0x04:
        strlen, used_bytes = parseVBEU(data[idx:])
        idx += used_bytes
        header.created_by = data[idx : idx + strlen]
        idx += strlen

    if flags & 0x03:
        print("parse error, future usage fileds")

    poiTagsCnt = int.from_bytes(data[idx : idx + 2])
    idx += 2
    header.poiTags = []
    for i in range(poiTagsCnt):
        strlen, used_bytes = parseVBEU(data[idx:])
        idx += used_bytes
        tag = data[idx : idx + strlen]
        idx += strlen
        header.poiTags.append(tag)
    header.poiTags.sort()

    wayTagsCnt = int.from_bytes(data[idx : idx + 2])
    idx += 2
    header.wayTags = []
    for i in range(wayTagsCnt):
        strlen, used_bytes = parseVBEU(data[idx:])
        idx += used_bytes
        tag = data[idx : idx + strlen]
        idx += strlen
        header.wayTags.append(tag)
    header.wayTags.sort()

    amount_zoom_intervals = int.from_bytes(data[idx : idx + 1])
    idx += 1

    header.zoom_interval_configs = []
    for i in range(amount_zoom_intervals):
        basezoom = int.from_bytes(data[idx : idx + 1])
        idx += 1
        minzoom = int.from_bytes(data[idx : idx + 1])
        idx += 1
        maxzoom = int.from_bytes(data[idx : idx + 1])
        idx += 1
        absstart = int.from_bytes(data[idx : idx + 8])
        idx += 8
        sizesub = int.from_bytes(data[idx : idx + 8])
        idx += 8
        header.zoom_interval_configs.append(
            {
                "basezoom": basezoom,
                "minzoom": minzoom,
                "maxzoom": maxzoom,
                "absstart": absstart,
                "sizesub": sizesub,
            }
        )

    # assert(idx - 24 == header.header_size)

    return header


# with leading zeros, 3digits
def intToB36(number):
    return "0" * (3 - len(np.base_repr(number, base=36))) + np.base_repr(
        number, base=36
    )


def merY(lat):
    lat_rad = (lat * math.pi) / 180
    return (1 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2


header = parseMapsForgeHeader(Path(tmp_map_file))
pprint.pp("generated file:")
pprint.pp(vars(header))

# some checks if file was correctly created
assert b"mapsforge binary OSM" == header.magic_byte
assert os.path.getsize(tmp_map_file) == header.file_size


n = 1 << 13
lon_start = math.floor(((header.minLon + 180) / 360) * n)
lat_start = math.floor(merY(header.maxLat) * n)
lon_end = math.floor(((header.maxLon + 180) / 360) * n)
lat_end = math.floor(merY(header.minLat) * n)
lon_diff = abs(lon_start - lon_end)
lat_diff = abs(lat_start - lat_end)

prefix = args.c + args.s
date = datetime.today().strftime("%y%m%d")
postfix = (
    intToB36(lon_start) + intToB36(lat_start) + intToB36(lon_diff) + intToB36(lat_diff)
)

out_map_file = os.path.realpath(prefix + date + postfix + ".map")

os.rename(tmp_map_file, out_map_file)
