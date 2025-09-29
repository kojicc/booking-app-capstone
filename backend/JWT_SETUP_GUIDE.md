# JWT Secrets Setup Guide

## Method 1: Python Command Line

```bash
python -c "import secrets; print('JWT_ACCESS_SECRET=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_REFRESH_SECRET=' + secrets.token_hex(32))"
```

## Method 2: Using OpenSSL (Linux/Mac)

```bash
openssl rand -hex 32
```

## Method 3: Online Generator (Use with caution)

- Only for development
- Never use for production
- Examples: https://www.allkeysgenerator.com/Random/Security-Encryption-Key-Generator.aspx

## Method 4: Node.js

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## Team Setup Instructions

### For New Team Members:

1. Clone the repository
2. Run: `python generate_secrets.py`
3. Or manually add secrets to `.env` file
4. Never share your `.env` file

### .env Template (.env.example)

Create this file for your team:

```
# Database Configuration
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# JWT Authentication Secrets (Generate your own!)
JWT_ACCESS_SECRET=generate_your_own_secret_here
JWT_REFRESH_SECRET=generate_your_own_secret_here
```
