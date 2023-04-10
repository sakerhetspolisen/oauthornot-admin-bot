import uuid


class Task():
    def __init__(self, url) -> None:
        self.url = url
        self.id = str(uuid.uuid4())
