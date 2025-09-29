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
    
    print("🔐 Generated JWT Secrets:")
    print(f"JWT_ACCESS_SECRET={access_secret}")
    print(f"JWT_REFRESH_SECRET={refresh_secret}")
    print()
    
    # Check if .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        print("📝 Found existing .env file")
        
        # Read existing content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check if JWT secrets already exist
        if 'JWT_ACCESS_SECRET=' in content:
            choice = input("⚠️  JWT secrets already exist. Replace them? (y/N): ").lower()
            if choice != 'y':
                print("❌ Cancelled. Secrets not updated.")
                return
            
            # Remove existing JWT secrets
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if not line.startswith('JWT_ACCESS_SECRET=') and not line.startswith('JWT_REFRESH_SECRET='):
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # Add new secrets
        if not content.endswith('\n'):
            content += '\n'
        content += f'\n# JWT Authentication Secrets\n'
        content += f'JWT_ACCESS_SECRET={access_secret}\n'
        content += f'JWT_REFRESH_SECRET={refresh_secret}\n'
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {env_file} with new JWT secrets")
    
    else:
        # Create new .env file
        content = f"""# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# JWT Authentication Secrets
JWT_ACCESS_SECRET={access_secret}
JWT_REFRESH_SECRET={refresh_secret}
"""
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Created {env_file} with JWT secrets")
    
    print("\n📋 Next Steps:")
    print("1. Never commit your .env file to git")
    print("2. Share this script with your team, not the .env file")
    print("3. Each developer should run this script in their local environment")
    print("4. Use different secrets for production deployment")

if __name__ == "__main__":
    print("🚀 JWT Secret Generator")
    print("=" * 40)
    generate_jwt_secrets()