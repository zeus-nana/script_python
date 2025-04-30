# Chemin du fichier: "D:\Téléchargements\Telegram Desktop\IMG_20250428_172945_252.jpg"
from PIL import Image

# Chemin de l'image source
chemin_source = r"D:\Téléchargements\Telegram Desktop\IMG_20250428_172945_252.jpg"

# Chemin pour l'image convertie (même nom mais avec extension .jpeg)
chemin_destination = chemin_source.replace('.jpg', '.jpeg')

# Ouvrir l'image
img = Image.open(chemin_source)

# Sauvegarder l'image au format JPEG
img.save(chemin_destination, "JPEG")

print(f"Image convertie et sauvegardée sous: {chemin_destination}")