import os

def afficher_structure(chemin, niveau=0, fichier_sortie=None, dossiers_exclus=None):
    """
    Affiche la structure d'un dossier avec ses sous-dossiers et fichiers.

    :param chemin: Le chemin du dossier à analyser
    :param niveau: Le niveau d'indentation (utilisé pour la récursion)
    :param fichier_sortie: Le fichier dans lequel écrire la structure
    :param dossiers_exclus: Liste des dossiers à exclure (optionnel)
    """
    if dossiers_exclus is None:
        dossiers_exclus = []

    nom_dossier = os.path.basename(chemin)

    # Vérifier si le dossier courant doit être exclu (sauf pour le dossier racine)
    if niveau > 0 and nom_dossier in dossiers_exclus:
        return

    ligne = '  ' * niveau + '+--' + nom_dossier

    print(ligne)
    if fichier_sortie:
        fichier_sortie.write(ligne + '\n')

    try:
        elements = os.listdir(chemin)
    except PermissionError:
        ligne = '  ' * (niveau + 1) + 'Permission refusée'
        print(ligne)
        if fichier_sortie:
            fichier_sortie.write(ligne + '\n')
        return

    dossiers = []
    fichiers = []
    for element in elements:
        chemin_complet = os.path.join(chemin, element)
        if os.path.isdir(chemin_complet):
            if element not in dossiers_exclus:  # Vérifier si le dossier doit être exclu
                dossiers.append(element)
        else:
            fichiers.append(element)

    for dossier in sorted(dossiers):
        chemin_complet = os.path.join(chemin, dossier)
        afficher_structure(chemin_complet, niveau + 1, fichier_sortie, dossiers_exclus)

    for fichier in sorted(fichiers):
        ligne = '  ' * (niveau + 1) + '+--' + fichier
        print(ligne)
        if fichier_sortie:
            fichier_sortie.write(ligne + '\n')

# Demander à l'utilisateur le chemin du dossier à analyser
chemin_dossier = input("Entrez le chemin du dossier à analyser : ")

# Définir les dossiers à exclure
dossiers_exclus = ['node_modules', 'data', '.idea', 'dist']

# Vérifier si le chemin existe
if os.path.exists(chemin_dossier):
    # Obtenir le chemin du dossier Documents
    documents_path = os.path.join(os.path.expanduser('~'), 'Documents')

    # Créer le dossier Documents s'il n'existe pas
    os.makedirs(documents_path, exist_ok=True)

    # Définir le chemin complet du fichier de sortie dans le dossier Documents
    nom_fichier_sortie = os.path.join(documents_path, "structure_projet_ong.txt")

    # Ouvrir le fichier en mode écriture
    with open(nom_fichier_sortie, 'w', encoding='utf-8') as fichier_sortie:
        print(f"Structure du dossier '{chemin_dossier}':")
        fichier_sortie.write(f"Structure du dossier '{chemin_dossier}':\n")
        afficher_structure(chemin_dossier, fichier_sortie=fichier_sortie, dossiers_exclus=dossiers_exclus)

    print(f"\nLa structure du dossier a été sauvegardée dans le fichier '{nom_fichier_sortie}'")
else:
    print("Le chemin spécifié n'existe pas.")