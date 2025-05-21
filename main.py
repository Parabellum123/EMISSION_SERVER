import os
from dotenv import load_dotenv

load_dotenv()

print("MYSQL_USER =", os.getenv("MYSQL_USER"))
print("POSTGRES_HOST =", os.getenv("POSTGRES_HOST"))
