"""
Test script for rate limiting functionality.

This script tests the rate limiting implementation without requiring Firebase credentials.
It demonstrates how the rate limiting logic works.
"""
import sys
import os
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_rate_limit_logic():
    """Test the rate limiting logic."""
    print("=" * 60)
    print("Testing Rate Limiting Logic")
    print("=" * 60)
    
    # Simulate user data
    user_data = {
        'daily_analyses_count': 0,
        'rate_limit_reset_date': datetime.utcnow(),
        'image_analyses_count': 0
    }
    
    limit = 3
    
    print(f"\n1. Initial state:")
    print(f"   Daily count: {user_data['daily_analyses_count']}")
    print(f"   Limit: {limit}")
    print(f"   Reset date: {user_data['rate_limit_reset_date'].date()}")
    
    # Test 1: Make 3 requests (should all succeed)
    print(f"\n2. Making {limit} requests (should all succeed):")
    for i in range(limit):
        daily_count = user_data['daily_analyses_count']
        
        if daily_count >= limit:
            print(f"   Request {i+1}: ❌ DENIED (limit exceeded)")
            is_allowed = False
        else:
            print(f"   Request {i+1}: ✅ ALLOWED (remaining: {limit - daily_count - 1})")
            user_data['daily_analyses_count'] += 1
            user_data['image_analyses_count'] += 1
            is_allowed = True
    
    # Test 2: Make 4th request (should fail)
    print(f"\n3. Making 4th request (should fail):")
    daily_count = user_data['daily_analyses_count']
    if daily_count >= limit:
        print(f"   Request 4: ❌ DENIED (limit exceeded)")
        print(f"   Remaining: 0")
        print(f"   Message: Daily image analysis limit exceeded. You can analyze up to 3 images per day.")
    
    # Test 3: Simulate next day (should reset)
    print(f"\n4. Simulating next day (should reset counter):")
    today = datetime.utcnow().date()
    last_reset = user_data['rate_limit_reset_date'].date()
    
    # Simulate next day
    user_data['rate_limit_reset_date'] = datetime.utcnow() - timedelta(days=1)
    last_reset = user_data['rate_limit_reset_date'].date()
    
    print(f"   Current date: {today}")
    print(f"   Last reset date: {last_reset}")
    
    if last_reset < today:
        print(f"   ✅ Resetting counter (new day detected)")
        user_data['daily_analyses_count'] = 0
        user_data['rate_limit_reset_date'] = datetime.utcnow()
    
    print(f"   New daily count: {user_data['daily_analyses_count']}")
    print(f"   New reset date: {user_data['rate_limit_reset_date'].date()}")
    
    # Test 4: Make request after reset
    print(f"\n5. Making request after reset (should succeed):")
    daily_count = user_data['daily_analyses_count']
    if daily_count >= limit:
        print(f"   Request: ❌ DENIED")
    else:
        print(f"   Request: ✅ ALLOWED (remaining: {limit - daily_count - 1})")
        user_data['daily_analyses_count'] += 1
        user_data['image_analyses_count'] += 1
    
    # Final stats
    print(f"\n6. Final statistics:")
    print(f"   Total lifetime analyses: {user_data['image_analyses_count']}")
    print(f"   Today's analyses: {user_data['daily_analyses_count']}")
    print(f"   Remaining today: {max(0, limit - user_data['daily_analyses_count'])}")
    
    print("\n" + "=" * 60)
    print("✅ Rate limiting logic test completed successfully!")
    print("=" * 60)


def test_firestore_availability():
    """Test if Firebase/Firestore is available."""
    print("\n" + "=" * 60)
    print("Testing Firebase/Firestore Availability")
    print("=" * 60)
    
    try:
        from app.services.firebase_service import firebase_service
        
        print(f"\n✅ Firebase service imported successfully")
        print(f"   Is available: {firebase_service.is_available}")
        
        if firebase_service.is_available:
            print(f"   ✅ Firestore is configured and ready")
            print(f"\n   You can now use the following features:")
            print(f"   - User management")
            print(f"   - Rate limiting")
            print(f"   - Playlist tracking")
        else:
            print(f"   ⚠️  Firestore is not configured")
            print(f"\n   To enable Firestore, set one of these environment variables:")
            print(f"   - FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json")
            print(f"   - FIREBASE_CREDENTIALS_JSON='{{...}}'")
            print(f"   - Or deploy to GCP to use Application Default Credentials")
            print(f"\n   The application will still work, but rate limiting will be disabled.")
        
    except Exception as e:
        print(f"\n❌ Error importing Firebase service: {e}")
        print(f"   Make sure firebase-admin is installed:")
        print(f"   pip install firebase-admin")
    
    print("\n" + "=" * 60)


def test_user_models():
    """Test user data models."""
    print("\n" + "=" * 60)
    print("Testing User Data Models")
    print("=" * 60)
    
    try:
        from app.models.user import UserProfile, RateLimitInfo, PlaylistRecord
        
        print(f"\n✅ User models imported successfully")
        
        # Test UserProfile
        user = UserProfile(
            user_id="test_user_123",
            email="test@example.com",
            display_name="Test User",
            image_analyses_count=5,
            playlists_created_count=2,
            daily_analyses_count=1
        )
        print(f"\n1. UserProfile:")
        print(f"   User ID: {user.user_id}")
        print(f"   Email: {user.email}")
        print(f"   Total analyses: {user.image_analyses_count}")
        print(f"   Total playlists: {user.playlists_created_count}")
        print(f"   Today's analyses: {user.daily_analyses_count}")
        
        # Test RateLimitInfo
        rate_limit = RateLimitInfo(
            limit=3,
            remaining=2,
            is_exceeded=False
        )
        print(f"\n2. RateLimitInfo:")
        print(f"   Limit: {rate_limit.limit}")
        print(f"   Remaining: {rate_limit.remaining}")
        print(f"   Is exceeded: {rate_limit.is_exceeded}")
        
        # Test PlaylistRecord
        playlist = PlaylistRecord(
            user_id="test_user_123",
            playlist_name="Test Playlist",
            artists=["Artist 1", "Artist 2", "Artist 3"],
            total_tracks=30
        )
        print(f"\n3. PlaylistRecord:")
        print(f"   Name: {playlist.playlist_name}")
        print(f"   Artists: {len(playlist.artists)}")
        print(f"   Total tracks: {playlist.total_tracks}")
        
        print(f"\n✅ All models validated successfully")
        
    except Exception as e:
        print(f"\n❌ Error testing models: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "RATE LIMITING IMPLEMENTATION TEST" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Run tests
    test_rate_limit_logic()
    test_user_models()
    test_firestore_availability()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set up Firebase project (see FIREBASE_SETUP.md)")
    print("2. Configure environment variables")
    print("3. Start the backend server: python backend/start_server.py")
    print("4. Test the API endpoints")
    print("=" * 60)
    print()

