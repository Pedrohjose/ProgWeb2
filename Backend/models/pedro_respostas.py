from fastapi import Response


class PNGResponse(Response):
    media_type = "image/png"
