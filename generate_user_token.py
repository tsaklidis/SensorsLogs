"""
Generate JWT token for a user via login API.

Usage:
    python generate_user_token.py <username> <password>

Example:
    python generate_user_token.py john_doe SecurePass123!
"""

import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_BASE = f"{BASE_URL}/api/v1.0"


def generate_token(username: str, password: str):
    """Generate JWT tokens by logging in."""

    print("\n" + "="*80)
    print("GENERATING JWT TOKENS")
    print("="*80)
    print(f"Username: {username}")
    print(f"API URL: {API_BASE}/auth/login")
    print("-"*80)

    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "username": username,
                "password": password
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            print("\n✅ SUCCESS - Tokens Generated!")
            print("-"*80)
            print(f"\n📝 ACCESS TOKEN (expires in {data['expires_in']} seconds / {data['expires_in']//60} minutes):")
            print(data['access_token'])
            print(f"\n🔄 REFRESH TOKEN:")
            print(data['refresh_token'])

            print("\n" + "-"*80)
            print("📋 COPY & PASTE FOR USER:")
            print("-"*80)
            print(f"""
# Access Token (use for API requests):
export ACCESS_TOKEN="{data['access_token']}"

# Refresh Token (use to get new access token):
export REFRESH_TOKEN="{data['refresh_token']}"

# Example API request:
curl -X POST "{API_BASE}/records" \\
  -H "Authorization: Bearer $ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"sensor_id": 1, "value": 23.5}}'
""")

            print("-"*80)
            print("\n⏰ TOKEN LIFECYCLE:")
            print(f"  • Access token expires in: {data['expires_in']//60} minutes")
            print(f"  • Refresh token expires in: 7 days")
            print(f"  • After access token expires, use refresh token to get new one")
            print(f"  • After 7 days, user must login again")

            print("\n🔄 TO REFRESH TOKEN:")
            print(f'curl -X POST "{API_BASE}/auth/refresh" \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{\"refresh_token\": \"<REFRESH_TOKEN>\"}}\'')

            print("\n" + "="*80)

            return data

        elif response.status_code == 401:
            print("\n❌ ERROR: Login Failed!")
            print("-"*80)
            error = response.json()
            print(f"Reason: {error.get('detail', 'Unknown error')}")
            print("\nPossible causes:")
            print("  • Incorrect username or password")
            print("  • User account is inactive")
            print("  • Username is case-sensitive")
            print("\n" + "="*80)
            return None

        else:
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            print("-"*80)
            try:
                error = response.json()
                print(f"Error: {error}")
            except:
                print(f"Response: {response.text}")
            print("="*80)
            return None

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API!")
        print("-"*80)
        print(f"URL: {API_BASE}/auth/login")
        print("\nPlease check:")
        print("  • Is the server running?")
        print("  • Is the BASE_URL correct in .env?")
        print("  • Can you access the API in your browser?")
        print("="*80)
        return None

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print("-"*80)
        print(str(e))
        print("="*80)
        return None


def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("\n❌ ERROR: Invalid arguments")
        print("="*80)
        print("Usage: python generate_user_token.py <username> <password>")
        print("\nExample:")
        print("  python generate_user_token.py john_doe SecurePass123!")
        print("\nThis script will:")
        print("  1. Login to the API with the provided credentials")
        print("  2. Return JWT access and refresh tokens")
        print("  3. Show you how to use the tokens")
        print("="*80)
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    result = generate_token(username, password)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

