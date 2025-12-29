#!/usr/bin/env python3

import ctypes
import math
import os
import argparse
import subprocess
import tempfile
import numpy as np
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

# config
bin_dir = "osmosis/bin"
tag_file = "tag-igpsport.xml"
cmd = './osmosis --rbf file={input_map_file} --tag-filter reject-ways amenity=* highway=* building=* natural=* landuse=* leisure=* shop=* waterway=* man_made=* railway=* tourism=* barrier=* boundary=* power=* historic=* emergency=* office=* craft=* healthcare=* aeroway=* route=* public_transport=* bridge=* tunnel=* addr:housenumber=* addr:street=* addr:city=* addr:postcode=* name=* ref=* surface=* access=* foot=* bicycle=* motor_vehicle=* oneway=* lit=* width=* maxspeed=* mountain_pass=* religion=* tracktype=* area=* sport=* piste=* admin_level=* aerialway=* lock=* roof=* military=* wood=* --tag-filter accept-relations natural=water place=islet --used-node --rbf file={input_map_file} --tag-filter accept-ways highway=* waterway=* landuse=* natural=* place=* --tag-filter accept-relations highway=* waterway=* landuse=* natural=* place=* --used-node --merge --mapfile-writer file={output_map_file} type=hd zoom-interval-conf=13,13,13,14,14,14 threads=4 tag-conf-file={tag_file}'

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
except:
    # it is a file, not an URL
    input_map_file = os.path.realpath(args.i)
tag_file = os.path.realpath(tag_file)
tmp_map_file = os.path.realpath("tmp.map")
bin_dir = os.path.realpath(bin_dir)

# run
cmd = cmd.format(input_map_file=input_map_file, output_map_file=tmp_map_file, tag_file=tag_file)
subprocess.run(cmd.split(' '), cwd=bin_dir)

# calc name
class MapsForgeHeader(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("magic_byte", ctypes.c_char * 20),
        ("header_size", ctypes.c_uint32),
        ("file_version", ctypes.c_uint32),
        ("file_size", ctypes.c_uint64),
        ("date_of_creation", ctypes.c_uint64),
        ("minLat", ctypes.c_int32),
        ("minLon", ctypes.c_int32),
        ("maxLat", ctypes.c_int32),  # most nothern point
        ("maxLon", ctypes.c_int32),
        ("tile_size", ctypes.c_uint16),
    ]

# with leading zeros, 3digits
def intToB36(number):
    return '0' * (3 - len(np.base_repr(number, base=36))) + np.base_repr(number, base=36)

def merY(lat):
    lat_rad = (lat * math.pi) / 180
    return (1 - math.log(math.tan(lat_rad) + (1/math.cos(lat_rad))) / math.pi) / 2


header = MapsForgeHeader.from_buffer_copy(Path(tmp_map_file).read_bytes())

n = (1<<13)
lon_start = math.floor(((header.minLon/1000000 + 180) / 360) * n)
lat_start = math.floor(merY(header.maxLat/1000000) * n)
lon_end = math.floor(((header.maxLon/1000000 + 180) / 360) * n)
lat_end = math.floor(merY(header.minLat/1000000) * n)
lon_diff = abs(lon_start - lon_end)
lat_diff = abs(lat_start - lat_end)

prefix = args.c + args.s
date = datetime.today().strftime('%y%m%d')
postfix = intToB36(lon_start) + intToB36(lat_start) + intToB36(lon_diff) + intToB36(lat_diff)

out_map_file = os.path.realpath(prefix + date + postfix + ".map")

os.rename(tmp_map_file, out_map_file)
