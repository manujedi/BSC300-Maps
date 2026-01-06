#!/bin/bash
set -e

./osmosis/osmconvert graz.pbf -o=tmp.o5m

osmosis/osmfilter -v tmp.o5m \
--keep="highway=primary =primary_link =secondary =secondary_link =tertiary =tertiary_link =trunk =trunk_link =cycleway =living_street =residential =road =track =unclassified" \
--keep="highway=service and ( bicycle=designated or bicycle=yes or bicycle=permissive )" \
--keep="highway=footway and ( bicycle=designated or bicycle=yes or bicycle=permissive )" \
--keep="highway=bridleway and ( bicycle=designated or bicycle=yes or bicycle=permissive )" \
--keep="highway=path and ( bicycle=designated or bicycle=yes or bicycle=permissive )" \
--keep="highway=pedestrian and ( bicycle=designated or bicycle=yes or bicycle=permissive )" \
--keep="highway=unclassified and ( bicycle=designated or bicycle=yes or bicycle=permissive )" \
--keep="sidewalk:*:bicycle=yes" \
--keep="waterway= landuse= natural= leisure=" \
--keep="route=bicycle =mtb" \
--keep="cycleway:*=lane :*=track *:=shared_lane *:=share_busway *:=separate *:=crossing *:=shoulder *:=link *:=traffic_island" \
--keep="bicycle_road=yes" \
--keep="cyclestreet=yes" \
--out-o5m > tmp1.o5m

osmosis/osmfilter -v tmp1.o5m --modify-tags=" \
highway=trunk_link to =primary \
highway=trunk to =primary \
highway=primary_link to =primary \
highway=tertiary_link to =tertiary \
highway=secondary_link to =secondary \
highway=trunk_link to =trunk \
highway=footway to =cycleway \
highway=bridleway to =cycleway \
highway=sidewalk to =cycleway \
highway=path to =cycleway \
highway=pedestrian to =cycleway \
highway=unclassified to =cycleway \
leisure=garden to landuse=grass \
leisure=playground to landuse=grass \
leisure=park to landuse=grass \
landuse=orchard to =grass \
landuse=allotments to =grass \
landuse=farmland to =grass \
landuse=flowerbed to =grass \
landuse=meadow to =grass \
landuse=plant_nursery to =grass \
landuse=vineyard to =grass \
landuse=greenfield to =grass \
landuse=village_green to =grass \
landuse=greenery to =grass \
landuse=cemetery to =grass \
natural=scrub to landuse=grass \
" \
--drop-author --drop-version --out-o5m > tmp2.o5m


./osmosis/osmconvert tmp2.o5m -o=tmp_filtered.pbf


/usr/bin/time -v python generate_map.py -i tmp_filtered.pbf -c "TS" -s "0000" -t tags_with_green_stuff.xml
