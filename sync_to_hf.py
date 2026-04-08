#!/usr/bin/env python3
"""
Quick script to sync changes to Hugging Face Space after fixing API_BASE_URL.
This will help you redeploy with the proxy fix.
"""

import subprocess
import sys
import os

HF_SPACE_URL = "https://huggingface.co/spaces/shahid21/openenv"
HF_SPACE_GIT = "https://huggingface.co/spaces/shahid21/openenv.git"

def run_command(cmd, cwd=None):
    """Run a shell command and return success."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(e.stderr)
        return False

def main():
    print("="*60)
    print("HUGGING FACE SPACE UPDATE - API_BASE_URL FIX")
    print("="*60)
    print(f"\nYour HF Space: {HF_SPACE_URL}")
    
    # Check if .space directory exists
    space_dir = ".space"
    if not os.path.exists(space_dir):
        print(f"\n📁 Creating {space_dir} directory...")
        os.makedirs(space_dir, exist_ok=True)
        
        print(f"\n📥 Cloning HF Space repository...")
        if not run_command(f"git clone {HF_SPACE_GIT} {space_dir}"):
            print("\n❌ Failed to clone HF Space. Please check:")
            print("1. Your HF token has write access")
            print("2. The Space URL is correct")
            print("3. Git credentials are configured")
            sys.exit(1)
    else:
        print(f"\n✅ Found existing {space_dir} directory")
        print("\n📥 Pulling latest changes from HF Space...")
        run_command("git pull", cwd=space_dir)
    
    # Copy critical files
    print("\n📋 Copying updated files to HF Space...")
    files_to_copy = [
        "baseline/agent.py",
        "inference.py",
        ".env.example",
        "requirements.txt",
        "requirements-prod.txt",
        "Dockerfile",
        "README_HF_SPACE.md",
    ]
    
    for file in files_to_copy:
        src = file
        dst = os.path.join(space_dir, file)
        
        # Create parent directory if needed
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        if os.path.exists(src):
            try:
                import shutil
                shutil.copy2(src, dst)
                print(f"   ✅ {file}")
            except Exception as e:
                print(f"   ⚠️  {file} - {e}")
        else:
            print(f"   ⚠️  {file} - not found")
    
    # Git operations
    print("\n📤 Committing changes to HF Space...")
    run_command("git add .", cwd=space_dir)
    
    commit_msg = "Fix Phase 2: Require API_BASE_URL for LiteLLM proxy\\n\\nEnsure all API calls go through competition's LiteLLM proxy."
    if not run_command(f'git commit -m "{commit_msg}"', cwd=space_dir):
        print("\n⚠️  No changes to commit (maybe already up to date)")
    
    print("\n🚀 Pushing to Hugging Face Space...")
    if run_command("git push", cwd=space_dir):
        print("\n" + "="*60)
        print("✅ SUCCESS! HF Space updated")
        print("="*60)
        print(f"\n📺 View your Space at: {HF_SPACE_URL}")
        print("⏳ Wait 2-3 minutes for the Space to rebuild")
        print("\n💡 Next steps:")
        print("1. Monitor the build in the 'Logs' tab")
        print("2. Once built, test the API at: {}/health".format(HF_SPACE_URL.replace("spaces/", "spaces/")))
        print("3. Resubmit to the competition")
    else:
        print("\n❌ Failed to push to HF Space")
        print("Please check your HF credentials and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
