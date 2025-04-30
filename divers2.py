import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz  # Bibliothèque pour le matching approximatif
import re

def nettoyer_telephone(tel):
    """Nettoie un numéro de téléphone en supprimant tous les caractères non numériques"""
    if pd.isna(tel):
        return ""
    return re.sub(r'\D', '', str(tel))

def nettoyer_nom(nom):
    """Nettoie un nom en supprimant les accents, mettant en minuscules, etc."""
    if pd.isna(nom):
        return ""
    nom = str(nom).lower().strip()
    # On pourrait ajouter d'autres normalisations (accents, etc.)
    return nom

def nettoyer_cni(cni):
    """Nettoie un numéro CNI en supprimant espaces et caractères spéciaux"""
    if pd.isna(cni):
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(cni))

def calculer_similarite_client(client1, client2, poids=None):
    """
    Calcule un score de similarité entre deux clients.

    Args:
        client1, client2: Lignes de DataFrame contenant les informations des clients
        poids: Dictionnaire avec les poids à attribuer à chaque champ

    Returns:
        Score de similarité (0 à 100)
    """
    if poids is None:
        poids = {
            'telephone': 25,  # 25% du score total
            'nom': 20,        # 20% du score total
            'prenom': 15,     # 15% du score total
            'cni': 40         # 40% du score total
        }

    score_total = 0

    # 1. Comparaison des numéros de téléphone (matching exact après nettoyage)
    tel1 = nettoyer_telephone(client1['telephone'])
    tel2 = nettoyer_telephone(client2['telephone'])

    if tel1 and tel2 and tel1 == tel2:
        score_total += poids['telephone']

    # 2. Comparaison des noms (matching approximatif)
    nom1 = nettoyer_nom(client1['nom'])
    nom2 = nettoyer_nom(client2['nom'])

    if nom1 and nom2:
        sim_nom = fuzz.token_sort_ratio(nom1, nom2)  # Compare en ignorant l'ordre des mots
        score_total += (sim_nom / 100) * poids['nom']

    # 3. Comparaison des prénoms (matching approximatif)
    prenom1 = nettoyer_nom(client1['prenom'])
    prenom2 = nettoyer_nom(client2['prenom'])

    if prenom1 and prenom2:
        sim_prenom = fuzz.token_sort_ratio(prenom1, prenom2)
        score_total += (sim_prenom / 100) * poids['prenom']

    # 4. Comparaison des numéros CNI (matching exact après nettoyage)
    cni1 = nettoyer_cni(client1['cni'])
    cni2 = nettoyer_cni(client2['cni'])

    if cni1 and cni2 and cni1 == cni2:
        score_total += poids['cni']

    return score_total

def trouver_doublons(df, seuil_similarite=75, poids=None):
    """
    Trouve les doublons potentiels dans le DataFrame.

    Args:
        df: DataFrame avec les données clients
        seuil_similarite: Seuil minimum de similarité (0-100) pour considérer un doublon
        poids: Dictionnaire avec les poids à attribuer à chaque champ

    Returns:
        DataFrame contenant les paires de doublons potentiels avec leur score
    """
    # Liste pour stocker les résultats
    doublons = []

    # Optimisation: pré-blocage sur le téléphone pour réduire les comparaisons
    # Grouper les clients par téléphone (après nettoyage)
    df['telephone_clean'] = df['telephone'].apply(nettoyer_telephone)
    groupes_tel = df.groupby('telephone_clean')

    # 1. Vérifier les doublons par téléphone
    for tel, groupe in groupes_tel:
        if len(groupe) > 1 and tel != "":  # Si plusieurs clients ont le même téléphone
            # Comparer chaque paire dans ce groupe
            indices = groupe.index.tolist()
            for i in range(len(indices)):
                for j in range(i+1, len(indices)):
                    client1 = df.loc[indices[i]]
                    client2 = df.loc[indices[j]]

                    score = calculer_similarite_client(client1, client2, poids)

                    if score >= seuil_similarite:
                        doublons.append({
                            'index1': indices[i],
                            'index2': indices[j],
                            'client1': f"{client1['nom']} {client1['prenom']}",
                            'client2': f"{client2['nom']} {client2['prenom']}",
                            'telephone1': client1['telephone'],
                            'telephone2': client2['telephone'],
                            'cni1': client1['cni'],
                            'cni2': client2['cni'],
                            'score': score
                        })

    # 2. Recherche par CNI
    df['cni_clean'] = df['cni'].apply(nettoyer_cni)
    groupes_cni = df.groupby('cni_clean')

    for cni, groupe in groupes_cni:
        if len(groupe) > 1 and cni != "":  # Si plusieurs clients ont la même CNI
            indices = groupe.index.tolist()
            for i in range(len(indices)):
                for j in range(i+1, len(indices)):
                    client1 = df.loc[indices[i]]
                    client2 = df.loc[indices[j]]

                    # Vérifier si cette paire a déjà été ajoutée (via téléphone)
                    paire_existante = any(
                        (d['index1'] == indices[i] and d['index2'] == indices[j]) or
                        (d['index1'] == indices[j] and d['index2'] == indices[i])
                        for d in doublons
                    )

                    if not paire_existante:
                        score = calculer_similarite_client(client1, client2, poids)

                        if score >= seuil_similarite:
                            doublons.append({
                                'index1': indices[i],
                                'index2': indices[j],
                                'client1': f"{client1['nom']} {client1['prenom']}",
                                'client2': f"{client2['nom']} {client2['prenom']}",
                                'telephone1': client1['telephone'],
                                'telephone2': client2['telephone'],
                                'cni1': client1['cni'],
                                'cni2': client2['cni'],
                                'score': score
                            })

    # 3. Pour les clients restants, comparaison par nom/prénom
    # Pour les grandes bases, cette étape peut être limitée ou ignorée car coûteuse

    # Créer un DataFrame à partir des résultats
    if doublons:
        return pd.DataFrame(doublons).sort_values('score', ascending=False)
    else:
        return pd.DataFrame(columns=['index1', 'index2', 'client1', 'client2',
                                     'telephone1', 'telephone2', 'cni1', 'cni2', 'score'])

# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple de données
    data = {
        'nom': ['Dupont', 'Dupond', 'Martin', 'Martine', 'Dubois', 'Duboix'],
        'prenom': ['Jean', 'Jean-Pierre', 'Marie', 'Marie', 'Paul', 'Paul'],
        'telephone': ['0612345678', '06 12 34 56 78', '0698765432', '0698765432', '0654321789', '0654321789'],
        'cni': ['123ABC456', '123ABC456', '789XYZ012', '789XYZ012', 'AB123456', 'AB-123-456']
    }

    df = pd.DataFrame(data)
    print("Base de données originale:")
    print(df)
    print("\n")

    # Configuration des poids pour chaque champ
    poids_personnalises = {
        'telephone': 30,
        'nom': 25,
        'prenom': 15,
        'cni': 30
    }

    # Détection des doublons
    resultats = trouver_doublons(df, seuil_similarite=70, poids=poids_personnalises)

    if not resultats.empty:
        print("Doublons détectés:")
        print(resultats[['client1', 'client2', 'score']])

        # Suggestion de fusion
        print("\nGroupes de doublons proposés:")

        # Création d'un graphe de doublons
        import networkx as nx
        G = nx.Graph()

        # Ajouter tous les clients comme nœuds
        for idx in df.index:
            G.add_node(idx)

        # Ajouter les arêtes pour les doublons
        for _, row in resultats.iterrows():
            G.add_edge(row['index1'], row['index2'], weight=row['score'])

        # Trouver les composantes connexes (groupes de doublons)
        groupes = list(nx.connected_components(G))

        for i, groupe in enumerate(groupes):
            if len(groupe) > 1:  # Si le groupe contient plus d'un client
                print(f"Groupe {i+1}:")
                for idx in groupe:
                    client = df.loc[idx]
                    print(f"  - {client['nom']} {client['prenom']}, Tel: {client['telephone']}, CNI: {client['cni']}")
    else:
        print("Aucun doublon détecté avec le seuil spécifié.")