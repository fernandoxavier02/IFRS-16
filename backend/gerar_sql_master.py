
import bcrypt
import uuid

password = "Fcxv020781@"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

user_id = str(uuid.uuid4())
email = "fernandocostaxavier@gmail.com"
username = "fernando.costa"

# Gerar SQL Seguro
sql = f"""
INSERT INTO admin_users (id, username, email, password_hash, role, is_active, created_at, updated_at)
VALUES ('{user_id}', '{username}', '{email}', '{hashed}', 'SUPERADMIN', true, NOW(), NOW())
ON CONFLICT (email) DO UPDATE 
SET password_hash = '{hashed}', 
    role = 'SUPERADMIN', 
    is_active = true, 
    updated_at = NOW();
"""

print(sql)
