"""Run script for the Flask server, cleanup thread, and traffic simulator."""

import threading
import time as time_module
from datetime import datetime, timedelta

from app import create_app, db
from app.simulator import start_simulator

app = create_app()


def cleanup_stale_records():
    while True:
        time_module.sleep(60)
        with app.app_context():
            from app.models import Telemetry
            cutoff  = datetime.utcnow() - timedelta(minutes=5)
            removed = 0
            for record in Telemetry.query.all():
                try:
                    if datetime.fromisoformat(record.time) < cutoff:
                        db.session.delete(record)
                        removed += 1
                except (ValueError, TypeError):
                    pass
            if removed:
                db.session.commit()
                print(f"[Cleanup] Removed {removed} stale record(s) "
                      f"(older than {cutoff.strftime('%H:%M:%S')})")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    cleanup_thread = threading.Thread(target=cleanup_stale_records, daemon=True)
    cleanup_thread.start()
    print("[Cleanup] Stale-record cleanup thread started (interval: 60s, timeout: 5min)")

    start_simulator(app)

    app.run(host="0.0.0.0", port=9998, debug=True, use_reloader=False)