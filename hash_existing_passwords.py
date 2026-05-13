"""
Hash the existing plain text passwords in the users table.
After this runs, login will use werkzeug check_password_hash instead of plain match.

1. Connect to the database
2. Read all users with passwords
3. Skip any password that already looks hashed (starts with 'pbkdf2:' or 'scrypt:')
4. Hash the plain ones using werkzeug.security.generate_password_hash
5. Update the row

Safe to run more than once - already-hashed passwords are skipped.

docker exec -it biogeoda_flask_app python hash_existing_passwords.py
"""

import os
import pymysql
from werkzeug.security import generate_password_hash

# DB connection - same as routes.py uses
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'vps.biogeoda.au'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'flora-admin_flora-admin'),
    'password': os.getenv('DB_PASSWORD', 'BOT_mortimer7indiana'),
    'database': os.getenv('DB_NAME', 'flora-admin_Project.ID.10'),
    'cursorclass': pymysql.cursors.DictCursor,
}


def is_already_hashed(password):
    """Check if a password looks like it has already been hashed by werkzeug."""
    if not password:
        return False
    # werkzeug hashes start with method name and colon
    return password.startswith('pbkdf2:') or password.startswith('scrypt:')


def main():
    print(f"Connecting to {DB_CONFIG['host']}...")
    conn = pymysql.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cursor:
            # get all users
            cursor.execute("SELECT user_id, email, password FROM users")
            users = cursor.fetchall()

            print(f"Found {len(users)} users")

            updated = 0
            skipped = 0

            for user in users:
                user_id = user['user_id']
                email = user['email']
                current_pw = user['password']

                if is_already_hashed(current_pw):
                    print(f"  Skip user_id={user_id} ({email}) - already hashed")
                    skipped += 1
                    continue

                # hash the plain text password
                hashed = generate_password_hash(current_pw)

                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s",
                    [hashed, user_id]
                )
                print(f"  Hashed password for user_id={user_id} ({email})")
                updated += 1

            conn.commit()
            print(f"\nDone. Updated: {updated}, Skipped (already hashed): {skipped}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()