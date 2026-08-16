from supabase import create_client, Client
import os 
from dotenv import load_dotenv

load_dotenv(override=True)

url= os.getenv("SUPABASE_URL")
key= os.getenv("SUPABASE_API")
supabase: Client = create_client(url, key)


def sign_up_user(email, password, full_name, role='customer', store_name=None, store_location=None):
    """Registers user in Supabase Auth and guarantees a profile row in public.users."""
    try:
        store_id = None
        
        # 1. If seller, create store first
        if role == 'seller':
            store_payload = {
                "name": store_name, 
                "location": store_location
                # Do not include 'id' here; Supabase generates the long ID automatically
            }
            store_response = supabase.table('stores').insert(store_payload).execute()
            store_id = store_response.data[0]['id']

        # 2. Register user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        user = auth_response.user
        if not user:
            return {"success": False, "error": "Sign-up failed. Could not create Auth user."}
        
        # 3. Create or Update user profile metadata in public.users (using upsert)
        user_metadata = {
            "id": user.id,
            "email": email,
            "full_name": full_name,
            "role": role,
            "store_id": store_id
        }
        
        # Upsert ensures that if the Auth user exists, the public record is guaranteed to be created
        db_response = supabase.table('users').upsert(user_metadata).execute()
        
        if not db_response.data:
            return {"success": False, "error": "Failed to create public user profile record."}

        success_msg = f"User registered successfully! (Assigned Store ID: {store_id})" if role == 'seller' else "User registered successfully!"
        
        return {
            "success": True,
            "message": success_msg,
            "user_id": user.id,
            "data": db_response.data[0]
        }

    except Exception as e:
        return {"success": False, "error": f"Registration failed: {str(e)}"}

def login_user(email, password):
    """Authenticates user and safely restores missing public profile records."""
    try:
        # 1. Authenticate with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        session = auth_response.session
        user = auth_response.user
        
        if not session or not user:
            return {"success": False, "error": "Incorrect password. Please try again."}
        
        # 2. Fetch profile from public.users by user ID
        user_profile = (
            supabase.table('users')
            .select('*')
            .eq('id', user.id)
            .execute()
        )

        # 3. SELF-HEALING: If missing by ID, handle stale duplicate emails first
        if not user_profile.data:
            # Check if a stale row exists with the same email under a different ID
            stale_check = (
                supabase.table('users')
                .select('*')
                .eq('email', email)
                .execute()
            )
            
            # If a stale email record exists, delete it so we can insert the fresh UUID record
            if stale_check.data:
                supabase.table('users').delete().eq('email', email).execute()

            user_metadata = user.user_metadata or {}
            full_name = user_metadata.get("full_name", email.split("@")[0])
            role = user_metadata.get("role", "customer")
            store_id = user_metadata.get("store_id", None)

            healed_user = {
                "id": user.id,
                "email": email,
                "full_name": full_name,
                "role": role,
                "store_id": store_id
            }

            insert_response = supabase.table('users').insert(healed_user).execute()
            
            if not insert_response.data:
                return {
                    "success": False,
                    "error": "Account authenticated, but failed to synchronize profile record."
                }
            
            user_data = insert_response.data[0]
        else:
            user_data = user_profile.data[0]

        return {
            "success": True,
            "message": "Login successful!",
            "access_token": session.access_token,
            "user": user_data
        }

    except Exception as e:
        error_str = str(e).lower()
        if "invalid login credentials" in error_str or "invalid_credentials" in error_str:
            return {"success": False, "error": "Incorrect email or password. Please try again."}
            
        return {"success": False, "error": f"Login failed: {str(e)}"}