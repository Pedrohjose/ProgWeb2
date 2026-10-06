import hashlib
import hmac
import secrets

def hash_senha(senha):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${digest}"

def verificar_senha(senha, valor):
    try:
        algoritmo, vezes, salt, esperado = valor.split("$")
        if algoritmo != "pbkdf2_sha256" or int(vezes) != 600000:
            return False
        obtido = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt.encode(), int(vezes)).hex()
        return hmac.compare_digest(obtido, esperado)
    except (ValueError, AttributeError):
        return False
