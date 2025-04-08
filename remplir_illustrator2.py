import win32com.client
import os

# Chemins spécifiques
template_ai = r"C:\Users\fnana\Downloads\invitation_penda - 2.ai"
names_file = r"D:\code\guest-list - 2.txt"
output_folder = r"C:\Users\fnana\Downloads\billet_pentose\030225\02"

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

try:
    # Création du client Illustrator
    app = win32com.client.Dispatch('Illustrator.Application')

    # Lecture du fichier texte contenant les noms
    with open(names_file, 'r', encoding='utf-8') as f:
        names = [name.strip() for name in f.readlines() if name.strip()]

    # Pour chaque nom dans la liste
    for index, name in enumerate(names, 1):
        try:
            # Ouvrir le fichier template
            doc = app.Open(template_ai)

            # Cibler le calque spécifique et son texte
            nom_layer = doc.Layers.Item("NOM_INVITE")
            text_frame = nom_layer.TextFrames[0]

            # Remplacer le texte
            text_frame.Contents = name

            # Définir les options d'export PDF de manière plus simple
            pdf_options = win32com.client.Dispatch('Illustrator.PDFSaveOptions')
            # Minimiser les options pour éviter les erreurs
            pdf_options.Compatibility = 4  # Acrobat 5.0

            # Créer le nom du fichier PDF (nettoyé pour éviter les caractères problématiques)
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            pdf_path = os.path.join(output_folder, f"Invitation_{safe_name}.pdf")

            # Sauvegarder en PDF
            doc.SaveAs(pdf_path, pdf_options)

            # Fermer le document sans sauvegarder les modifications au fichier .ai
            doc.Close(2)  # 2 = aiDoNotSaveChanges

            print(f"Traitement {index}/{len(names)} : {name} - PDF créé avec succès")

        except Exception as e:
            print(f"Erreur lors du traitement de {name}: {str(e)}")
            continue

except Exception as e:
    print(f"Erreur générale : {str(e)}")

finally:
    # Fermer Adobe Illustrator
    if 'app' in locals():
        app.Quit()
    print("\nTraitement terminé")