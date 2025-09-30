#!/usr/bin/env python3
"""
JWT Secret Generator for Django Project
Run this script to generate secure JWT secrets for your .env file
"""

import secrets
import os

def generate_jwt_secrets():
    """Generate secure JWT secrets and update .env file"""
    
    # Generate cryptographically secure random secrets
    access_secret = secrets.token_hex(32)  # 64 character hex string
    refresh_secret = secrets.token_hex(32)  # 64 character hex string
    # Django SECRET_KEY is typically a URL-safe string. Use token_urlsafe for broader charset.
    secret_key = secrets.token_urlsafe(48)
    # Also expose a DJANGO-prefixed secret for environments that expect it
    django_secret_key = secret_key
    
    print("🔐 Generated JWT Secrets:")
    print(f"JWT_ACCESS_SECRET={access_secret}")
    print(f"JWT_REFRESH_SECRET={refresh_secret}")
    print(f"SECRET_KEY={secret_key}")
    print(f"DJANGO_SECRET_KEY={django_secret_key}")
    print()
    
    # Check if .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        print("📝 Found existing .env file")

        # Read existing content
        with open(env_file, 'r') as f:
            content = f.read()

        # If any of the keys already exist, ask once and replace them
        existing_keys = any(k in content for k in ('JWT_ACCESS_SECRET=', 'JWT_REFRESH_SECRET=', 'SECRET_KEY=', 'DJANGO_SECRET_KEY='))
        if existing_keys:
            choice = input("⚠️  Some secrets already exist in .env. Replace them? (y/N): ").lower()
            if choice != 'y':
                print("❌ Cancelled. Secrets not updated.")
                return

            # Remove any existing JWT/Django secret lines
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if (line.startswith('JWT_ACCESS_SECRET=') or line.startswith('JWT_REFRESH_SECRET=') 
                    or line.startswith('SECRET_KEY=') or line.startswith('DJANGO_SECRET_KEY=')):
                    continue
                new_lines.append(line)
            content = '\n'.join(new_lines)

        # Ensure trailing newline before appending
        if not content.endswith('\n') and content != '':
            content += '\n'

        # Append new secrets
        content += '\n# JWT Authentication & Django Secrets\n'
        content += f'JWT_ACCESS_SECRET={access_secret}\n'
        content += f'JWT_REFRESH_SECRET={refresh_secret}\n'
        content += f'SECRET_KEY={secret_key}\n'
        content += f'DJANGO_SECRET_KEY={django_secret_key}\n'

        # Write back to file
        with open(env_file, 'w') as f:
            f.write(content)

        print(f"✅ Updated {env_file} with new JWT and Django secrets")
    else:
        # Create new .env file
        content = f"""# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# JWT Authentication & Django Secrets
JWT_ACCESS_SECRET={access_secret}
JWT_REFRESH_SECRET={refresh_secret}
SECRET_KEY={secret_key}
DJANGO_SECRET_KEY={django_secret_key}
"""
        with open(env_file, 'w') as f:
            f.write(content)

        print(f"✅ Created {env_file} with JWT and Django secrets")
    
    print("\n📋 Next Steps:")
    print("1. Never commit your .env file to git")
    print("2. Share this script with your team, not the .env file")
    print("3. Each developer should run this script in their local environment")
    print("4. Use different secrets for production deployment")

if __name__ == "__main__":
    print("🚀 JWT Secret Generator")
    print("=" * 40)
    generate_jwt_secrets()