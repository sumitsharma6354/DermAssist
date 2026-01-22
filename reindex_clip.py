import os
import pandas as pd
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# --- CONFIGURATION ---
QDRANT_URL = "https://01316258-dac8-44a6-9cd3-da472e9d12e6.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.ZrhpQ1sheNE2d4lhadPSOiw5VmYLN9I1b4U58u-5TLU"# <--- PASTE KEY
COLLECTION_NAME = "healthcare_clip"  # <--- New Collection Name

# PATHS
DATASET_DIR = "images" 
METADATA_PATH = "metadata.csv"

# --- MAIN SCRIPT ---
def run_upload():
    print("⚙️ Loading CLIP Model (This understands Text & Images)...")
    # We use a lightweight, high-performance CLIP model
    model = SentenceTransformer('clip-ViT-B-32')
    print("✅ Model Loaded!")

    # 1. Load Metadata
    meta_dict = {}
    if os.path.exists(METADATA_PATH):
        df = pd.read_csv(METADATA_PATH)
        df = df.drop_duplicates(subset=['image_id'], keep='first')
        # Clean data to prevent errors
        df['age'] = df['age'].fillna(0).astype(int).astype(str)
        df['localization'] = df['localization'].fillna("Unknown")
        df['dx'] = df['dx'].fillna("unknown")
        meta_dict = df.set_index('image_id').to_dict('index')
        print(f"✅ Metadata Loaded: {len(meta_dict)} rows")

    # 2. Connect to Cloud
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)
    
    # Vector size for clip-ViT-B-32 is 512
    print(f"🗑️ Creating New Collection '{COLLECTION_NAME}'...")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=512, distance=Distance.COSINE),
    )

    # 3. Upload Loop
    files = [f for f in os.listdir(DATASET_DIR) if f.lower().endswith('.jpg')]
    print(f"🚀 Found {len(files)} images. Starting upload...")

    batch = []
    BATCH_SIZE = 32 # Bigger batch because CLIP is fast
    
    for i, filename in tqdm(enumerate(files), total=len(files)):
        try:
            path = os.path.join(DATASET_DIR, filename)
            img = Image.open(path).convert('RGB')
            
            # Generate CLIP Vector (The Magic Part)
            vector = model.encode(img).tolist()
            
            img_id = filename.split('.')[0]
            payload = {"image_id": img_id, "filename": filename}
            if img_id in meta_dict:
                payload.update(meta_dict[img_id])
            
            batch.append(PointStruct(id=i, vector=vector, payload=payload))
            
            if len(batch) >= BATCH_SIZE:
                client.upsert(collection_name=COLLECTION_NAME, points=batch)
                batch = []
                
        except Exception as e:
            print(f"Error {filename}: {e}")

    if batch:
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
    
    print("🎉 CLIP Upload Complete! Your database is now Text-Smart.")

if __name__ == "__main__":
    run_upload()