import cv2
import os
import sys
import numpy as np
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(r"E:\Paresh\Auto Post\GlobeVista")
EXTRACT_DIR = BASE_DIR / "images" / "extracted"
QUEUE_FILE = BASE_DIR / "images_urls.txt"
BACKUP_FILE = BASE_DIR / "images_urls_backup.txt"

# Exact Flow star watermark polygon (896x1200)
cx, cy = 795, 1099
pts = np.array([
    [cx, cy - 31],       # top (795, 1068)
    [cx + 10, cy - 13],  # top-right (805, 1086)
    [cx + 25, cy],       # right (820, 1099)
    [cx + 10, cy + 13],  # bottom-right (805, 1112)
    [cx, cy + 31],       # bottom (795, 1130)
    [cx - 10, cy + 13],  # bottom-left (785, 1112)
    [cx - 25, cy],       # left (770, 1099)
    [cx - 10, cy - 13],  # top-left (785, 1086)
], np.int32)

mask = np.zeros((1200, 896), dtype=np.uint8)
cv2.fillPoly(mask, [pts], 255)
mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=1)

def clean_watermark(img):
    """Clean the Flow watermark without cropping."""
    return cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

def upload_to_catbox(image_bytes):
    """Upload jpeg bytes to Catbox.moe."""
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    files = {"fileToUpload": ("travel_place.jpg", image_bytes, "image/jpeg")}
    try:
        r = requests.post(url, data=data, files=files, timeout=30)
        if r.status_code == 200 and r.text.strip().startswith("http"):
            return r.text.strip()
    except Exception as e:
        print(f"Upload error: {e}")
    return None

def process_file(file_name):
    p = EXTRACT_DIR / file_name
    img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return None
    
    cleaned = clean_watermark(img)
    _, buf = cv2.imencode(".jpg", cleaned, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    url = upload_to_catbox(buf.tobytes())
    return url

def main():
    files = [f for f in os.listdir(EXTRACT_DIR) if f.endswith(".jpg")]
    print(f"Found {len(files)} extracted travel images.")
    
    target_count = 60
    candidates = files[:target_count]
    print(f"Processing and uploading {len(candidates)} images to Catbox...")
    
    urls = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(process_file, f): f for f in candidates}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                urls.append(res)
                print(f"[{len(urls)}/{target_count}] Uploaded: {res}")
    
    print(f"\nSuccessfully uploaded {len(urls)} images to Catbox.")
    
    # Save to queue and backup
    existing_urls = []
    if QUEUE_FILE.exists():
        existing_urls = [l.strip() for l in QUEUE_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    
    all_urls = list(dict.fromkeys(existing_urls + urls))
    
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_urls) + "\n")
    
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_urls) + "\n")
        
    print(f"Saved {len(all_urls)} URLs to images_urls.txt and images_urls_backup.txt.")

if __name__ == "__main__":
    main()
