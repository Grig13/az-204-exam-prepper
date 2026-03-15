import fitz  # PyMuPDF
import os
# CHANGED: Fixed import
import config

def ensure_directories():
    for folder in [config.IMAGES_DIR, config.SNAPSHOTS_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def save_page_diagrams(doc, page_num):
    """Extrage obiectele imagine (diagramele) de pe o pagină."""
    saved_images = []
    page = doc[page_num]
    image_list = page.get_images(full=True)
    if image_list:
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_name = f"page_{page_num + 1}_diagram_{img_index}.{image_ext}"
                image_path = os.path.join(config.IMAGES_DIR, image_name)

                if not os.path.exists(image_path):
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                saved_images.append(image_path)
            except: pass
    return saved_images

def render_page_snapshot(doc, page_num):
    """Face screenshot la întreaga pagină PDF pentru validare."""
    filename = f"page_{page_num + 1}.png"
    filepath = os.path.join(config.SNAPSHOTS_DIR, filename)
    if os.path.exists(filepath): return filepath

    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) # Zoom 150%
    pix.save(filepath)
    return filepath
