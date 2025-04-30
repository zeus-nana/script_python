# Chemin: file_tree_generator.py
# Script pour générer l'arbre de fichiers d'un dossier donné

import os
import sys

# Définir le chemin du projet directement dans le code
PROJECT_PATH = r"C:\Users\fnana\IdeaProjects\projet_cera"

def generate_file_tree(directory, prefix="", is_last=True, exclude_patterns=None):
    """
    Génère récursivement un arbre de fichiers pour le dossier spécifié.

    Args:
        directory (str): Chemin du dossier à explorer
        prefix (str): Préfixe pour l'indentation
        is_last (bool): Indique si c'est le dernier élément du dossier parent
        exclude_patterns (list): Motifs de noms à exclure
    """
    if exclude_patterns is None:
        exclude_patterns = []

    # Obtenir le nom de base du dossier
    base_name = os.path.basename(directory)

    # Définir les caractères pour l'arbre
    connector = "└── " if is_last else "├── "

    # Afficher le dossier actuel
    print(f"{prefix}{connector}{base_name}")

    # Préparer le préfixe pour les enfants
    child_prefix = prefix + ("    " if is_last else "│   ")

    try:
        # Lister tous les fichiers et dossiers
        items = sorted(os.listdir(directory))

        # Filtrer les éléments exclus
        filtered_items = [item for item in items if not any(pattern in item for pattern in exclude_patterns)]

        # Compter les dossiers visibles pour déterminer le dernier
        visible_items = len(filtered_items)

        for index, item in enumerate(filtered_items):
            item_path = os.path.join(directory, item)

            # Vérifier si c'est un dossier
            if os.path.isdir(item_path):
                # Récursion pour les sous-dossiers
                generate_file_tree(
                    item_path,
                    child_prefix,
                    index == visible_items - 1,
                    exclude_patterns
                )
            else:
                # C'est un fichier, l'afficher simplement
                is_last_file = index == visible_items - 1
                file_connector = "└── " if is_last_file else "├── "
                print(f"{child_prefix}{file_connector}{item}")

    except PermissionError:
        print(f"{child_prefix}└── [Accès refusé]")
    except Exception as e:
        print(f"{child_prefix}└── [Erreur: {str(e)}]")

if __name__ == "__main__":
    # Vérifier si un chemin est fourni comme argument
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        # Utiliser le chemin défini dans la variable PROJECT_PATH
        path = PROJECT_PATH
        print(f"Utilisation du chemin défini dans le code: {path}")

    # Motifs à exclure (peut être personnalisé)
    exclusions = [".git", "__pycache__", "node_modules", ".vscode", ".idea", "dist"]

    print(f"Arbre de fichiers pour: {path}\n")

    # Vérifier si le chemin existe
    if os.path.exists(path):
        # Générer l'arbre
        generate_file_tree(path, exclude_patterns=exclusions)
    else:
        print(f"Le chemin '{path}' n'existe pas.")