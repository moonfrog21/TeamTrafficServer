"""
app/simulator.py
Proper traffic simulator - builds cars up to 6+ to trigger GREEN,
clears them one by one through the intersection, then switches direction.
One full cycle ≈ 60 seconds.
"""

import threading
import time
import random
from datetime import datetime


def start_simulator(app):

    def simulate():
        from app import db
        from app.models import Telemetry
        from app.traffic_logic import traffic_sm, count_by_direction, INTERSECTION

        print("[Simulator] Traffic simulation thread started")

        LANE_OFFSET = 0.0003

        SPAWN = {
            # Direction 1 – Horizontal (West ↔ East)
            # West arm: car from West heading East → northern lane (lat + offset)
            "dir1_west":  {
                "lat": INTERSECTION["lat"] + LANE_OFFSET,
                "lng": INTERSECTION["lng"] - 0.0025
            },
            # East arm: car from East heading West → southern lane (lat - offset)
            "dir1_east":  {
                "lat": INTERSECTION["lat"] - LANE_OFFSET,
                "lng": INTERSECTION["lng"] + 0.0025
            },
            # Direction 2 – Vertical (North ↕ South)
            # North arm: car from North heading South → eastern lane (lng + offset)
            "dir2_north": {
                "lat": INTERSECTION["lat"] - 0.0025,
                "lng": INTERSECTION["lng"] + LANE_OFFSET
            },
            # South arm: car from South heading North → western lane (lng - offset)
            "dir2_south": {
                "lat": INTERSECTION["lat"] + 0.0025,
                "lng": INTERSECTION["lng"] - LANE_OFFSET
            },
        }

        def jitter(lat, lng, spread=0.0002):
            return (
                lat + random.uniform(-spread, spread),
                lng + random.uniform(-spread, spread),
            )

        def spawn(direction, arm, car_id):
            key      = f"dir{direction}_{arm}"
            pt       = SPAWN[key]
            lat, lng = jitter(pt["lat"], pt["lng"])
            user     = f"sim_dir{direction}_{arm}_{car_id}"
            now      = datetime.utcnow().isoformat()
            with app.app_context():
                from app.models import Telemetry
                from app import db
                Telemetry.query.filter_by(user=user).delete()
                db.session.add(Telemetry(
                    user=user,
                    latitude=str(round(lat, 6)),
                    longitude=str(round(lng, 6)),
                    time=now,
                ))
                db.session.commit()

        def clear_car(direction, arm, car_id):
            user = f"sim_dir{direction}_{arm}_{car_id}"
            with app.app_context():
                from app.models import Telemetry
                from app import db
                Telemetry.query.filter_by(user=user).delete()
                db.session.commit()

        def clear_all(direction):
            prefix = f"sim_dir{direction}_"
            with app.app_context():
                from app.models import Telemetry
                from app import db
                Telemetry.query.filter(
                    Telemetry.user.like(f"{prefix}%")
                ).delete(synchronize_session=False)
                db.session.commit()

        def tick_sm():
            with app.app_context():
                from app.models import Telemetry
                from app.traffic_logic import count_by_direction
                records = Telemetry.query.all()
                d1, d2  = count_by_direction(records)
                traffic_sm.tick(d1, d2)
                return d1, d2

        def wait_for(target_state, timeout=15):
            deadline = time.time() + timeout
            while time.time() < deadline:
                tick_sm()
                if traffic_sm.state == target_state:
                    return True
                time.sleep(0.5)
            return False

        ARMS = {"1": ["west", "east"], "2": ["north", "south"]}

        while True:
            # ── Phase 1: Build Direction 1 to 6+ cars ────────────────────
            n = random.randint(6, 8)
            spawned1 = []
            for i in range(n):
                arm = ARMS["1"][i % 2]
                spawn("1", arm, i)
                spawned1.append(("1", arm, i))
                tick_sm()
                time.sleep(random.uniform(1.5, 2.5))

            d1, d2 = tick_sm()
            print(f"[Simulator] Dir1 built up: {d1} cars → waiting for GREEN_D1")

            # ── Phase 2: Wait for GREEN_D1 then clear cars one by one ─────
            wait_for("GREEN_D1", timeout=10)
            print(f"[Simulator] GREEN_D1 triggered — clearing cars")

            for direction, arm, car_id in spawned1:
                clear_car(direction, arm, car_id)
                tick_sm()
                time.sleep(random.uniform(0.3, 0.7))

            # ── Phase 3: ORANGE_D1 (auto 5s) ─────────────────────────────
            wait_for("ORANGE_D1", timeout=6)
            print("[Simulator] ORANGE_D1 — switching soon")
            for _ in range(6):
                tick_sm()
                time.sleep(1)

            # ── Phase 4: Build Direction 2 to 6+ cars ────────────────────
            n = random.randint(6, 8)
            spawned2 = []
            for i in range(n):
                arm = ARMS["2"][i % 2]
                spawn("2", arm, i)
                spawned2.append(("2", arm, i))
                tick_sm()
                time.sleep(random.uniform(0.3, 0.7))

            d1, d2 = tick_sm()
            print(f"[Simulator] Dir2 built up: {d2} cars → waiting for GREEN_D2")

            # ── Phase 5: Wait for GREEN_D2 then clear ────────────────────
            wait_for("GREEN_D2", timeout=10)
            print("[Simulator] GREEN_D2 triggered — clearing cars")

            for direction, arm, car_id in spawned2:
                clear_car(direction, arm, car_id)
                tick_sm()
                time.sleep(random.uniform(1.2, 2.0))

            # ── Phase 6: ORANGE_D2 then loop ─────────────────────────────
            wait_for("ORANGE_D2", timeout=6)
            print("[Simulator] ORANGE_D2 — cycle complete, restarting")
            for _ in range(6):
                tick_sm()
                time.sleep(1)

            # Safety cleanup before next cycle
            clear_all("1")
            clear_all("2")
            time.sleep(2)

    t = threading.Thread(target=simulate, daemon=True)
    t.start()
    print("[Simulator] Traffic simulator thread launched")