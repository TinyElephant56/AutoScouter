class Path:
    def __init__(self, init_time, last_time, init_cord, last_cord, color, cords):
        self.init_time = init_time
        self.last_time = last_time
        self.init_cord = init_cord
        self.last_cord = last_cord
        self.color = color
        self.cords = cords

        self.number = None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        # Convert string keys in 'cords' back to integers because stupid json
        data["cords"] = {int(k): v for k, v in data["cords"].items()}
        
        path = cls(
            data["init_time"], data["last_time"], data["init_cord"], data["last_cord"],
            data["color"], data["cords"]
        )
        path.number = data.get("number")
        return path