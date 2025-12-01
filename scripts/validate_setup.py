#!/usr/bin/env python3
"""
Startup validation script for User Story Automation
Checks that all required dependencies and configurations are present
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version is 3.8+"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_env_file():
    """Check .env file exists and has required variables"""
    print("\nChecking .env configuration...")
    env_path = Path(__file__).parent / '.env'

    if not env_path.exists():
        print(f"⚠️  .env file not found at {env_path}")
        print("   The application will use default settings (Ollama)")
        print("   To customize, copy .env.example to .env")
        return True  # .env is optional with defaults

    # Read .env and check configuration
    with open(env_path, 'r') as f:
        env_content = f.read()

    provider = 'ollama'  # default
    if 'LLM_PROVIDER=openai' in env_content:
        provider = 'openai'
    elif 'LLM_PROVIDER=groq' in env_content:
        provider = 'groq'

    print(f"✅ Configured to use {provider.upper()}")

    if provider == 'ollama':
        print("✅ No API key required for Ollama")
    elif provider == 'openai':
        if 'OPENAI_API_KEY' in env_content or 'auth_key' in env_content:
            print("✅ OpenAI API key configured")
        else:
            print("⚠️  No OpenAI API key found in .env")
            return False
    elif provider == 'groq':
        if 'GROQ_API_KEY' in env_content:
            print("✅ Groq API key configured")
        else:
            print("⚠️  No Groq API key found in .env")
            return False

    return True

def check_requirements():
    """Check if requirements.txt exists"""
    print("\nChecking requirements.txt...")
    req_path = Path(__file__).parent / 'requirements.txt'

    if not req_path.exists():
        print(f"❌ requirements.txt not found")
        return False

    print("✅ requirements.txt exists")
    return True

def check_ollama_connection():
    """Check if Ollama is accessible (if configured)"""
    print("\nChecking Ollama connection...")
    from dotenv import load_dotenv
    load_dotenv()

    provider = os.getenv('LLM_PROVIDER', 'ollama').lower()

    if provider != 'ollama':
        print(f"ℹ️  Not using Ollama (using {provider}), skipping check")
        return True

    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

    try:
        import requests
        response = requests.get(f"{ollama_url}/api/version", timeout=2)
        if response.status_code == 200:
            version = response.json().get('version', 'unknown')
            print(f"✅ Ollama is running (version {version})")
            return True
        else:
            print(f"⚠️  Ollama returned status code {response.status_code}")
            return False
    except ImportError:
        print("⚠️  requests module not installed, skipping Ollama check")
        print("   Install with: pip install requests")
        return True
    except Exception as e:
        print(f"⚠️  Cannot connect to Ollama at {ollama_url}")
        print(f"   Error: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False

def check_backend_files():
    """Check that backend files exist"""
    print("\nChecking backend files...")
    required_files = [
        'app.py',
        'autoAgile/utils/prompts.py',
        'autoAgile/save_output.py'
    ]

    all_exist = True
    for file_path in required_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            all_exist = False

    return all_exist

def main():
    """Run all validation checks"""
    print("=" * 60)
    print("User Story Automation - Startup Validation")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("Environment Configuration", check_env_file),
        ("Requirements File", check_requirements),
        ("Backend Files", check_backend_files),
        ("Ollama Connection", check_ollama_connection),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error during {name} check: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    all_passed = all(result for _, result in results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} {name}")

    print("=" * 60)

    if all_passed:
        print("✅ All checks passed! Ready to start the application.")
        print("\nTo start:")
        print("  Backend:  python app.py")
        print("  Frontend: npm start")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
