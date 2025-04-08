from cryptography.fernet import Fernet
from django.conf import settings

fernet = Fernet(settings.SECRET_ENCRYPTION_KEY)

def encrypt_password(plain_text_password: str) -> str:
    encrypted = fernet.encrypt(plain_text_password.encode())
    return encrypted.decode()

def decrypt_password(encrypted_password: str) -> str:
    decrypted = fernet.decrypt(encrypted_password.encode())
    return decrypted.decode()
