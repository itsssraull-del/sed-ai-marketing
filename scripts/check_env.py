"""
SED Energy — Environment Variable Checker
Run via: make env-check
"""
import os
import sys

REQUIRED = {
    "Core": ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"],
    "AI APIs": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"],
    "Facebook": ["FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"],
    "Instagram": ["INSTAGRAM_BUSINESS_ACCOUNT_ID"],
    "LinkedIn": ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_PERSON_URN"],
    "WhatsApp": ["WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN"],
    "Storage": ["S3_BUCKET_NAME", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "Pinecone": ["PINECONE_API_KEY", "PINECONE_INDEX_NAME"],
    "Image Gen": ["REPLICATE_API_TOKEN"],
}

OPTIONAL = ["RUNWAY_API_KEY", "IDEOGRAM_API_KEY", "SAGE_ERP_API_URL", "SAGE_ERP_API_KEY"]

missing = []
warnings = []

print("\n🔍 SED Energy — Environment Check\n" + "=" * 40)
for group, keys in REQUIRED.items():
    print(f"\n[{group}]")
    for key in keys:
        val = os.environ.get(key, "")
        if not val or val.startswith("<"):
            print(f"  ❌ {key} — MISSING")
            missing.append(key)
        else:
            masked = val[:4] + "****" + val[-4:] if len(val) > 10 else "****"
            print(f"  ✅ {key} = {masked}")

print("\n[Optional]")
for key in OPTIONAL:
    val = os.environ.get(key, "")
    if not val or val.startswith("<"):
        print(f"  ⚠️  {key} — not set (optional)")
        warnings.append(key)
    else:
        print(f"  ✅ {key} = ****")

print("\n" + "=" * 40)
if missing:
    print(f"❌ {len(missing)} required variable(s) missing: {', '.join(missing)}")
    sys.exit(1)
else:
    print(f"✅ All required variables set\! ({len(warnings)} optional missing)")
