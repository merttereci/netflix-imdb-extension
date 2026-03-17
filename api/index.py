import sys
import os

# Vercel'in "backend" klasorunu gorebilmesi icin sys.path'e ekliyoruz
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

# FastAPI uygulamamizi backend icinden disa aktariyoruz
from app.main import app
