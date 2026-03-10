
import sys
import time
import datetime

print(f"Python Version: {sys.version}")

try:
    import cryptg
    print(f"✅ cryptg is installed")
except ImportError:
    print("❌ cryptg is NOT installed")

try:
    import tgcrypto
    print(f"✅ tgcrypto is installed")
except ImportError:
    print("❌ tgcrypto is NOT installed")

print(f"Local Time: {datetime.datetime.now()}")
print(f"UTC Time:   {datetime.datetime.utcnow()}")
