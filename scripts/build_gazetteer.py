"""Build data/sample/gazetteer.csv from the downloads in data/raw/geo/ (FA-06).

Needs the `osm` extra (geopandas):
    uv sync --extra osm --inexact
    uv run python scripts/build_gazetteer.py

Downloads and licences: docs/data-and-privacy.md, section "Geodata".
"""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.ops import nearest_points

from eagleradar.geo.gazetteer import (
    DEFAULT_CSV,
    Place,
    normalize,
    station_variants,
    write_csv,
)

RAW = Path(__file__).parents[1] / "data" / "raw" / "geo"
METRIC = "EPSG:25833"  # UTM 33N, distances in metres
WGS84 = "EPSG:4326"
MAX_KB = 2000  # limit of the pre-commit hook check-added-large-files

# Segments of one name that are closer than this belong to the same street (squares, crossings).
STREET_GAP_M = 300

LANDMARKS = ["town_hall", "hospital", "police", "fire_station"]

# Park and museum railways: their stops ("Hauptbahnhof" in Wuhlheide) are no real stations.
PARK_RAILWAYS = ["narrow_gauge", "miniature_railway"]


def find(pattern: str) -> Path:
    """Newest file in data/raw/geo/ that matches the pattern."""
    files = sorted(RAW.glob(pattern))
    if not files:
        raise SystemExit(
            f"{RAW / pattern} not found. See docs/data-and-privacy.md, section Geodata."
        )
    return files[-1]


def read_localities() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Localities (with the name of their district) and districts."""
    districts = gpd.read_file(find("bezirke.*json"))
    names = {
        int(number): name for number, name in zip(districts.gem, districts.namgem, strict=True)
    }
    localities = gpd.read_file(find("ortsteile.*json"))
    # Code of a locality, e.g. 110000060607: characters 7-8 are the district (06).
    localities["district"] = localities["sch"].str[6:8].astype(int).map(names)
    localities = localities.rename(columns={"nam": "locality"})
    return localities[["locality", "district", "geometry"]], districts


def area_places(localities: gpd.GeoDataFrame, districts: gpd.GeoDataFrame) -> list[Place]:
    places = []
    for row in localities.itertuples():
        point = row.geometry.representative_point()  # always inside the area
        places.append(
            Place(row.locality, "locality", point.y, point.x, "alkis", row.locality, row.district)
        )
    for row in districts.itertuples():
        point = row.geometry.representative_point()
        places.append(Place(row.namgem, "district", point.y, point.x, "alkis", None, row.namgem))
    return places


def with_locality(points: gpd.GeoDataFrame, localities: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add locality and district to points; points outside Berlin are dropped."""
    joined = gpd.sjoin(points, localities.to_crs(points.crs), predicate="within")
    return joined[~joined.index.duplicated()].drop(columns="index_right")


def to_wgs84(points: list) -> list:
    return list(gpd.GeoSeries(points, crs=METRIC).to_crs(WGS84))


def street_places(osm: str, localities: gpd.GeoDataFrame) -> list[Place]:
    """One place per street name and locality, on the street near its middle.

    Segments that are not connected get different part numbers: Clayallee runs through four
    localities but is one street, "Hauptstraße" in Spandau and in Pankow are two.
    """
    roads = gpd.read_file(osm + "gis_osm_roads_free_1.shp", columns=["name"])
    roads = roads[roads["name"].notna()].to_crs(METRIC).reset_index(drop=True)
    roads["line"] = roads.geometry
    # The middle of each segment decides to which locality the segment belongs.
    roads = roads.set_geometry(roads.geometry.interpolate(0.5, normalized=True))
    roads = with_locality(roads, localities)

    keys, points = [], []
    for name, segments in roads.groupby("name", sort=True):
        if not normalize(name):
            continue
        lines = segments["line"].to_numpy()
        areas = shapely.get_parts(shapely.union_all(shapely.buffer(lines, STREET_GAP_M / 2)))
        part = shapely.STRtree(areas).query_nearest(lines, all_matches=False)[1]
        for (locality, district), group in segments.assign(part=part).groupby(
            ["locality", "district"], sort=True
        ):
            # Several separate streets with one name in one locality: keep the longest.
            longest = group["line"].map(lambda g: g.length).groupby(group["part"]).sum().idxmax()
            street = shapely.union_all(group.loc[group["part"] == longest, "line"].to_numpy())
            keys.append((name, locality, district, int(longest), round(street.length)))
            points.append(nearest_points(street, street.centroid)[0])
    return [
        Place(
            name, "street", point.y, point.x, "osm", locality, district, part=part, length_m=length
        )
        for (name, locality, district, part, length), point in zip(
            keys, to_wgs84(points), strict=True
        )
    ]


def landmark_places(osm: str, localities: gpd.GeoDataFrame) -> list[Place]:
    """Town halls, hospitals, police and fire stations."""
    layers = [
        gpd.read_file(osm + f"gis_osm_pois_{kind}free_1.shp", columns=["fclass", "name"])
        for kind in ("", "a_")
    ]
    pois = pd.concat(layers, ignore_index=True)
    # One-word names ("Rathaus", "Bundespolizei") would match any text.
    pois = pois[pois.fclass.isin(LANDMARKS) & pois["name"].str.contains(r"[\s-]", na=False)]
    pois = pois.to_crs(METRIC)
    pois = with_locality(pois.set_geometry(pois.geometry.centroid), localities)

    groups = list(pois.groupby(["name", "locality", "district"], sort=True))
    points = to_wgs84([group.geometry.union_all().centroid for _, group in groups])
    return [
        Place(name, "landmark", point.y, point.x, "osm", locality, district)
        for ((name, locality, district), _), point in zip(groups, points, strict=True)
    ]


def station_places(osm: str, localities: gpd.GeoDataFrame) -> list[Place]:
    """One place per station name; platforms and lines of the same station are merged."""
    stops = gpd.read_file(osm + "gis_osm_transport_free_1.shp", columns=["fclass", "name"])
    stops = stops[stops.fclass.isin(["railway_station", "railway_halt"]) & stops["name"].notna()]
    tracks = gpd.read_file(osm + "gis_osm_railways_free_1.shp", columns=["fclass"])
    stops = gpd.sjoin_nearest(
        stops.to_crs(METRIC).drop(columns="fclass"), tracks.to_crs(METRIC)[["fclass", "geometry"]]
    )
    stops = stops[~stops.index.duplicated()].drop(columns="index_right")
    stops = with_locality(stops[~stops.fclass.isin(PARK_RAILWAYS)], localities)

    # 'Berlin Südkreuz', 'Südkreuz (Ringbahn)', 'U Friedrichstraße' -> name used in posts
    stops["clean"] = (
        stops["name"]
        .str.replace(r"\s*\(.*\)$", "", regex=True)
        .str.replace(r"^(Berlin[ -]+|S\+U |[SU] )", "", regex=True)
    )
    groups = list(stops.groupby("clean", sort=True))
    points = to_wgs84([group.geometry.union_all().centroid for _, group in groups])
    places = []
    for (name, group), point in zip(groups, points, strict=True):
        variants = station_variants(name) + [normalize(original) for original in group["name"]]
        variants = tuple(v for v in dict.fromkeys(variants) if v != normalize(name))
        locality, district = group[["locality", "district"]].mode().iloc[0]
        places.append(Place(name, "station", point.y, point.x, "osm", locality, district, variants))
    return places


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_CSV)
    out = parser.parse_args().out

    osm = f"zip://{find('berlin-*-free.shp.zip').as_posix()}!"
    localities, districts = read_localities()
    places = area_places(localities, districts)
    places += station_places(osm, localities)
    places += landmark_places(osm, localities)
    places += street_places(osm, localities)
    write_csv(places, out)

    print(pd.Series([p.kind for p in places]).value_counts().to_string())
    size = out.stat().st_size / 1024
    print(f"{len(places)} places written to {out} ({size:.0f} KB)")
    if size > MAX_KB:
        raise SystemExit(f"Too large to commit: the limit is {MAX_KB} KB")


if __name__ == "__main__":
    main()
