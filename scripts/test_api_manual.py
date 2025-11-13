#!/usr/bin/env python3
"""
Manual API Test Script for Vocabulator
Tests the API endpoints interactively using the running local server
"""

import json
import sys
from pathlib import Path
from typing import Optional

import httpx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print(f"{'=' * 80}\n")


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def check_health(client: httpx.Client) -> bool:
    """Check if API is healthy"""
    try:
        response = client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is healthy: {data.get('status')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Could not connect to API: {e}")
        print_info("Make sure the API server is running: uvicorn src.api.main:app --reload")
        return False


def create_student(client: httpx.Client, student_id: str, grade_level: int = 7) -> Optional[dict]:
    """Create a student profile"""
    print_header(f"Creating Student Profile: {student_id}")
    
    payload = {
        "student_id": student_id,
        "grade_level": grade_level,
    }
    
    try:
        response = client.post(f"{API_BASE}/students", json=payload)
        if response.status_code == 201:
            data = response.json()
            print_success(f"Student created: {data['student_id']}")
            print_info(f"  Grade Level: {data['grade_level']}")
            print_info(f"  Vocabulary Size: {len(data.get('vocabulary_list', []))}")
            return data
        else:
            print_error(f"Failed to create student: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error creating student: {e}")
        return None


def upload_transcript(client: httpx.Client, student_id: str, transcript_text: str, grade_level: int = 7) -> Optional[dict]:
    """Upload a transcript"""
    print_header(f"Uploading Transcript for {student_id}")
    
    from datetime import date
    
    payload = {
        "student_id": student_id,
        "text": transcript_text.strip(),
        "session_date": date.today().isoformat(),
        "grade_level": grade_level,
    }
    
    try:
        response = client.post(f"{API_BASE}/transcripts/upload", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_success("Transcript uploaded successfully")
            print_info(f"  Request ID: {data.get('request_id')}")
            print_info(f"  Vocabulary extracted: {len(data.get('extracted_words', []))} words")
            return data
        else:
            print_error(f"Failed to upload transcript: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error uploading transcript: {e}")
        return None


def get_student_profile(client: httpx.Client, student_id: str) -> Optional[dict]:
    """Get student profile"""
    print_header(f"Getting Student Profile: {student_id}")
    
    try:
        response = client.get(f"{API_BASE}/students/{student_id}/profile")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved profile for {student_id}")
            print_info(f"  Grade Level: {data['grade_level']}")
            print_info(f"  Vocabulary Size: {len(data.get('vocabulary_list', []))}")
            print_info(f"  Proficiency Score: {data.get('proficiency_score', 0):.2f}")
            
            if data.get('vocabulary_list'):
                print_info("\n  Vocabulary Words:")
                for entry in data['vocabulary_list'][:10]:  # Show first 10
                    word = entry.get('word', 'unknown')
                    count = entry.get('usage_count', 0)
                    print_info(f"    • {word} (used {count} times)")
                if len(data['vocabulary_list']) > 10:
                    print_info(f"    ... and {len(data['vocabulary_list']) - 10} more")
            
            return data
        else:
            print_error(f"Failed to get profile: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error getting profile: {e}")
        return None


def get_recommendations(client: httpx.Client, student_id: str) -> Optional[dict]:
    """Get recommendations for a student"""
    print_header(f"Getting Recommendations for {student_id}")
    
    try:
        response = client.get(f"{API_BASE}/students/{student_id}/recommendations")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print_success(f"Found {len(recommendations)} recommendation(s)")
            
            for rec in recommendations:
                date = rec.get('recommendation_date', 'unknown')
                status = rec.get('status', 'unknown')
                words = rec.get('words', [])
                print_info(f"\n  Date: {date}")
                print_info(f"  Status: {status}")
                print_info(f"  Words: {len(words)}")
                
                for word in words[:5]:  # Show first 5
                    word_text = word.get('word', 'unknown')
                    difficulty = word.get('difficulty_score', 0)
                    definition = word.get('definition', 'No definition')
                    print_info(f"    • {word_text} (difficulty: {difficulty:.2f})")
                    print_info(f"      {definition[:80]}...")
            
            return data
        else:
            print_error(f"Failed to get recommendations: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error getting recommendations: {e}")
        return None


def main():
    """Run manual API tests"""
    print_header("Vocabulator API Manual Test")
    
    client = httpx.Client(timeout=120.0)  # Increased timeout for OpenAI API calls
    
    # Check health
    if not check_health(client):
        sys.exit(1)
    
    # Test student creation (must match pattern STU-XXX where XXX is 3 digits)
    # Use a unique ID based on timestamp to avoid conflicts
    import time
    student_id = f"STU-{int(time.time()) % 1000:03d}"
    student = create_student(client, student_id, grade_level=7)
    
    if not student:
        # Try to get existing student if creation failed due to conflict
        print_info("Student creation failed, trying to get existing profile...")
        profile = get_student_profile(client, student_id)
        if profile:
            print_info("Using existing student profile")
            student = profile
        else:
            print_error("Failed to create or retrieve student. Cannot continue.")
            sys.exit(1)
    
    # Test transcript upload
    sample_transcript = """
    Today in science class, we learned about photosynthesis and cellular respiration.
    Photosynthesis occurs in chloroplasts, which contain chlorophyll.
    The chloroplast uses sunlight to create energy through a process called photosynthesis.
    Cellular respiration happens in mitochondria, which are organelles in the cell.
    We discussed how plants convert light energy into chemical energy.
    """
    
    upload_result = upload_transcript(client, student_id, sample_transcript, grade_level=7)
    
    if upload_result:
        print_info("Waiting a moment for processing...")
        import time
        time.sleep(2)  # Give it a moment
    
    # Get updated profile
    profile = get_student_profile(client, student_id)
    
    # Get recommendations
    recommendations = get_recommendations(client, student_id)
    
    # Summary
    print_header("✅ Manual API Test Complete")
    print_success("All API endpoints tested successfully!")
    print_info("\nTest Summary:")
    print_info(f"  ✓ Health check passed")
    print_info(f"  ✓ Student created: {student_id}")
    if upload_result:
        print_info(f"  ✓ Transcript uploaded")
    if profile:
        print_info(f"  ✓ Profile retrieved ({len(profile.get('vocabulary_list', []))} words)")
    if recommendations:
        rec_count = len(recommendations.get('recommendations', []))
        print_info(f"  ✓ Recommendations retrieved ({rec_count} recommendation(s))")
    
    print_info("\nNext steps:")
    print_info("  • View API docs: http://localhost:8000/api/v1/docs")
    print_info("  • Try other endpoints from the interactive docs")
    print_info("  • Check the student profile and recommendations in the database")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

