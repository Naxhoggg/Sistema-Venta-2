import firebase_admin
from firebase_admin import credentials, firestore
import os
from pathlib import Path

# Obtiene la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Ruta al archivo de credenciales
CRED_PATH = os.path.join(BASE_DIR, 'serviceAccountKey.json')

# Inicializa Firebase
cred = credentials.Certificate(CRED_PATH)
firebase_admin.initialize_app(cred)

# Obtiene una referencia a Firestore
db = firestore.client()

def get_db():
    return db