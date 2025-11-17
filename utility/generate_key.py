from cryptography.fernet import Fernet


#key = Fernet.generate_key()
#with open("secret.key", "wb") as key_file:
 #   key_file.write(key)

#print("✅ Key saved to secret.key")

with open("secret.key", "rb") as f:
    key = f.read()

fernet = Fernet(key)

# --- Encrypt text ---
def encrypt_text(plain_text: str) -> str:
    if plain_text is None:
        return None
    encrypted = fernet.encrypt(plain_text.encode())
    return encrypted.decode()          # store as string in DB

# --- Decrypt text ---
def decrypt_text(cipher_text: str) -> str:
    if cipher_text is None:
        return None
    decrypted = fernet.decrypt(cipher_text.encode())
    return decrypted.decode()