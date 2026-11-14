"""Import DynAdjust and DynaML files into a SQLite database.

The module keeps the original public importer names for scripts that import
Dyna2db, while separating database, XML, and text-file parsing concerns.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import shapefile as shp
import xmltodict


TABLES = (
    "FILES",
    "DNA_STATION",
    "DNA_MEASUREMENT",
    "DNA_BASELINES",
    "DNA_DIRECTIONS",
    "ADJ_STATION",
    "ADJ_MEASUREMENT",
    "ADJ_ADJUSTMENT_STATS",
    "X_G_Y_COMPONENTS",
    "APU_STATION",
)


def _quote_identifier(identifier: str) -> str:
    """Quote a SQLite identifier, escaping embedded quote characters."""
    return '"' + identifier.replace('"', '""') + '"'


def _connect(db: str | os.PathLike[str]) -> sqlite3.Connection:
    return sqlite3.connect(db)


def delete_DynaML_db(db: str | os.PathLike[str]) -> None:
    """Drop all tables managed by this module."""
    with _connect(db) as conn:
        for table in TABLES:
            conn.execute(f"DROP TABLE IF EXISTS {_quote_identifier(table)}")


def create_DynaML_db(db: str | os.PathLike[str]) -> None:
    """Create the empty tables used by the importers."""
    with _connect(db) as conn:
        for table in TABLES:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {_quote_identifier(table)} "
                "(ID INTEGER PRIMARY KEY)"
            )


def _column_type(column: str) -> str:
    text_columns = {
        "M", "C", "OUTLIER", "OUTLIER?", "CONST", "DESCRIPTION",
    }
    if column in text_columns or column.startswith("STATION"):
        return "TEXT"
    return "REAL"


def add_tbl_clm(tbl: str, clms: Iterable[str], conn: sqlite3.Connection) -> None:
    """Add missing columns to a dynamically shaped import table."""
    table = _quote_identifier(tbl)
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for column in clms:
        if not column or column in existing:
            continue
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {_quote_identifier(column)} "
            f"{_column_type(column)}"
        )
        existing.add(column)


def fmt4sql(stg: str) -> list[str]:
    """Convert DynAdjust fixed-width headings to SQLite-friendly names."""
    normalized = (
        stg.replace("*", " ")
        .replace(". ID", "_ID ")
        .replace("?", " ")
        .replace(".", "")
        .replace("-", "_")
        .replace("(", "_")
        .replace(",", "_")
        .replace(":", " ")
        .replace("%", "p")
        .replace(")", " ")
        .replace("M Station 1", "M  Station 1")
        .upper()
    )
    return [part.strip().replace(" ", "_") for part in normalized.split("  ") if part.strip()]


def list2sql(clms: Sequence[str]) -> str:
    """Return the legacy ``(columns) VALUES (...)`` fragment."""
    if not clms:
        raise ValueError("An INSERT must contain at least one column")
    columns = ", ".join(clms)
    values = ", ".join("?" for _ in clms)
    return f" ({columns}) VALUES ({values})"


def _insert(
    conn: sqlite3.Connection,
    table: str,
    values: Mapping[str, Any],
) -> None:
    """Ensure columns exist and insert one mapping using bound parameters."""
    columns = list(values)
    add_tbl_clm(table, columns, conn)
    names = ", ".join(_quote_identifier(name) for name in columns)
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(
        f"INSERT INTO {_quote_identifier(table)} ({names}) VALUES ({placeholders})",
        [values[name] for name in columns],
    )


def add_file_ref(f: str | os.PathLike[str], tbl: str, conn: sqlite3.Connection) -> None:
    """Attach rows without a source reference to the imported file record."""
    filename = os.fspath(f)
    add_tbl_clm(tbl, ["FILES_ID"], conn)
    add_tbl_clm("FILES", ["FILE_NAME"], conn)
    row = conn.execute(
        'SELECT ID FROM FILES WHERE FILE_NAME = ?', (filename,)
    ).fetchone()
    if row is None:
        cursor = conn.execute('INSERT INTO FILES (FILE_NAME) VALUES (?)', (filename,))
        file_id = cursor.lastrowid
    else:
        file_id = row[0]
    conn.execute(
        f'UPDATE {_quote_identifier(tbl)} SET FILES_ID = ? WHERE FILES_ID IS NULL',
        (file_id,),
    )


def _read_xml(path: str | os.PathLike[str], **kwargs: Any) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as stream:
        return xmltodict.parse(stream.read(), **kwargs)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def stn_xml2db(f: str | os.PathLike[str], db: str | os.PathLike[str]) -> None:
    """Import DynaML stations, including their coordinate fields."""
    xml = _read_xml(f, process_comments=True, comment_key="COMMENT")
    stations = _as_list(xml["DnaXmlFormat"].get("DnaStation"))
    with _connect(db) as conn:
        for station in stations:
            record = dict(station)
            coordinates = record.pop("StationCoord", {}) or {}
            if not isinstance(coordinates, Mapping):
                raise ValueError("DnaStation StationCoord must be an XML element")
            record.update(coordinates)
            if record:
                _insert(conn, "DNA_STATION", record)
        add_file_ref(f, "DNA_STATION", conn)


def msr_xml2db(f: str | os.PathLike[str], db: str | os.PathLike[str]) -> None:
    """Import measurements and their direction/baseline child records."""
    xml = _read_xml(f)
    measurements = _as_list(xml["DnaXmlFormat"].get("DnaMeasurement"))
    with _connect(db) as conn:
        for measurement in measurements:
            base_record: dict[str, Any] = {}
            for key, value in measurement.items():
                if key == "Directions":
                    for target in _as_list(value):
                        direction = {"MEASUREMENT_ID": None, **target}
                        # The parent ID is assigned by SQLite after insertion.
                        add_tbl_clm("DNA_DIRECTIONS", direction, conn)
                        columns = list(direction)
                        names = ", ".join(_quote_identifier(name) for name in columns)
                        conn.execute(
                            f"INSERT INTO DNA_DIRECTIONS ({names}) VALUES "
                            f"({', '.join('?' for _ in columns)})",
                            [None, *target.values()],
                        )
                elif key in {"GPSBaseline", "Clusterpoint"}:
                    child = {"MEASUREMENT_ID": None, **value}
                    _insert(conn, "DNA_BASELINES", child)
                else:
                    base_record[key] = value
            if base_record:
                _insert(conn, "DNA_MEASUREMENT", base_record)
                measurement_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.execute(
                    "UPDATE DNA_DIRECTIONS SET MEASUREMENT_ID = ? "
                    "WHERE MEASUREMENT_ID IS NULL", (measurement_id,)
                )
                conn.execute(
                    "UPDATE DNA_BASELINES SET MEASUREMENT_ID = ? "
                    "WHERE MEASUREMENT_ID IS NULL", (measurement_id,)
                )
        add_file_ref(f, "DNA_MEASUREMENT", conn)
        add_file_ref(f, "DNA_DIRECTIONS", conn)
        add_file_ref(f, "DNA_BASELINES", conn)


def _parse_number(value: str) -> Any:
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _adj_measurement_values(line: str) -> list[Any]:
    values: list[Any] = [
        line[:2].strip(),
        line[2:20].strip(),
        line[22:40].strip(),
        line[42:60].strip(),
        line[62:67].strip(),
    ]
    values.extend(_parse_number(item.strip()) for item in line[68:106].split("  ") if item.strip())
    values.extend(_parse_number(item.strip()) for item in line[106:].split() if item.strip())
    return values


def import_adj(f: str | os.PathLike[str], db: str | os.PathLike[str]):
    """Import an adjustment report and return its stats, stations and observations."""
    adj_stats: dict[str, Any] = {}
    adj_stns: dict[str, dict[str, Any]] = {}
    adj_obs: dict[int, dict[str, Any]] = {}
    section = ""
    skip_lines = -1
    stats_columns: list[str] = []
    stats_values: list[Any] = []
    station_columns: list[str] = []
    measurement_columns: list[str] = []
    gnss_rows: list[list[Any]] = []

    with _connect(db) as conn, open(f, "r", encoding="utf-8-sig") as adj_file:
        next_observation_id = (conn.execute(
            "SELECT COALESCE(MAX(ID), 0) + 1 FROM ADJ_MEASUREMENT"
        ).fetchone()[0])
        measurement_index = 0
        for line in adj_file:
            if not line.strip() or line.startswith("    "):
                continue
            if line.startswith(("+ Initialising adjustment", "Adjusted Coordinates",
                                "Measurements to Station", "Adjusted Measurements")):
                skip_lines = -1

            if line.startswith("DYNADJUST ADJUSTMENT OUTPUT FILE"):
                section = "stats"
                stats_columns, stats_values = [], []
                skip_lines = 2
            if line.startswith("SOLUTION"):
                skip_lines = 0
            if skip_lines == 0 and section == "stats" and not line.startswith("--"):
                heading = fmt4sql(line)
                if heading:
                    stats_columns.append(heading[0])
                    stats_values.append(line[line.find("  "):].strip())
            if line.startswith("Adjusted Measurements") and section == "stats" and stats_columns:
                _insert(conn, "ADJ_ADJUSTMENT_STATS", dict(zip(stats_columns, stats_values)))
                adj_stats.update(zip(stats_columns, stats_values))
                section = ""

            if line.startswith("Station             Const"):
                section = "stations"
                station_columns = fmt4sql(line)
                add_tbl_clm("ADJ_STATION", station_columns, conn)
                skip_lines = 2
            elif skip_lines == 0 and section == "stations":
                values: list[Any] = [line[:20].strip(), *line[20:].split()]
                if len(values) > len(station_columns):
                    values = values[:len(station_columns) - 1] + [
                        " ".join(values[len(station_columns) - 1:])
                    ]
                record = dict(zip(station_columns, values))
                if record:
                    _insert(conn, "ADJ_STATION", record)
                    station_name = str(values[0])
                    adj_stns[station_name] = record

            if line.startswith("M Station 1           Station 2           Station 3"):
                section = "measurements"
                measurement_columns = fmt4sql(line)
                add_tbl_clm("ADJ_MEASUREMENT", measurement_columns, conn)
                component_columns = ["OBSERVATION_ID", *fmt4sql(line[65:])]
                add_tbl_clm("X_G_Y_COMPONENTS", component_columns, conn)
                skip_lines = 2
                measurement_index = 0
                gnss_rows = []
            elif skip_lines == 0 and section == "measurements":
                values = _adj_measurement_values(line)
                if not values[0]:
                    if skip_lines > 0:
                        skip_lines -= 1
                    continue
                obs_record = {"OBS_ID": next_observation_id}
                obs_record.update(zip(measurement_columns, values))
                adj_obs[measurement_index] = obs_record
                measurement_index += 1

                if values[0] in {"X", "Y", "G"}:
                    component_values = [next_observation_id, *values[4:]]
                    component_names = component_columns[:len(component_values)]
                    _insert(conn, "X_G_Y_COMPONENTS", dict(zip(component_names, component_values)))
                    gnss_rows.append(values)
                    if len(gnss_rows) == 3:
                        average = list(values)
                        if len(average) > 4:
                            average[4] = "Avg"
                        for index in range(5, min(7, len(average))):
                            average[index] = ""
                        for index in range(7, min(len(average), len(gnss_rows[0]) - 2)):
                            numeric = [row[index] for row in gnss_rows
                                       if index < len(row) and isinstance(row[index], (int, float))]
                            if numeric:
                                average[index] = round(sum(abs(item) for item in numeric) / len(gnss_rows), 4)
                        values = average
                        gnss_rows = []
                    else:
                        if skip_lines > 0:
                            skip_lines -= 1
                        continue

                record = dict(zip(measurement_columns, values))
                if record:
                    _insert(conn, "ADJ_MEASUREMENT", record)
                    next_observation_id += 1
            if skip_lines > 0:
                skip_lines -= 1

        for table in ("ADJ_ADJUSTMENT_STATS", "ADJ_STATION", "ADJ_MEASUREMENT", "X_G_Y_COMPONENTS"):
            add_file_ref(f, table, conn)
    return adj_stats, adj_stns, adj_obs


def import_apu(f: str | os.PathLike[str], db: str | os.PathLike[str]) -> dict[str, dict[str, Any]]:
    """Import positional-uncertainty station records and return them by station."""
    apu_stns: dict[str, dict[str, Any]] = {}
    columns: list[str] = []
    skip_lines = -1
    header = "Station                     Latitude      Longitude    Hz PosU    Vt PosU   Semi-major   Semi-minor  Orientation        Variance(X)        Variance(Y)        Variance(Z)"
    with _connect(db) as conn, open(f, "r", encoding="utf-8-sig") as apu_file:
        for line in apu_file:
            if not line.strip():
                skip_lines = -1
            if line.startswith(header):
                columns = fmt4sql(line)
                add_tbl_clm("APU_STATION", columns, conn)
                skip_lines = 2
            elif skip_lines == 0 and columns:
                values = [line[:20].strip(), *line[20:].split()]
                record = dict(zip(columns, values))
                if record:
                    _insert(conn, "APU_STATION", record)
                    apu_stns[str(values[0])] = record
                skip_lines = 3
            if skip_lines > 0:
                skip_lines -= 1
        add_file_ref(f, "APU_STATION", conn)
    return apu_stns


def count_sigfigs(n: float) -> int:
    """Return the number of decimal places needed to represent a float."""
    if not math.isfinite(float(n)):
        return 0
    text = format(float(n), ".15f").rstrip("0").rstrip(".")
    return len(text.partition(".")[2]) if "." in text else 0


def isnumber(x: Any) -> bool:
    if x is None or x == "":
        return False
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def defineshpfields(k: str, v: Any, clms: OrderedDict | dict) -> OrderedDict | dict:
    """Track shapefile field types and suitable numeric precision."""
    if k not in clms:
        if isnumber(v):
            number = float(v)
            clms[k] = {
                "name": k, "type": "N",
                "size": max(1, len(str(number))),
                "decimal": count_sigfigs(number),
            }
        else:
            clms[k] = {"name": k, "type": "C"}
    elif clms[k]["type"] == "N" and isnumber(v):
        number = float(v)
        clms[k]["size"] = max(clms[k]["size"], len(str(number)))
        clms[k]["decimal"] = max(clms[k]["decimal"], count_sigfigs(number))
    elif clms[k]["type"] == "N" and not isnumber(v):
        clms[k] = {"name": k, "type": "C"}
    return clms


def _flatten_measurement(measurement: Mapping[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in measurement.items():
        if key in {"Clusterpoint", "GPSBaseline"} and isinstance(value, Mapping):
            flattened.update(value)
        elif key == "Directions":
            directions = _as_list(value)
            if directions and isinstance(directions[0], Mapping):
                flattened.update(directions[0])
        else:
            flattened[key] = value
    return flattened


def _write_shape_records(writer: Any, columns: Mapping[str, Any], records: Iterable[Mapping[str, Any]]) -> None:
    names = list(columns)
    for record in records:
        writer.record(*(record.get(name, "") for name in names))


def dynaml2shp(f: str | os.PathLike[str], db: str | os.PathLike[str] | None = None) -> None:
    """Export DynaML station and measurement XML to point/line shapefiles."""
    del db  # Kept for compatibility with the original call signature.
    source = os.fspath(f)
    output_dir = Path("shp Layers")
    output_dir.mkdir(exist_ok=True)
    stations: dict[str, dict[str, Any]] = {}

    if source.endswith("stn.xml"):
        xml = _read_xml(source)
        for station in _as_list(xml["DnaXmlFormat"].get("DnaStation")):
            record = dict(station)
            record.update(record.pop("StationCoord", {}) or {})
            if record.get("Name"):
                stations[str(record["Name"])] = record
        columns: OrderedDict[str, dict[str, Any]] = OrderedDict(
            [("Name", {"name": "Name", "type": "C"})]
        )
        for station in stations.values():
            for key, value in station.items():
                defineshpfields(key, value, columns)
        stem = source.replace(".", "_") + "_point"
        writer = shp.Writer(stem, shapeType=shp.POINT)
        for field in columns.values():
            if field["type"] == "N":
                writer.field(field["name"], "N", size=max(1, min(20, field["size"])),
                             decimal=min(15, field["decimal"]))
            else:
                writer.field(field["name"], "C")
        for station in stations.values():
            writer.point(float(station["XAxis"]), float(station["YAxis"]))
        _write_shape_records(writer, columns, stations.values())
        writer.close()

    measurement_path = source.replace("stn.xml", "msr.xml")
    if stations and os.path.exists(measurement_path):
        xml = _read_xml(measurement_path)
        measurements = [
            _flatten_measurement(item)
            for item in _as_list(xml["DnaXmlFormat"].get("DnaMeasurement"))
        ]
        columns = OrderedDict((key, {"name": key, "type": "C"})
                              for key in ("First", "Second", "Target"))
        for measurement in measurements:
            for key, value in measurement.items():
                defineshpfields(key, value, columns)
        stem = measurement_path.replace(".", "_") + "_line"
        writer = shp.Writer(stem, shapeType=shp.POLYLINE)
        for field in columns.values():
            if field["type"] == "N":
                writer.field(field["name"], "N", size=max(1, min(20, field["size"])),
                             decimal=min(15, field["decimal"]))
            else:
                writer.field(field["name"], "C")
        for measurement in measurements:
            station_names = [measurement.get(name) for name in ("First", "Second", "Target")]
            points = []
            for name in station_names:
                if name is not None and str(name) in stations:
                    station = stations[str(name)]
                    points.append([float(station["XAxis"]), float(station["YAxis"])])
            if len(points) == 1:
                points.append(points[0])
            if len(points) >= 2:
                writer.line([points])
                writer.record(*(measurement.get(name, "") for name in columns))
        writer.close()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import adjustment files into a database.")
    for name, description in (
        ("stn", "DynaML station XML file (.stn.xml)"),
        ("msr", "DynaML measurement XML file (.msr.xml)"),
        ("adj", "DynAdjust adjustment file (.adj)"),
        ("apu", "DynAdjust positional uncertainty file (.apu)"),
    ):
        parser.add_argument(f"--{name}", help=description)
        parser.add_argument(f"--{name}2", help=f"Second {description[0].lower()}{description[1:]}")
    return parser.parse_args(argv)


def _import_path(path: str, db: str) -> None:
    lowered = path.lower()
    if lowered.endswith((".stn.xml", "stn.xml")):
        stn_xml2db(path, db)
    elif lowered.endswith((".msr.xml", "msr.xml")):
        msr_xml2db(path, db)
    elif lowered.endswith(".adj"):
        import_adj(path, db)
    elif lowered.endswith(".apu"):
        import_apu(path, db)


def _discover_inputs(root: Path) -> list[Path]:
    suffixes = (".stn.xml", "stn.xml", ".msr.xml", "msr.xml", ".adj", ".apu")
    return sorted(
        (path for path in root.rglob("*") if path.is_file()
         and path.name.lower().endswith(suffixes)
         and path.name.lower() != "network.db"),
        key=lambda path: str(path).lower(),
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    db = "network.db"
    delete_DynaML_db(db)
    create_DynaML_db(db)
    explicit = [getattr(args, name) for name in
                ("stn", "msr", "adj", "apu", "stn2", "msr2", "adj2", "apu2")]
    inputs = [path for path in explicit if path]
    if inputs:
        for path in inputs:
            _import_path(path, db)
    else:
        for path in _discover_inputs(Path.cwd()):
            _import_path(str(path), db)


if __name__ == "__main__":
    main()
