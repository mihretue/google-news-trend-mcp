#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment Variables Test:")
print("=" * 40)

# Test required variables
required_vars = [
    "SUPABASE_URL",
    "SUPABASE_KEY", 
    "SUPABASE_JWT_SECRET",
    "TAVILY_API_KEY",
    "OPENAI_API_KEY"
]

for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "KEY" in var or "SECRET" in var:
            masked = value[:8] + "..." + value[-8:] if len(value) > 16 else "***"
            print(f"✅ {var}: {masked}")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NOT SET")

print("=" * 40)
print("Environment test complete!")