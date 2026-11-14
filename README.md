# GlobeVista - Travel Auto Poster 🌍

Automated daily travel content poster for **Facebook Page** (GlobeVista) & **Instagram** (@GlobeVista1).

## ✨ Features
- 📸 Posts 1 travel image daily at **4:00 PM IST**
- 🤖 Gemini Vision AI analyzes each image and writes a unique caption
- 📝 Caption includes: Place name, brief history, why to visit, hashtags
- 🔄 Smart image queue system (auto-refills from backup)
- 📱 Simultaneous Facebook + Instagram posting

## 📁 File Structure
```
GlobeVista/
├── auto_poster.py          # Main posting script
├── fb_config.json          # Page & IG account IDs
├── images_urls.txt         # Active image queue (add URLs here)
├── images_urls_backup.txt  # Backup pool (refills queue when empty)
├── used_urls.txt           # Posted images log
└── .github/workflows/
    └── daily_post.yml      # GitHub Actions schedule
```

## 🖼️ Adding Images
Add public image URLs to `images_urls.txt` (one per line).
Also add same URLs to `images_urls_backup.txt` for the refill pool.

## ⚙️ GitHub Secrets Required
- `FB_PAGE_ACCESS_TOKEN` — Facebook Page Access Token
- `GEMINI_API_KEY` — Google Gemini API Key

