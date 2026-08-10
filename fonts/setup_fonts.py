"""Auto-download DejaVu fonts for PDF Unicode support."""
import os
import urllib.request
import zipfile
import shutil

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

# DejaVu fonts download URL
url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"
zip_path = os.path.join(FONT_DIR, "dejavu.zip")

try:
    print("Downloading DejaVu fonts...")
    urllib.request.urlretrieve(url, zip_path)
    print("Download complete.")

    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if name.endswith('.ttf') and 'DejaVuSans' in name:
                z.extract(name, FONT_DIR)
                # Flatten directory structure
                src = os.path.join(FONT_DIR, name)
                dst = os.path.join(FONT_DIR, os.path.basename(name))
                if src != dst and os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    shutil.move(src, dst)

    # Clean up zip
    os.remove(zip_path)

    # Remove empty subdirectories
    for root, dirs, files in os.walk(FONT_DIR, topdown=False):
        for d in dirs:
            dpath = os.path.join(root, d)
            try:
                if not os.listdir(dpath):
                    os.rmdir(dpath)
            except OSError:
                pass

    installed = [f for f in os.listdir(FONT_DIR) if f.endswith('.ttf')]
    print(f"\n✅ Fonts installed to: {FONT_DIR}")
    print(f"Installed files ({len(installed)}):")
    for f in sorted(installed):
        print(f"  - {f}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Please download manually from: https://dejavu-fonts.github.io/Download.html")