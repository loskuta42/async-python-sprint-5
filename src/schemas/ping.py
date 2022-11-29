from pydantic import BaseModel


class Ping(BaseModel):
    db: float
    redis: float