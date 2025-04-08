import xml.etree.ElementTree as ET
import pandas as pd
import os
from decimal import Decimal, getcontext

getcontext().prec = 10

def extraire_references_montants(chemin_fichier):
    """
    Extrait les références et montants d'un fichier PAIN.001 (format XML ISO 20022)

    Args:
        chemin_fichier (str): Chemin vers le fichier XML

    Returns:
        pandas.DataFrame: DataFrame contenant les références et montants
        ElementTree.Element: Racine du document XML
    """
    # Définir les namespaces utilisés dans le document
    namespaces = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}

    # Charger le fichier XML
    tree = ET.parse(chemin_fichier)
    root = tree.getroot()

    # Initialiser les listes pour stocker les données
    references = []
    montants = []

    # Parcourir toutes les transactions de paiement
    for transaction in root.findall('.//ns:CdtTrfTxInf', namespaces):
        # Extraire la référence (EndToEndId)
        reference = transaction.find('.//ns:EndToEndId', namespaces).text

        # Extraire le montant (InstdAmt)
        montant_element = transaction.find('.//ns:InstdAmt', namespaces)
        montant = Decimal(montant_element.text)

        # Ajouter aux listes
        references.append(reference)
        montants.append(montant)

    # Créer un DataFrame avec les données extraites
    df = pd.DataFrame({
        'Reference': references,
        'Montant': montants
    })

    return df, root

def analyser_dossier_pain001(chemin_dossier):
    """
    Analyse tous les fichiers PAIN.001 dans un dossier et génère un rapport des différences de totaux

    Args:
        chemin_dossier (str): Chemin vers le dossier contenant les fichiers PAIN.001
    """
    namespaces = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}

    # Vérifier si le dossier existe
    if not os.path.isdir(chemin_dossier):
        print(f"Erreur: Le dossier '{chemin_dossier}' n'existe pas.")
        return

    # Obtenir la liste des fichiers XML dans le dossier
    fichiers_xml = [f for f in os.listdir(chemin_dossier) if f.lower().endswith('.xml')]

    if not fichiers_xml:
        print(f"Aucun fichier XML trouvé dans le dossier '{chemin_dossier}'.")
        return

    print("\n=== RAPPORT D'ANALYSE DES FICHIERS PAIN ===\n")

    resultats_globaux = {
        'nombre_fichiers': 0,
        'nombre_transactions': 0,
        'montant_total': Decimal('0'),
        'ctrl_sum_total': Decimal('0'),
        'difference_totale': Decimal('0'),
        'fichiers_avec_ecart': 0,
        'liste_fichiers_avec_ecart': []
    }

    # Traiter chaque fichier XML
    for fichier in fichiers_xml:
        chemin_fichier = os.path.join(chemin_dossier, fichier)

        try:
            # Extraire les données
            resultats, root = extraire_references_montants(chemin_fichier)

            # Calculer le montant total
            total = resultats['Montant'].sum()

            # Récupérer la somme de contrôle (CtrlSum)
            try:
                ctrl_sum = Decimal(root.find('.//ns:CtrlSum', namespaces).text)
            except (AttributeError, TypeError):
                ctrl_sum = Decimal('0')
                print(f"Avertissement: CtrlSum non trouvé dans le fichier '{fichier}'")

            # Calculer la différence
            difference = total - ctrl_sum

            # Mettre à jour les résultats globaux
            resultats_globaux['nombre_fichiers'] += 1
            resultats_globaux['nombre_transactions'] += len(resultats)
            resultats_globaux['montant_total'] += total
            resultats_globaux['ctrl_sum_total'] += ctrl_sum
            resultats_globaux['difference_totale'] += difference

            if difference != 0:
                resultats_globaux['fichiers_avec_ecart'] += 1
                resultats_globaux['liste_fichiers_avec_ecart'].append(fichier)

            # Afficher les résultats pour ce fichier
            print(f"\nFichier: {fichier}")
            print(f"  Nombre de transactions: {len(resultats)}")
            print(f"  Montant total calculé: {total} EUR")
            print(f"  Valeur CtrlSum: {ctrl_sum} EUR")
            print(f"  Différence: {difference} EUR")

            # Afficher un message d'alerte si la différence n'est pas nulle
            if difference != 0:
                print(f"  ⚠️  ATTENTION: Écart détecté de {difference} EUR!")
            else:
                print("  ✓ Sommes concordantes")

        except Exception as e:
            print(f"\nErreur lors du traitement du fichier '{fichier}': {e}")

    # Afficher le résumé global
    print("\n=== RÉSUMÉ GLOBAL ===")
    print(f"Nombre total de fichiers traités: {resultats_globaux['nombre_fichiers']}")
    print(f"Nombre total de transactions: {resultats_globaux['nombre_transactions']}")
    print(f"Montant total de toutes les transactions: {resultats_globaux['montant_total']} EUR")
    print(f"Total des sommes de contrôle (CtrlSum): {resultats_globaux['ctrl_sum_total']} EUR")
    print(f"Différence totale: {resultats_globaux['difference_totale']} EUR")
    print(f"Nombre de fichiers avec écart: {resultats_globaux['fichiers_avec_ecart']} / {resultats_globaux['nombre_fichiers']}")

    if resultats_globaux['difference_totale'] == 0:
        print("\n✓ BILAN: Toutes les sommes de contrôle concordent avec les montants calculés.")
    else:
        print(f"\n⚠️ BILAN: Des écarts ont été détectés pour un total de {resultats_globaux['difference_totale']} EUR.")
        print("\nFichiers présentant des écarts:")
        for i, fichier in enumerate(resultats_globaux['liste_fichiers_avec_ecart'], 1):
            print(f"  {i}. {fichier}")

# Exemple d'utilisation
if __name__ == "__main__":
    chemin_dossier = r"C:\Users\fnana\Downloads\Pain du 02042025"

    try:
        analyser_dossier_pain001(chemin_dossier)
    except Exception as e:
        print(f"Erreur lors de l'analyse du dossier: {e}")