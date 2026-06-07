# Copyright (c) J. Lluch (original)
# Adapted by Raul Hernandez Lopez, 2026
#
# Based on work shared by @jlluch (Universitat Politècnica de València) as course material.
# This adaptation is distributed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode

"""

2 Fase OFFLINE:
encripta/cifra las tablas de data/*.csv a data/*.enc

Formato:
[16 bytes de salt][datos Fernet], compatible con encrypt_utils.decrypt_csv_file

Nota:
La contraseña debe ser la misma tanto en .streamlit/secrets.toml en local
como en Settings -> Secrets de Streamlit Cloud

Uso:
    python build/encrypt_files.py
"""

import os
import base64
from pathlib import Path

import pandas as pd
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import tomllib as _tomllib, pathlib as _pl
with open(_pl.Path(__file__).resolve().parent.parent / ".streamlit/secrets.toml", "rb") as _f:
    PASSWORD = _tomllib.load(_f)["data_encryption"]["key"]
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FILES = ["running_sessions", "aggregations", "heatmap_points", "track_destacada"]


def get_key(password, salt=None):
    """Generate a Fernet key from a password and salt."""
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode())), salt

def encrypt_csv(csv_path, out_path, password):
    """Encrypt a CSV file."""
    df = pd.read_csv(csv_path)
    payload = df.to_csv(index=False).encode()
    key, salt = get_key(password)
    # Encrypt the data
    encrypted = Fernet(key).encrypt(payload)

    with open(out_path, "wb") as f:
        f.write(salt)
        f.write(encrypted)
    print(f"-> {out_path.name} ({out_path.stat().st_size // 1024} KB)")


def main():
    missing = [n for n in FILES if not (DATA / f"{n}.csv").exists()]
    if missing:
        raise SystemExit(f"Faltan CSV en claro: {missing}. Ejecuta build/build_aggregations.py antes.")
    for name in FILES:
        encrypt_csv(DATA / f"{name}.csv", DATA / f"{name}.csv.enc", PASSWORD)
    print("\nEncriptación completa." \
    "\nImportante: los .csv limpios están en .gitignore" \
    "y solo se suben los .enc.")


if __name__ == "__main__":
    main()
