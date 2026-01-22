
# 🩺 DermAssist AI: Smart Clinical Search Engine for Dermatology

**DermAssist AI** is a hybrid search engine designed to assist dermatologists in identifying skin lesions. Unlike standard image classifiers that simply guess a diagnosis, this tool retrieves **verified historical cases** based on visual similarity and medical metadata (Age, Gender, Diagnosis).

It uses a **Hybrid Architecture**:
1.  **Visual Search:** Uses OpenAI's **CLIP** model and **Qdrant** (Vector DB) to find visually similar lesions.
2.  **Clinical Search:** Uses **Pandas** for strict, 100% accurate filtering of patient metadata (e.g., "Find Melanoma in 40-year-old Female").

---

## 🚀 Features
* **Context-Aware Search:** Filters results by Patient Age and Gender to ensure medical relevance.
* **Fail-Safe Logic:**
    * *Level 1:* Strict Match (Visual + Diagnosis + Demographics).
    * *Level 2:* Relaxed Match (Diagnosis Only).
    * *Level 3:* Visual Fallback (Finds similar looking images if metadata fails).
* **Quality Control:** Automatically filters out "Junk Data" (e.g., Unknown Gender, Age 0) from results.
* **Format Support:** robust handling of `.jpg`, `.JPG`, and `.png` image extensions.

---

## 📂 Dataset (Important!)
Due to the large file size, the image dataset is **not included** in this repository. You must download it separately to run the project.

**1. Download the Dataset:**
* Link: **(https://www.kaggle.com/datasets/jnegrini/skin-lesions-act-keratosis-and-melanoma)**


**2. Setup Instructions:**
* Download the images.
* Extract the zip file.
* Rename the folder containing the images to **`images`**.
* Place the `images` folder inside the root directory of this project.

 
 # Installation & Setup
1. Clone the Repository

Bash
git clone https://github.com/sumitsharma6354/DermAssist.git

2. Install Dependencies

Bash
pip install -r requirements.txt
3. Verify Metadata Ensure metadata.csv is present in the root folder. This file is critical for the Text Search feature to function.

# How to Run
Run the Flask application:

Bash
python app.py
Open your web browser and go to:

http://localhost:5000
# Technical Details
Hybrid Search Logic
The system intelligently decides which search method to use:

Image Uploads: Trigger the AI Engine (CLIP + Qdrant). The image is converted into a 512-dimensional vector and compared against the database using Cosine Similarity.

Text Queries: Trigger the Pandas Engine. The query (e.g., "Melanoma on female") is parsed to extract specific medical constraints, guaranteeing zero false positives for disease types.

# Quality Control
To prevent "garbage-in, garbage-out," the system enforces a strict Quality Filter:

Excludes records where Sex = Unknown or Null.

Excludes records where Age = 0.

Fail-Safe: If the strict filter removes all results, the system automatically relaxes the rules to ensure the user always receives a helpful visual reference.

# Future Scope
Heatmap Explanation (XAI): Implementing Grad-CAM to highlight why the AI flagged a specific area of the skin.

PDF Report Generation: One-click download of patient analysis for Electronic Health Records (EHR).

Real-time Dermoscopy: Integration with hardware dermoscopes for live analysis.

