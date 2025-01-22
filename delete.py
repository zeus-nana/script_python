import os
import shutil
from pathlib import Path

def supprimer(chemin):
    r"""
    Supprime un fichier ou un dossier, quel que soit le format du chemin (/ ou \).

    Args:
        chemin (str): Chemin du fichier ou dossier à supprimer

    Returns:
        bool: True si la suppression a réussi, False sinon
    """
    try:
        # Nettoie le chemin des guillemets éventuels
        chemin = chemin.strip('"').strip("'")

        # Normalise le chemin pour gérer / et \
        chemin = Path(chemin).resolve()

        if not chemin.exists():
            print(f"Erreur: Le chemin {chemin} n'existe pas.")
            return False

        if chemin.is_file():
            # Supprime le fichier
            os.remove(chemin)
            print(f"Fichier {chemin} supprimé avec succès.")
        else:
            # Supprime le dossier et son contenu
            shutil.rmtree(chemin)
            print(f"Dossier {chemin} et son contenu supprimés avec succès.")
        return True

    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        return False

if __name__ == "__main__":
    # Demande le chemin à l'utilisateur
    chemin = input("Entrez le chemin du fichier ou dossier à supprimer (sans guillemets): ")
    supprimer(chemin)