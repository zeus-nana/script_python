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

        print(f"Référence: {reference}, Montant: {montant}")

    # Créer un DataFrame avec les données extraites
    df = pd.DataFrame({
        'Reference': references,
        'Montant': montants
    })

    return df, tree.getroot()  # Retourner également la racine XML pour accéder à CtrlSum

# Exemple d'utilisation
if __name__ == "__main__":
    chemin_fichier = r"D:\code\280325\PAIN DU 31032025\PAIN111AA20250331100000ABIFR.xml"
    dossier_sortie = r"D:\code"

    try:
        # Extraire les données
        resultats, root = extraire_references_montants(chemin_fichier)

        # Afficher les résultats
        print(f"Nombre de transactions trouvées: {len(resultats)}")
        # print(resultats.head(10))  # Afficher les 10 premières lignes

        # Calculer le montant total
        total = resultats['Montant'].sum()
        print(f"\nMontant total: {total} EUR")

        # Vérifier la somme de contrôle (CtrlSum)
        namespaces = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.09'}
        ctrl_sum = Decimal(root.find('.//ns:CtrlSum', namespaces).text)
        print(f"Valeur CtrlSum: {ctrl_sum} EUR")

        # Calculer la différence
        difference = total - ctrl_sum
        print(f"Différence (total - CtrlSum): {difference} EUR")

        # S'assurer que le dossier de sortie existe
        os.makedirs(dossier_sortie, exist_ok=True)

        # Chemin complet du fichier de sortie
        chemin_sortie = os.path.join(dossier_sortie, 'resultats_pain001.csv')

        # Exporter vers CSV
        resultats.to_csv(chemin_sortie, index=False)
        print(f"Résultats exportés vers '{chemin_sortie}'")

        # DEBUT EXPORT BIGDECIMAL - Décommenter cette section pour générer le fichier BigDecimal

        # Chemin du fichier BigDecimal
        chemin_bigdecimal = os.path.join(dossier_sortie, 'montants_bigdecimal.txt')

        # Ouvrir le fichier texte pour écriture
        with open(chemin_bigdecimal, 'w') as f:
            f.write("BigDecimal[] valeurs = {\n")

            # Écrire chaque montant au format BigDecimal
            for i, montant in enumerate(resultats['Montant']):
                f.write(f'    new BigDecimal("{montant}")')

                # Ajouter une virgule sauf pour le dernier élément
                if i < len(resultats) - 1:
                    f.write(',\n')
                else:
                    f.write('\n')

            f.write("};\n")

        print(f"Fichier BigDecimal généré: '{chemin_bigdecimal}'")

        # FIN EXPORT BIGDECIMAL

    except Exception as e:
        print(f"Erreur lors du traitement du fichier: {e}")