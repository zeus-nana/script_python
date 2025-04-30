# Path: D:\code\reconart\Matching\Admin\combine_images.py

import os
import glob
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import math

# Chemin du dossier contenant les images PNG
input_folder = r"D:\code\reconart\Matching\Admin"
# Dossier de sortie pour les PDF
output_folder = r"D:\code\reconart\Matching\Admin"

# Récupérer tous les fichiers PNG
png_files = glob.glob(os.path.join(input_folder, "*.png"))
png_files.sort()  # Trier les fichiers par nom

# Nombre d'images par PDF
images_per_pdf = 10

# Calculer le nombre de PDF à créer
num_pdfs = math.ceil(len(png_files) / images_per_pdf)

for pdf_index in range(num_pdfs):
    # Déterminer les images pour ce PDF
    start_idx = pdf_index * images_per_pdf
    end_idx = min((pdf_index + 1) * images_per_pdf, len(png_files))
    current_batch = png_files[start_idx:end_idx]

    # Nom du fichier PDF à créer
    pdf_filename = os.path.join(output_folder, f"combined_images_{pdf_index + 1}.pdf")

    # Créer un nouveau PDF
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    for i, img_path in enumerate(current_batch):
        # Ouvrir l'image avec PIL
        img = Image.open(img_path)

        # Créer une nouvelle page pour chaque image (sauf la première)
        if i > 0:
            c.showPage()

        # Calculer les dimensions pour adapter l'image à la page
        img_width, img_height = img.size
        margin = 50  # Marge en points

        # Calculer le ratio pour ajuster l'image à la page
        width_ratio = (width - 2 * margin) / img_width
        height_ratio = (height - 2 * margin) / img_height
        ratio = min(width_ratio, height_ratio)

        # Nouvelles dimensions de l'image
        new_width = img_width * ratio
        new_height = img_height * ratio

        # Position pour centrer l'image sur la page
        x = (width - new_width) / 2
        y = (height - new_height) / 2

        # Dessiner l'image sur la page
        c.drawImage(img_path, x, y, width=new_width, height=new_height)

    # Sauvegarder le PDF
    c.save()

print(f"{num_pdfs} fichiers PDF ont été créés dans {output_folder}")