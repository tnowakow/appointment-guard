#!/usr/bin/env python3
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Railway token to add as secret
token = "00c9be57-884c-4fa6-97db-7bd53180025c"

# Public key from GitHub (base64 encoded)
public_key_b64 = "w8JYvynU074Q2pFSRdsMtS/nSGqxguG9z/4iXs0ISQI="

# Decode the public key
public_key_der = base64.b64decode(public_key_b64)
public_key = serialization.load_pem_public_key(public_key_der)

# Encrypt the token
encrypted = public_key.encrypt(
    token.encode(),
    padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
)

# Base64 encode the encrypted value
encrypted_b64 = base64.b64encode(encrypted).decode()

print(f"Encrypted value: {encrypted_b64}")
