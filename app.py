import os
import re
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from sentence_transformers import SentenceTransformer
from PIL import Image

app = Flask(__name__)

# ==========================================
# 1. CONFIGURATION
# ==========================================
QDRANT_URL = "https://01316258-dac8-44a6-9cd3-da472e9d12e6.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_API_KEY = "your_key"
COLLECTION_NAME = "healthcare_clip"
DATASET_DIR = "images"  
METADATA_PATH = "metadata.csv"

# ==========================================
# 2. LOAD RESOURCES
# ==========================================
print("⚙️ Loading AI Brain...")
model = SentenceTransformer('clip-ViT-B-32') 
print("✅ AI Ready!")

print("⚙️ Loading CSV Database...")
if os.path.exists(METADATA_PATH):
    df = pd.read_csv(METADATA_PATH)
    # Standardize Columns
    df.columns = df.columns.str.lower()
    # Clean Data
    if 'dx' in df.columns: df['dx'] = df['dx'].astype(str).str.lower().str.strip()
    if 'sex' in df.columns: df['sex'] = df['sex'].astype(str).str.lower().str.strip()
    if 'age' in df.columns: df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0).astype(int)
    print(f"✅ CSV Loaded! {len(df)} records.")
else:
    print("❌ CRITICAL ERROR: metadata.csv NOT FOUND.")
    df = pd.DataFrame()

# ==========================================
# 3. HELPER: FILE PATH FINDER
# ==========================================
def find_image_file(image_id):
    """
    Checks if the image exists as .jpg, .JPG, or .png
    Returns the filename if found, else None.
    """
    image_id = str(image_id).strip()
    
    # Check variations
    for ext in [".jpg", ".JPG", ".png", ".PNG", ".jpeg"]:
        filename = f"{image_id}{ext}"
        full_path = os.path.join(DATASET_DIR, filename)
        if os.path.exists(full_path):
            return filename
            
    return None

# ==========================================
# 4. SEARCH LOGIC A: TEXT (CSV STRICT)
# ==========================================
def search_by_text(query):
    print(f"   👉 Text Search Mode: '{query}'")
    query = query.lower()
    results_df = df.copy()
    
    # 1. Disease Filter (Fuzzy Match)
    disease_map = {
        "melanoma": ["mel", "melanoma"], 
        "nevus": ["nv", "nevus", "mole"],
        "mole": ["nv", "nevus", "mole"],
        "basal": ["bcc", "basal"],
        "carcinoma": ["bcc", "carcinoma"],
        "keratosis": ["akiec", "bkl", "keratosis"],
        "vascular": ["vasc", "vascular"],
        "dermatofibroma": ["df", "dermatofibroma"]
    }
    
    found_disease = False
    for name, codes in disease_map.items():
        if name in query:
            results_df = results_df[results_df['dx'].isin(codes)]
            found_disease = True
            print(f"      💊 Filtered by Disease: {name}")
            break
            
    # 2. Gender Filter
    if "female" in query or "woman" in query:
        results_df = results_df[results_df['sex'] == 'female']
    elif "male" in query or "man" in query:
        results_df = results_df[results_df['sex'] == 'male']

    # 3. Age Filter (+/- 5 years)
    age_match = re.search(r'(?:age|old)[\s:]*(\d{1,3})', query)
    if age_match:
        age = int(age_match.group(1))
        results_df = results_df[(results_df['age'] >= age-5) & (results_df['age'] <= age+5)]

    # 4. Fail-Safe (If strict failed, keep disease, drop age/sex)
    if len(results_df) == 0 and found_disease:
        print("      ⚠️ No strict match. Relaxing rules (Keeping Disease).")
        results_df = df.copy()
        for name, codes in disease_map.items():
            if name in query:
                results_df = results_df[results_df['dx'].isin(codes)]
                break
                
    # 5. Select Results
    final_results = []
    if len(results_df) > 0:
        # Pick up to 3 random samples
        samples = results_df.sample(n=min(3, len(results_df)))
        
        disease_pretty = {'mel': 'Melanoma', 'nv': 'Nevus', 'bcc': 'Basal Cell Carcinoma', 'akiec': 'Actinic Keratosis', 'bkl': 'Benign Keratosis', 'vasc': 'Vascular', 'df': 'Dermatofibroma'}

        for _, row in samples.iterrows():
            img_id = row['image_id']
            filename = find_image_file(img_id) # Uses the helper to find .jpg/.JPG
            
            if filename:
                final_results.append({
                    "score": 100,
                    "diagnosis": disease_pretty.get(row['dx'], row['dx']),
                    "age": int(row['age']),
                    "sex": row['sex'],
                    "location": row.get('localization', 'unknown'),
                    "image_url": f"/images/{filename}"
                })

    return final_results

# ==========================================
# 5. SEARCH LOGIC B: IMAGE (AI VECTOR)
# ==========================================
def search_by_image(vector):
    print("   👉 Image Search Mode (AI)")
    api_url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search"
    headers = { "api-key": QDRANT_API_KEY, "Content-Type": "application/json" }
    
    # Try Strict First
    payload = {
        "vector": vector, "limit": 3, "with_payload": True,
        "filter": {"must": [{"key": "sex", "match": {"except": ["unknown", "null"]}}, {"key": "age", "range": {"gt": 0}}]}
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        results = response.json().get("result", [])
        
        # If Strict fails, Remove Filters
        if not results:
            print("      ⚠️ No strict matches. Dropping filters.")
            del payload["filter"]
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            results = response.json().get("result", [])
            
        # Format Results
        formatted = []
        disease_map = {'mel': 'Melanoma', 'nv': 'Nevus', 'bcc': 'Basal Cell Carcinoma', 'akiec': 'Actinic Keratosis', 'bkl': 'Benign Keratosis', 'vasc': 'Vascular', 'df': 'Dermatofibroma'}
        
        for hit in results:
            data = hit.get("payload", {})
            img_id = data.get('image_id', 'Unknown')
            filename = find_image_file(img_id) # Check file existence
            
            formatted.append({
                "score": round(hit.get("score", 0) * 100, 1),
                "diagnosis": disease_map.get(data.get('dx'), data.get('dx')),
                "age": data.get("age", "?"),
                "sex": data.get("sex", "?"),
                "location": data.get("localization", "?"),
                "image_url": f"/images/{filename}" if filename else None
            })
        return formatted
        
    except Exception as e:
        print(f"Error: {e}")
        return []

# ==========================================
# 6. ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(DATASET_DIR, filename)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' in request.files:
            # IMAGE SEARCH PATH
            file = request.files['file']
            img = Image.open(file).convert('RGB')
            query_vector = model.encode(img).tolist()
            results = search_by_image(query_vector)
            return jsonify(results)
            
        elif 'query' in request.form:
            # TEXT SEARCH PATH
            query_text = request.form['query']
            results = search_by_text(query_text)
            return jsonify(results)
            
        else:
            return jsonify({"error": "No input provided"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':

    app.run(port=5000, debug=True, use_reloader=False)
