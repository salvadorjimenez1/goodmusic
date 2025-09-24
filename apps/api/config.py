import os
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")   # change in prod
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7