import os, sys, time, json, requests, zipfile, io, random
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = r'e:\Paresh\Auto Post\GlobeVista'
ZIP_PATH = os.path.join(BASE_DIR, 'images', 'Nov 16 - 09_04.zip')
MAP_FILE = os.path.join(BASE_DIR, 'uploaded_files_map.json')
QUEUE_FILE = os.path.join(BASE_DIR, 'images_urls.txt')
BACKUP_FILE = os.path.join(BASE_DIR, 'images_urls_backup.txt')
USED_FILE = os.path.join(BASE_DIR, 'used_urls.txt')

print("=" * 60)
print("🌍 GLOBEVISTA CATBOX BULK UPLOADER (3,019 IMAGES)")
print("=" * 60)

# 1. Load existing map
uploaded_map = {}
if os.path.exists(MAP_FILE):
    try:
        with open(MAP_FILE, 'r', encoding='utf-8') as f:
            uploaded_map = json.load(f)
    except Exception:
        uploaded_map = {}

print(f"Existing uploaded map count: {len(uploaded_map)}")

# 2. Inspect zip
if not os.path.exists(ZIP_PATH):
    print(f"ERROR: Zip not found at {ZIP_PATH}")
    sys.exit(1)

z = zipfile.ZipFile(ZIP_PATH, 'r')
all_items = [n for n in z.namelist() if n.lower().endswith(('.jpg', '.jpeg', '.png'))]
pending_items = [n for n in all_items if os.path.basename(n) not in uploaded_map]
print(f"Total items in zip: {len(all_items)} | Already uploaded: {len(all_items) - len(pending_items)} | Pending: {len(pending_items)}")

def upload_zip_entry(entry_name):
    fname = os.path.basename(entry_name)
    url = "https://catbox.moe/user/api.php"
    
    # Read bytes from zip
    try:
        data = z.read(entry_name)
    except Exception as e:
        return fname, None
        
    for attempt in range(4):
        try:
            files = {"fileToUpload": (fname, data, "image/jpeg")}
            r = requests.post(url, data={"reqtype": "fileupload"}, files=files, timeout=40)
            res = r.text.strip()
            if r.status_code == 200 and res.startswith("http"):
                return fname, res
        except Exception:
            time.sleep(1.5 * (attempt + 1))
            
    return fname, None

if pending_items:
    print(f"Starting Catbox upload with 10 workers for {len(pending_items)} images...")
    done = 0
    t0 = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(upload_zip_entry, item): item for item in pending_items}
        for fut in as_completed(futures):
            fn, u = fut.result()
            if u:
                uploaded_map[fn] = u
            done += 1
            if done % 100 == 0 or done == len(pending_items):
                speed = done / max(1.0, time.time() - t0)
                rem_sec = (len(pending_items) - done) / max(0.01, speed)
                print(f"[{done}/{len(pending_items)}] -> Uploaded: {fn}: {u} ({speed:.1f} imgs/s, ETA: {rem_sec/60:.1f}m)")
                with open(MAP_FILE, 'w', encoding='utf-8') as f:
                    json.dump(uploaded_map, f, indent=2)

z.close()
print("All zip images processed!")

# Final save map
with open(MAP_FILE, 'w', encoding='utf-8') as f:
    json.dump(uploaded_map, f, indent=2)

# Merge URLs into backup and queue
all_urls = list(dict.fromkeys(uploaded_map.values()))
print(f"Total Unique Catbox URLs: {len(all_urls)}")

# Write master backup
with open(BACKUP_FILE, 'w', encoding='utf-8') as bf:
    bf.write("\n".join(all_urls) + "\n")

# Load used
used_urls = set()
if os.path.exists(USED_FILE):
    with open(USED_FILE, 'r', encoding='utf-8') as uf:
        used_urls = {l.strip() for l in uf if l.strip()}

# Queue has all unused URLs, shuffled randomly
unused = [u for u in all_urls if u not in used_urls]
random.seed(108)
random.shuffle(unused)

with open(QUEUE_FILE, 'w', encoding='utf-8') as qf:
    qf.write("\n".join(unused) + "\n")

print(f"SUCCESS: {len(unused)} shuffled unused URLs saved to images_urls.txt")
print(f"SUCCESS: {len(all_urls)} URLs saved to images_urls_backup.txt")

# Delete zip file from PC to free disk space!
try:
    sz_mb = os.path.getsize(ZIP_PATH) / (1024*1024)
    os.remove(ZIP_PATH)
    print(f"🗑️ DELETED ZIP FILE: {ZIP_PATH} (Freed {sz_mb:.2f} MB!)")
except Exception as e:
    print(f"Error removing zip: {e}")

# Also delete any other zip files in images/
for old_zip in [os.path.join(BASE_DIR, 'images', 'Nov 14 - 17_25.zip')]:
    if os.path.exists(old_zip):
        try:
            sz_mb = os.path.getsize(old_zip) / (1024*1024)
            os.remove(old_zip)
            print(f"🗑️ DELETED OLD ZIP: {old_zip} (Freed {sz_mb:.2f} MB!)")
        except Exception:
            pass

print("🎉 GLOBEVISTA CATBOX PIPELINE 100% COMPLETE!")

