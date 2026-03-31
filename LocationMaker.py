import json
import math
import re
from urllib.request import urlopen
from pathlib import Path

BUILDINGS_URL = "https://api.mazemap.com/api/buildings/?campusid=309"
POIS_URL = "https://api.mazemap.com/api/campus/309/pois/?fromid=0&srid=900913"

BUILDINGS_SOURCE = Path("buildings.txt")
POIS_SOURCE = Path("pois.txt")


from urllib.request import Request, urlopen
import json

def fetch_data(url):
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def load_data(local_path, fallback_url):
    if local_path.exists():
        with local_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return fetch_data(fallback_url)


def split_building_name(full_name):
    clean_full_name = (full_name or "").strip()
    if " - " not in clean_full_name:
        return "", clean_full_name
    number, name = clean_full_name.split(" - ", 1)
    return number.strip(), name.strip()


def polygon_centroid_lon_lat(coordinates):
    points = []
    for ring in coordinates or []:
        for point in ring:
            if len(point) == 2:
                points.append(point)

    if not points:
        return None, None

    lon = sum(p[0] for p in points) / len(points)
    lat = sum(p[1] for p in points) / len(points)
    return lon, lat


def mercator_to_lat_lng(x, y):
    radius = 6378137.0
    lng = (x / radius) * (180.0 / math.pi)
    lat = (2.0 * math.atan(math.exp(y / radius)) - (math.pi / 2.0)) * (180.0 / math.pi)
    return lat, lng


ROOM_IDENTIFIER_PATTERN = re.compile(r"\b([A-Za-z0-9]+\.[A-Za-z0-9]+)\b")


def infer_identifier(poi):
    identifier = (poi.get("identifier") or "").strip()
    if identifier:
        return identifier

    title = (poi.get("title") or "").strip()
    match = ROOM_IDENTIFIER_PATTERN.search(title)
    if match:
        return match.group(1)

    for info in poi.get("infos") or []:
        info_name = (info.get("name") or "").strip()
        match = ROOM_IDENTIFIER_PATTERN.search(info_name)
        if match:
            return match.group(1)

    return ""


def is_code_like_name(value, identifier):
    text = (value or "").strip().upper()
    if not text:
        return True
    if text == identifier.upper():
        return True
    # Names made only from code-ish characters are not useful labels.
    if re.fullmatch(r"[A-Z0-9.\-_/ ]+", text):
        return True
    return False


def pick_best_name(poi, identifier):
    title = (poi.get("title") or "").strip()
    info_names = [
        (info.get("name") or "").strip()
        for info in (poi.get("infos") or [])
        if (info.get("name") or "").strip()
    ]

    for info_name in info_names:
        if not is_code_like_name(info_name, identifier):
            return info_name

    if not is_code_like_name(title, identifier):
        return title

    for info_name in info_names:
        if info_name.upper() != identifier.upper():
            return info_name

    return title or identifier


def extract_buildings(data):
    buildings = {}

    for building in data.get("buildings", []):
        full_name = building.get("name", "")
        number, clean_name = split_building_name(full_name)
        if not number:
            continue

        floor_outline = None
        floors = building.get("floors") or []
        if floors:
            floor_outline = floors[0].get("outline", {}).get("coordinates")

        lon, lat = polygon_centroid_lon_lat(floor_outline)

        buildings[number] = {
            "identifier": number,
            "name": clean_name,
            "full_name": full_name.strip(),
            "latitude": lat,
            "longitude": lon,
        }

    return dict(sorted(buildings.items(), key=lambda item: item[0]))


def extract_pois(data):
    pois = {}

    for poi in data.get("pois", []):
        if poi.get("deleted"):
            continue

        identifier = infer_identifier(poi)
        if not identifier:
            continue

        display_name = pick_best_name(poi, identifier)

        point = poi.get("point", {}).get("coordinates")
        if not point or len(point) != 2:
            continue

        x, y = point
        lat, lng = mercator_to_lat_lng(x, y)

        building_full_name = (poi.get("buildingName") or "").strip()
        parent_identifier, building_name = split_building_name(building_full_name)

        # Extract first POI type name
        poi_types = poi.get("types") or []
        type_name = poi_types[0].get("name") if poi_types else None

        # Handle peopleCapacity: convert 0/null to None (becomes null in JSON)
        capacity = poi.get("peopleCapacity")
        if capacity is None or capacity == 0:
            capacity = None

        pois[identifier] = {
            "identifier": identifier,
            "name": display_name,
            "type": type_name,
            "parent_building": parent_identifier,
            "building_name": building_name,
            "building_full_name": building_full_name,
            "latitude": lat,
            "longitude": lng,
            "floor": (poi.get("floorName") or "").strip(),
            "people_capacity": capacity,
        }

    return dict(sorted(pois.items(), key=lambda item: item[0]))


if __name__ == "__main__":
    print("Loading MazeMap data...")

    buildings_raw = load_data(BUILDINGS_SOURCE, BUILDINGS_URL)
    pois_raw = load_data(POIS_SOURCE, POIS_URL)

    print("Processing buildings...")
    buildings = extract_buildings(buildings_raw)

    print("Processing POIs...")
    pois = extract_pois(pois_raw)

    with open("buildings.json", "w", encoding="utf-8") as f:
        json.dump(buildings, f, indent=4)

    with open("pois.json", "w", encoding="utf-8") as f:
        json.dump(pois, f, indent=4)

    print(f"Saved {len(buildings)} buildings")
    print(f"Saved {len(pois)} POIs with identifiers")