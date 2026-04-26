"""
app/traffic_logic.py
Intersection traffic light state machine.

Cycle (per direction):
  GREEN  12s  → direction has 6+ cars queued
  ORANGE  5s  → transition warning
  RED         → hold until other side builds 4+ OR this side drops to ≤2
               then switch and repeat

Two directions share one state object so the ESP32 and dashboard
always see a single source of truth.
"""

from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Intersection centre + per-direction approach zones
# Adjust to your real coordinates.
# ---------------------------------------------------------------------------
INTERSECTION = {"lat": -33.9249, "lng": 18.4241}

# Each direction has two "arms" (from-left / from-right or from-top / from-bottom).
# The zone radius is how close a car must be to count as "at the intersection".
ZONE_RADIUS_KM = 0.3   # 150 m

# Simulated car spawn points (just outside the intersection on each arm)
SPAWN_POINTS = {
    "dir1_west":  {"lat": INTERSECTION["lat"],        "lng": INTERSECTION["lng"] - 0.003},
    "dir1_east":  {"lat": INTERSECTION["lat"],        "lng": INTERSECTION["lng"] + 0.003},
    "dir2_north": {"lat": INTERSECTION["lat"] - 0.003,"lng": INTERSECTION["lng"]},
    "dir2_south": {"lat": INTERSECTION["lat"] + 0.003,"lng": INTERSECTION["lng"]},
}

# ---------------------------------------------------------------------------
# Haversine distance
# ---------------------------------------------------------------------------
def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ---------------------------------------------------------------------------
# Count active telemetry rows near the intersection, split by direction tag
# ---------------------------------------------------------------------------
def count_by_direction(records):
    """
    Returns (dir1_count, dir2_count).
    Records tagged user='sim_dir1_*' count for direction 1,
    'sim_dir2_*' for direction 2, real users counted by GPS proximity only
    and split by which arm they're closest to.
    """
    dir1, dir2 = 0, 0
    for r in records:
        try:
            lat = float(r.latitude)
            lng = float(r.longitude)
        except (ValueError, TypeError):
            continue

        dist = haversine_km(lat, lng, INTERSECTION["lat"], INTERSECTION["lng"])
        if dist > ZONE_RADIUS_KM:
            continue  # outside the intersection zone

        u = r.user or ""
        if u.startswith("sim_dir1") or u.startswith("sim_dir2"):
            if u.startswith("sim_dir1"):
                dir1 += 1
            else:
                dir2 += 1
        else:
            # Real user — split by whether they're east/west vs north/south
            # Simple rule: if their lng offset > lat offset → horizontal road
            dlat = abs(lat - INTERSECTION["lat"])
            dlng = abs(lng - INTERSECTION["lng"])
            if dlng >= dlat:
                dir1 += 1
            else:
                dir2 += 1

    return dir1, dir2


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------
class TrafficStateMachine:
    """
    Single shared instance that tracks the intersection's light state.
    Call .tick(dir1_count, dir2_count) every few seconds from the
    simulator thread to advance the state.
    """

    STATES = ["GREEN_D1", "ORANGE_D1", "RED_D1",
              "GREEN_D2", "ORANGE_D2", "RED_D2"]

    GREEN_DURATION  = 12   # seconds
    ORANGE_DURATION = 5    # seconds

    def __init__(self):
        self.state       = "RED_D1"   # start with D1 waiting to get green
        self.state_since = datetime.utcnow()
        self.dir1_count  = 0
        self.dir2_count  = 0

    # ------------------------------------------------------------------
    def elapsed(self):
        return (datetime.utcnow() - self.state_since).total_seconds()

    def _transition(self, new_state):
        self.state       = new_state
        self.state_since = datetime.utcnow()

    # ------------------------------------------------------------------
    def tick(self, dir1_count, dir2_count):
        """Advance the state machine. Call this frequently (every ~2s)."""
        self.dir1_count = dir1_count
        self.dir2_count = dir2_count
        e = self.elapsed()

        if self.state == "RED_D1":
            # Switch to GREEN_D1 when dir1 builds up 6+ cars
            if dir1_count >= 6:
                self._transition("GREEN_D1")

        elif self.state == "GREEN_D1":
            if e >= self.GREEN_DURATION:
                self._transition("ORANGE_D1")

        elif self.state == "ORANGE_D1":
            if e >= self.ORANGE_DURATION:
                self._transition("RED_D2")

        elif self.state == "RED_D2":
            # Switch to GREEN_D2 when dir2 builds up 6+ cars
            if dir2_count >= 6:
                self._transition("GREEN_D2")
            # Also switch if dir1 has dropped very low and dir2 is waiting
            elif dir1_count <= 2 and dir2_count >= 4:
                self._transition("GREEN_D2")

        elif self.state == "GREEN_D2":
            if e >= self.GREEN_DURATION:
                self._transition("ORANGE_D2")

        elif self.state == "ORANGE_D2":
            if e >= self.ORANGE_DURATION:
                self._transition("RED_D1")

    # ------------------------------------------------------------------
    def light_for_direction(self, direction: int):
        """
        Returns 'GREEN', 'ORANGE', or 'RED' for direction 1 or 2.
        When one direction is green/orange, the other is always red.
        """
        if direction == 1:
            if self.state in ("GREEN_D1",):  return "GREEN"
            if self.state in ("ORANGE_D1",): return "ORANGE"
            return "RED"
        else:
            if self.state in ("GREEN_D2",):  return "GREEN"
            if self.state in ("ORANGE_D2",): return "ORANGE"
            return "RED"

    def summary(self):
        return {
            "state":       self.state,
            "elapsed_s":   round(self.elapsed(), 1),
            "dir1_light":  self.light_for_direction(1),
            "dir2_light":  self.light_for_direction(2),
            "dir1_count":  self.dir1_count,
            "dir2_count":  self.dir2_count,
        }


# Module-level singleton used by routes + simulator
traffic_sm = TrafficStateMachine()