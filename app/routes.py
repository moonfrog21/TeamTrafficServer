from flask import Blueprint, request, jsonify, render_template
from app import db
from app.models import Telemetry
from app.traffic_logic import traffic_sm

main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")


@main.route("/data", methods=["POST"])
def receive_data():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"status": "error", "message": "No JSON payload received"}), 400
    try:
        user      = payload["user"]
        latitude  = payload["latitude"]
        longitude = payload["Longitude"]
        time      = payload["time"]
    except KeyError as missing:
        return jsonify({"status": "error", "message": f"Missing key: {missing}"}), 400

    record = Telemetry.query.filter_by(user=user).first()
    if record:
        record.latitude  = latitude
        record.longitude = longitude
        record.time      = time
    else:
        record = Telemetry(user=user, latitude=latitude, longitude=longitude, time=time)
        db.session.add(record)

    db.session.commit()
    return jsonify({"status": "success"}), 200


@main.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    records = Telemetry.query.all()
    return jsonify([r.to_dict() for r in records])


# ── ESP32 endpoint ──────────────────────────────────────────────────────────
@main.route("/light-state")
def light_state():
    s = traffic_sm.summary()
    return jsonify({
        "dir1_light": s["dir1_light"],
        "dir2_light": s["dir2_light"],
        "dir1_count": s["dir1_count"],
        "dir2_count": s["dir2_count"],
        "state":      s["state"],
    })


# ── Dashboard endpoint ──────────────────────────────────────────────────────
@main.route("/traffic-status")
def traffic_status():
    from app.traffic_logic import count_by_direction, INTERSECTION

    records = Telemetry.query.all()
    d1, d2  = count_by_direction(records)
    summary = traffic_sm.summary()

    vehicles = []
    for r in records:
        try:
            vehicles.append({
                "user":      r.user,
                "lat":       float(r.latitude),
                "lng":       float(r.longitude),
                "simulated": (r.user or "").startswith("sim_"),
                "direction": 1 if (r.user or "").startswith("sim_dir1") else 2,
            })
        except (ValueError, TypeError):
            pass

    return jsonify({
        **summary,
        "vehicles":     vehicles,
        "intersection": INTERSECTION,
    })