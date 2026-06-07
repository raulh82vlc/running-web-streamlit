# Copyright (c) J. Lluch (original)
# Adapted by Raul Hernandez Lopez, 2026
#
# Based on work shared by @jlluch (Universitat Politècnica de València) as course material.
# This adaptation is distributed under the
# Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0).
# Full license: https://creativecommons.org/licenses/by-sa/4.0/legalcode

"""
Funciones de DESENCRIPTADO (en remoto)
- El encriptado está en build/encrypt_files.py

Formato del fichero .enc: [16 bytes de salt][datos cifrados con Fernet].

Clave derivada de la contraseña con
PBKDF2-HMAC-SHA256 (100 000 iteraciones).

"""
import os
import io
import base64
import pandas as pd
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_key_from_password(password, salt=None):
    """Genera una clave Fernet a partir de contraseña y salt"""
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def decrypt_to_dataframe(encrypted_data, password, salt):
    """Desencripta datos a un DataFrame usando contraseña y salt"""
    try:
        key, _ = get_key_from_password(password, salt)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return pd.read_csv(io.StringIO(decrypted_data.decode()))
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


def decrypt_csv_file(encrypted_path, password):
    """Desencripta un fichero CSV .enc a un DataFrame"""
    with open(encrypted_path, "rb") as f:
        salt = f.read(16)  # los primeros 16 bytes son el salt
        encrypted_data = f.read()
    return decrypt_to_dataframe(encrypted_data, password, salt)
