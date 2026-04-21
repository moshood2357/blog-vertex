
from werkzeug.security import generate_password_hash, check_password_hash

password = "coolestdude"

# Generate Argon2 hash
hashed_password = generate_password_hash(
    password,
    method='argon2'
)

print(hashed_password)