from qdrant_client import QdrantClient, models

# ==========================================
# CONFIGURATION
# ==========================================
QDRANT_URL = "https://01316258-dac8-44a6-9cd3-da472e9d12e6.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "your_key"
COLLECTION_NAME = "healthcare_clip"  # Make sure this matches your current collection

# ==========================================
# MAIN SCRIPT
# ==========================================
def create_indexes():
    print(f"⚙️ Connecting to {COLLECTION_NAME}...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # We need to tell Qdrant: "Please make these fields searchable"
    fields_to_index = [
        "sex",           # To filter Male/Female
        "localization",  # To filter Face/Neck/Leg
        "dx",            # To filter Melanoma/Nevus
        "age"            # To filter Elderly/Child
    ]

    for field in fields_to_index:
        print(f"🔨 Creating Index for '{field}'...")
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print(f"   ✅ Index created for '{field}'")
        except Exception as e:
            print(f"   ⚠️ Could not create index for {field}: {e}")

    print("\n🎉 Success! Your database is now ready for filtering.")

if __name__ == "__main__":

    create_indexes()
