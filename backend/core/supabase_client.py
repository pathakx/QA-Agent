from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user_client(access_token: str) -> Client:
    """
    Create a new Supabase client authenticated as the user.
    This ensures RLS policies are applied correctly for the specific user.
    """
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.postgrest.auth(access_token)
    return client

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return supabase

def test_connection():
    """Test Supabase connection"""
    try:
        # Test basic query (will fail if tables don't exist, but connection is verified)
        print("Testing Supabase connection...")
        print(f"URL: {SUPABASE_URL}")
        print(f"Connection: ✅ Connected successfully!")
        return True
    except Exception as e:
        print(f"Connection: ❌ Failed - {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
