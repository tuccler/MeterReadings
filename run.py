import json
import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g, abort
from flask_cors import CORS

DATA_DIR = "/data"
DB_PATH = os.path.join(DATA_DIR, "meter_readings.db")

app = Flask(__name__)
CORS(app)

os.makedirs(DATA_DIR, exist_ok=True)

SCHEMA = {
    "devices": "CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, area TEXT NOT NULL, created_at TEXT NOT NULL)",
    "readings": "CREATE TABLE IF NOT EXISTS readings (id INTEGER PRIMARY KEY AUTOINCREMENT, device_id INTEGER NOT NULL, value REAL NOT NULL, timestamp TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE)"
}


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db
    return db


def init_db():
    db = get_db()
    for sql in SCHEMA.values():
        db.execute(sql)
    db.commit()


@app.teardown_appcontext
def close_db(exception=None):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


def validate_device_payload(payload):
    if not isinstance(payload, dict):
        return False
    return bool(payload.get("name")) and bool(payload.get("area"))


def validate_reading_payload(payload):
    if not isinstance(payload, dict):
        return False
    return payload.get("value") is not None


def parse_timestamp(value):
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    return None


def row_to_dict(row):
    return {key: row[key] for key in row.keys()}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/devices", methods=["GET"])
def list_devices():
    db = get_db()
    devices = db.execute("SELECT * FROM devices ORDER BY id").fetchall()
    return jsonify([row_to_dict(device) for device in devices])


@app.route("/devices", methods=["POST"])
def create_device():
    data = request.get_json(silent=True)
    if not validate_device_payload(data):
        return jsonify({"error": "Payload must include name and area."}), 400

    created_at = datetime.now(timezone.utc).isoformat()
    db = get_db()
    cursor = db.execute(
        "INSERT INTO devices (name, area, created_at) VALUES (?, ?, ?)",
        (data["name"], data["area"], created_at),
    )
    device_id = cursor.lastrowid
    db.execute(
        "INSERT INTO readings (device_id, value, timestamp, created_at) VALUES (?, ?, ?, ?)",
        (device_id, 0.0, created_at, created_at),
    )
    db.commit()
    device = db.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    return jsonify(row_to_dict(device)), 201


@app.route("/devices/<int:device_id>", methods=["GET"])
def get_device(device_id):
    db = get_db()
    device = db.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    if device is None:
        abort(404)
    return jsonify(row_to_dict(device))


@app.route("/devices/<int:device_id>/readings", methods=["GET"])
def list_readings(device_id):
    db = get_db()
    device = db.execute("SELECT id FROM devices WHERE id = ?", (device_id,)).fetchone()
    if device is None:
        abort(404)
    readings = db.execute(
        "SELECT * FROM readings WHERE device_id = ? ORDER BY timestamp DESC, id DESC",
        (device_id,),
    ).fetchall()
    return jsonify([row_to_dict(reading) for reading in readings])


@app.route("/devices/<int:device_id>/readings", methods=["POST"])
def create_reading(device_id):
    data = request.get_json(silent=True)
    if not validate_reading_payload(data):
        return jsonify({"error": "Payload must include value."}), 400

    timestamp = parse_timestamp(data.get("timestamp"))
    if timestamp is None:
        return jsonify({"error": "Invalid ISO timestamp."}), 400

    db = get_db()
    device = db.execute("SELECT id FROM devices WHERE id = ?", (device_id,)).fetchone()
    if device is None:
        abort(404)

    created_at = datetime.now(timezone.utc).isoformat()
    cursor = db.execute(
        "INSERT INTO readings (device_id, value, timestamp, created_at) VALUES (?, ?, ?, ?)",
        (device_id, float(data["value"]), timestamp, created_at),
    )
    db.commit()
    reading = db.execute("SELECT * FROM readings WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(row_to_dict(reading)), 201


@app.route("/devices/<int:device_id>/readings/<int:reading_id>", methods=["DELETE"])
def delete_reading(device_id, reading_id):
    db = get_db()
    result = db.execute(
        "DELETE FROM readings WHERE id = ? AND device_id = ?",
        (reading_id, device_id),
    )
    if result.rowcount == 0:
        abort(404)
    db.commit()
    return jsonify({"deleted": reading_id})


@app.route("/export", methods=["GET"])
def export_all():
    """Export all devices with their readings as JSON."""
    db = get_db()
    devices = db.execute("SELECT * FROM devices ORDER BY id").fetchall()
    out = []
    for d in devices:
        dev = row_to_dict(d)
        readings = db.execute(
            "SELECT * FROM readings WHERE device_id = ? ORDER BY timestamp DESC, id DESC",
            (d["id"],),
        ).fetchall()
        dev["readings"] = [row_to_dict(r) for r in readings]
        out.append(dev)
    return jsonify({"devices": out})


@app.route("/import", methods=["POST"])
def import_data():
    """Import devices + readings from JSON payload. Payload format: { "devices": [ { "name":..., "area":..., "readings": [ {"value":.., "timestamp":...}, ... ] }, ... ] }
    New devices are created; readings are inserted. Returns list of created device IDs.
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict) or "devices" not in payload:
        return jsonify({"error": "Payload must be JSON with a 'devices' list."}), 400

    db = get_db()
    created = []
    for dev in payload.get("devices", []):
        name = dev.get("name")
        area = dev.get("area")
        if not name or not area:
            continue
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = db.execute(
            "INSERT INTO devices (name, area, created_at) VALUES (?, ?, ?)",
            (name, area, created_at),
        )
        device_id = cursor.lastrowid
        created.append(device_id)
        # insert readings if provided
        for r in dev.get("readings", []):
            value = r.get("value")
            ts = r.get("timestamp") or created_at
            # validate timestamp
            parsed = parse_timestamp(ts)
            if parsed is None:
                parsed = created_at
            db.execute(
                "INSERT INTO readings (device_id, value, timestamp, created_at) VALUES (?, ?, ?, ?)",
                (device_id, float(value), parsed, created_at),
            )
    db.commit()
    return jsonify({"created_device_ids": created}), 201


@app.route("/metrics", methods=["GET"])
def metrics():
    db = get_db()
    devices = db.execute("SELECT id, name, area FROM devices ORDER BY id").fetchall()

    lines = [
        "# HELP heater_meter_value Gauge. Aktueller Ablesewert des Heizkostenverteilers.",
        "# TYPE heater_meter_value gauge",
        "# HELP heater_meter_last_reading_timestamp_seconds Gauge. Unix-Epoch Zeit der letzten Ablesung.",
        "# TYPE heater_meter_last_reading_timestamp_seconds gauge",
        "# HELP heater_meter_readings_count Gauge. Anzahl gespeicherter Ablesungen pro Gerät.",
        "# TYPE heater_meter_readings_count gauge",
    ]

    for device in devices:
        device_id = device["id"]
        name = device["name"]
        area = device["area"]

        # latest reading
        latest = db.execute(
            "SELECT value, timestamp FROM readings WHERE device_id = ? ORDER BY timestamp DESC, id DESC LIMIT 1",
            (device_id,),
        ).fetchone()

        # readings count
        cnt_row = db.execute("SELECT COUNT(*) as cnt FROM readings WHERE device_id = ?", (device_id,)).fetchone()
        readings_count = cnt_row["cnt"] if cnt_row is not None else 0

        value = latest["value"] if latest is not None else 0.0
        timestamp_iso = latest["timestamp"] if latest is not None else None
        ts_seconds = "0"
        if timestamp_iso:
            try:
                # timestamp is stored as ISO with timezone (UTC)
                dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
                ts_seconds = str(int(dt.replace(tzinfo=timezone.utc).timestamp()))
            except Exception:
                ts_seconds = "0"

        labels = f'name="{name}",area="{area}",device_id="{device_id}"'
        lines.append(f'heater_meter_value{{{labels}}} {value}')
        lines.append(f'heater_meter_last_reading_timestamp_seconds{{{labels}}} {ts_seconds}')
        lines.append(f'heater_meter_readings_count{{{labels}}} {readings_count}')

    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"}


if __name__ == "__main__":
    with app.app_context():
        init_db()
    port = int(os.environ.get("SERVER_PORT", "8100"))
    app.run(host="0.0.0.0", port=port)
