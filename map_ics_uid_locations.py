import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


BUILDING_ALIAS_OVERRIDES = {
    "ARTS": "106",
    "BUSN": "441",
    "CSSE": "241",
    "EZONECENT": "275",
    "EZONENTH": "222",
    "GGGL": "225",
    "HACKH": "103",
    "OCTA": "143",
    "PHYS": "245",
    "SSCI": "352",
    "WTLTS": "210"
}

ONLINE_TEXT_MARKERS = {
    "lecture recording available if unable to attend.",
    "lecture recording available if unable to attend",
}

DIRECT_ID_RE = re.compile(r"\b([A-Za-z0-9]+\.[A-Za-z0-9]+)\b")
ALIAS_ROOM_RE = re.compile(r"^\s*([A-Za-z0-9&\- ]+?)\s*:\s*\[\s*([A-Za-z0-9]+)\s*\]\s*(.*)$")
LOCATION_IN_DESCRIPTION_RE = re.compile(r"(?:^|\n)Location:\s*(.+)", re.IGNORECASE)


def normalize_text(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def split_segments(raw_location: str) -> List[str]:
    parts = [p.strip() for p in re.split(r"\\,", raw_location) if p.strip()]
    return parts or [raw_location.strip()]


def tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[A-Za-z0-9]+", text.lower()) if len(t) > 1]


def build_alias_index(buildings: Dict[str, dict]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for building_id, building in buildings.items():
        name = building.get("name", "")
        full_name = building.get("full_name", "")

        candidates = {
            normalize_text(building_id),
            normalize_text(name),
            normalize_text(full_name),
        }

        words = re.findall(r"[A-Za-z0-9]+", name.upper())
        if words:
            initials = "".join(w[0] for w in words if w and w[0].isalnum())
            if len(initials) >= 2:
                candidates.add(initials)

        for candidate in candidates:
            if candidate and candidate not in index:
                index[candidate] = building_id

    for alias, building_id in BUILDING_ALIAS_OVERRIDES.items():
        index[normalize_text(alias)] = building_id
    return index


def build_room_index(pois: Dict[str, dict]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = defaultdict(list)
    for poi_id in pois:
        if "." in poi_id:
            _, room = poi_id.split(".", 1)
            index[room.upper()].append(poi_id)
    return index


def score_candidate(
    poi_id: str,
    pois: Dict[str, dict],
    buildings: Dict[str, dict],
    label: str,
    preferred_building: Optional[str],
) -> int:
    poi = pois[poi_id]
    building_id = poi.get("parent_building") or poi_id.split(".", 1)[0]
    building_name = (buildings.get(building_id) or {}).get("name", "")
    poi_name = poi.get("name", "")

    score = 0
    if preferred_building and building_id == preferred_building:
        score += 50

    label_tokens = set(tokenize(label))
    if label_tokens:
        target_tokens = set(tokenize(poi_name)) | set(tokenize(building_name))
        score += 10 * len(label_tokens & target_tokens)

    return score


def resolve_segment(
    segment: str,
    pois: Dict[str, dict],
    buildings: Dict[str, dict],
    alias_index: Dict[str, str],
    room_index: Dict[str, List[str]],
) -> Optional[str]:
    direct_match = DIRECT_ID_RE.search(segment)
    if direct_match and direct_match.group(1) in pois:
        return direct_match.group(1)

    alias_match = ALIAS_ROOM_RE.match(segment)
    if not alias_match:
        return None

    alias_raw, room_raw, label = alias_match.groups()
    preferred_building = alias_index.get(normalize_text(alias_raw))
    candidates = room_index.get(room_raw.upper(), [])
    if not candidates:
        return None

    if preferred_building:
        preferred = [c for c in candidates if c.split(".", 1)[0] == preferred_building]
        if len(preferred) == 1:
            return preferred[0]
        if preferred:
            candidates = preferred

    best = max(candidates, key=lambda c: score_candidate(c, pois, buildings, label, preferred_building))
    return best


def unfold_ics_lines(raw_text: str) -> List[str]:
    unfolded: List[str] = []
    for line in raw_text.splitlines():
        if (line.startswith(" ") or line.startswith("\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def parse_ics_events(ics_path: Path) -> List[Dict[str, str]]:
    events: List[Dict[str, str]] = []
    current: Optional[Dict[str, str]] = None

    for line in unfold_ics_lines(ics_path.read_text(encoding="utf-8")):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue

        prop, value = line.split(":", 1)
        key = prop.split(";", 1)[0].upper()
        current[key] = value

    return events


def get_event_location(event: Dict[str, str]) -> str:
    location = (event.get("LOCATION") or "").strip()
    if location:
        return location

    description = (event.get("DESCRIPTION") or "").replace("\\n", "\n")
    match = LOCATION_IN_DESCRIPTION_RE.search(description)
    return match.group(1).strip() if match else ""


def resolve_location(
    raw_location: str,
    pois: Dict[str, dict],
    buildings: Dict[str, dict],
    alias_index: Dict[str, str],
    room_index: Dict[str, List[str]],
) -> str:
    if raw_location.strip().lower() in ONLINE_TEXT_MARKERS:
        return "Online"

    mapped: List[str] = []
    for segment in split_segments(raw_location):
        poi_id = resolve_segment(segment, pois, buildings, alias_index, room_index)
        if poi_id:
            mapped.append(poi_id)

    deduped = list(dict.fromkeys(mapped))
    if deduped:
        return "|".join(deduped)

    return ""


def map_ics_to_txt(
    ics_path: Path,
    output_path: Path,
    buildings: Dict[str, dict],
    pois: Dict[str, dict],
) -> None:
    alias_index = build_alias_index(buildings)
    room_index = build_room_index(pois)

    events = parse_ics_events(ics_path)
    lines: List[str] = []
    resolved = 0

    for i, event in enumerate(events, start=1):
        uid = (event.get("UID") or f"missing_uid_{i}").strip()
        raw_location = get_event_location(event)
        location = resolve_location(raw_location, pois, buildings, alias_index, room_index)
        if location:
            resolved += 1
        lines.append(f"{uid},{location}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Events parsed: {len(events)}")
    print(f"Events resolved: {resolved}")
    print(f"Events unresolved: {len(events) - resolved}")
    print(f"Wrote: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Map ICS event UID to building.poi text output.")
    parser.add_argument(
        "ics",
        nargs="?",
        default="timetables/HotelMario.ics",
        help="Path to ICS file (default: timetables/HotelMario.ics)",
    )
    parser.add_argument("-o", "--output", default=None, help="Output txt path (default: <ics_stem>_uid_locations.txt)")
    parser.add_argument("--buildings", default="buildings.json", help="Path to buildings.json")
    parser.add_argument("--pois", default="pois.json", help="Path to pois.json")
    args = parser.parse_args()

    ics_path = Path(args.ics)
    output_path = Path(args.output) if args.output else Path(f"{ics_path.stem}_uid_locations.txt")
    buildings = json.loads(Path(args.buildings).read_text(encoding="utf-8"))
    pois = json.loads(Path(args.pois).read_text(encoding="utf-8"))

    map_ics_to_txt(ics_path, output_path, buildings, pois)


if __name__ == "__main__":
    main()
