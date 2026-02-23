#!/usr/bin/env python3
"""
Migrate voicebox profiles from AppData to backend database.
"""

import json
import requests
import sys
from pathlib import Path

# Configuration
VOICEBOX_DATA_DIR = Path.home() / "AppData" / "Roaming" / "sh.voicebox.app"
BACKEND_API = "http://localhost:17493"

def migrate_profiles():
    """Migrate all voicebox profiles to backend."""
    profiles_dir = VOICEBOX_DATA_DIR / "profiles"

    if not profiles_dir.exists():
        print(f"❌ Voicebox profiles directory not found: {profiles_dir}")
        return False

    profiles = list(profiles_dir.iterdir())
    if not profiles:
        print("❌ No profiles found in voicebox data directory")
        return False

    print(f"📂 Found {len(profiles)} profiles in voicebox")

    for profile_dir in profiles:
        if not profile_dir.is_dir():
            continue

        profile_id = profile_dir.name
        audio_files = list(profile_dir.glob("*.wav"))

        if not audio_files:
            print(f"⚠️  Skipping {profile_id} - no audio files found")
            continue

        # Try to read profile metadata
        profile_name = profile_dir.name  # Use folder name as fallback
        description = f"Imported from voicebox"
        language = "en"

        # Look for metadata file if it exists
        metadata_file = profile_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    profile_name = metadata.get("name", profile_name)
                    description = metadata.get("description", description)
                    language = metadata.get("language", language)
            except:
                pass

        print(f"\n🎤 Processing profile: {profile_name}")

        try:
            # Step 1: Create profile in backend
            profile_data = {
                "name": profile_name,
                "description": description,
                "language": language
            }

            resp = requests.post(
                f"{BACKEND_API}/profiles",
                json=profile_data,
                timeout=10
            )

            if resp.status_code not in [200, 201]:
                print(f"  ❌ Failed to create profile: {resp.text}")
                continue

            created_profile = resp.json()
            created_profile_id = created_profile["id"]
            print(f"  ✅ Created profile: {created_profile_id}")

            # Step 2: Add audio samples
            for audio_file in audio_files:
                print(f"    📁 Adding sample: {audio_file.name}")

                with open(audio_file, "rb") as f:
                    files = {"file": f}
                    sample_data = {
                        "reference_text": f"Sample from {profile_name}"
                    }

                    resp = requests.post(
                        f"{BACKEND_API}/profiles/{created_profile_id}/samples",
                        files=files,
                        data=sample_data,
                        timeout=30
                    )

                    if resp.status_code not in [200, 201]:
                        print(f"      ❌ Failed to add sample: {resp.text}")
                    else:
                        print(f"      ✅ Sample added")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    print("\n✅ Migration complete!")
    return True

if __name__ == "__main__":
    # Check if backend is running
    try:
        resp = requests.get(f"{BACKEND_API}/profiles", timeout=5)
    except:
        print("❌ Backend is not running. Please start it with: bun run dev:server")
        sys.exit(1)

    # Run migration
    success = migrate_profiles()
    sys.exit(0 if success else 1)
