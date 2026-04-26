from app import db


class Telemetry(db.Model):
    """Represents a single telemetry record received from the Flutter app."""
    id        = db.Column(db.Integer, primary_key=True)
    user      = db.Column(db.String, nullable=False)
    latitude  = db.Column(db.String, nullable=False)
    longitude = db.Column(db.String, nullable=False)
    time      = db.Column(db.String, nullable=False)

    def to_dict(self):
        """Serialise the record to a plain dictionary for JSON responses."""
        return {
            "id":        self.id,
            "user":      self.user,
            "latitude":  self.latitude,
            "longitude": self.longitude,
            "time":      self.time,
        }
