# Fichier: analyse_doublons_client_eumm.py
import psycopg2
import pandas as pd
import numpy as np
from Levenshtein import distance, ratio
import itertools
from collections import defaultdict
import json
import os
from datetime import datetime
import time
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# Paramètres de connexion
conn_params = {
    'dbname': 'uni',
    'user': 'postgres',
    'password': 'trinita',
    'host': 'localhost'
}

def connect_to_db():
    """Établit une connexion à la base de données PostgreSQL."""
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except Exception as e:
        print(f"Erreur lors de la connexion à la base de données: {e}")
        return None

def fetch_data():
    """Récupère les données de la table client_eumm."""
    conn = connect_to_db()
    if not conn:
        return None

    try:
        query = """
        SELECT id, nom_prenom, date_de_naissance, lieu_de_naissance, 
               type_piece_identite, numero_piece_identite, date_expiration_piece
        FROM public.client_eumm limit 1000;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Erreur lors de la récupération des données: {e}")
        conn.close()
        return None

def clean_identity_number(numero):
    """Nettoie le numéro de pièce d'identité."""
    if pd.isna(numero):
        return ""
    return str(numero).strip().upper()

def prepare_data(df):
    """Prépare les données pour l'analyse."""
    # Nettoyage des champs
    df['nom_prenom'] = df['nom_prenom'].fillna('')

    # Séparation nom/prénom (séparateur antislash)
    nom_prenom_split = df['nom_prenom'].str.split('/', n=1, expand=True)
    df['nom'] = nom_prenom_split[0].str.strip() if 0 in nom_prenom_split.columns else ''
    df['prenom'] = nom_prenom_split[1].str.strip() if 1 in nom_prenom_split.columns else ''

    # Création d'un champ nom complet standardisé
    df['full_name'] = df['nom_prenom'].str.lower().str.strip()

    # Nettoyage du numéro de pièce d'identité
    df['clean_numero_piece'] = df['numero_piece_identite'].apply(clean_identity_number)

    # Format de la date de naissance (si nécessaire)
    if 'date_de_naissance' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date_de_naissance']):
        try:
            df['date_de_naissance'] = pd.to_datetime(df['date_de_naissance'], errors='coerce')
        except:
            pass

    return df

def find_exact_duplicates(df):
    """Trouve les doublons exacts basés sur différentes combinaisons de champs."""
    duplicates = {
        'piece_identite': df[df.duplicated(subset=['clean_numero_piece'], keep=False) &
                             ~df['clean_numero_piece'].isna() &
                             (df['clean_numero_piece'] != '')].sort_values('clean_numero_piece'),

        'name_dob': df[df.duplicated(subset=['full_name', 'date_de_naissance'], keep=False) &
                       ~df['full_name'].isna() &
                       (df['full_name'] != '') &
                       ~df['date_de_naissance'].isna()].sort_values(['full_name', 'date_de_naissance']),

        'name_lieu': df[df.duplicated(subset=['full_name', 'lieu_de_naissance'], keep=False) &
                        ~df['full_name'].isna() &
                        (df['full_name'] != '') &
                        ~df['lieu_de_naissance'].isna() &
                        (df['lieu_de_naissance'] != '')].sort_values(['full_name', 'lieu_de_naissance']),
    }

    return duplicates

def find_fuzzy_name_duplicates(df, threshold=0.9):
    """
    Trouve les doublons basés sur la similarité des noms (méthode fuzzy).
    """
    # Pour limiter la complexité, on peut d'abord regrouper par première lettre du nom
    df['first_letter'] = df['full_name'].str[0:1]

    duplicate_groups = []

    # Pour chaque première lettre
    for letter in df['first_letter'].dropna().unique():
        letter_df = df[df['first_letter'] == letter].copy()

        # Si trop peu d'enregistrements, passer
        if len(letter_df) <= 1:
            continue

        # Comparer chaque paire d'enregistrements
        for i, j in itertools.combinations(letter_df.index, 2):
            name_i = letter_df.loc[i, 'full_name']
            name_j = letter_df.loc[j, 'full_name']

            # Calculer la similarité
            similarity = ratio(name_i, name_j)

            # Si similarity dépasse le seuil et d'autres champs correspondent
            if similarity >= threshold:
                # Vérifier si d'autres champs correspondent
                dob_match = (not pd.isna(letter_df.loc[i, 'date_de_naissance']) and
                             not pd.isna(letter_df.loc[j, 'date_de_naissance']) and
                             letter_df.loc[i, 'date_de_naissance'] == letter_df.loc[j, 'date_de_naissance'])

                lieu_match = (not pd.isna(letter_df.loc[i, 'lieu_de_naissance']) and
                              not pd.isna(letter_df.loc[j, 'lieu_de_naissance']) and
                              letter_df.loc[i, 'lieu_de_naissance'] == letter_df.loc[j, 'lieu_de_naissance'])

                if dob_match or lieu_match:
                    duplicate_groups.append({
                        'id1': int(letter_df.loc[i, 'id']),
                        'id2': int(letter_df.loc[j, 'id']),
                        'name1': letter_df.loc[i, 'full_name'],
                        'name2': letter_df.loc[j, 'full_name'],
                        'similarity': float(similarity),
                        'dob_match': bool(dob_match),
                        'lieu_match': bool(lieu_match)
                    })

    return duplicate_groups

def generate_summary_stats(df, exact_duplicates, fuzzy_duplicates):
    """Génère des statistiques récapitulatives pour le dashboard."""
    # Statistiques de base
    stats = {
        'total_records': len(df),
        'unique_names': df['full_name'].nunique(),
        'unique_pieces': df['clean_numero_piece'].dropna().nunique(),
        'exact_duplicates': {
            'piece_identite': len(exact_duplicates['piece_identite']),
            'name_dob': len(exact_duplicates['name_dob']),
            'name_lieu': len(exact_duplicates['name_lieu']),
        },
        'fuzzy_duplicates': len(fuzzy_duplicates),
        'potential_unique_customers': len(df) - max(
            len(exact_duplicates['piece_identite']),
            len(exact_duplicates['name_dob']),
            len(exact_duplicates['name_lieu'])
        ) - len(fuzzy_duplicates)
    }

    # Statistiques détaillées sur les doublons fuzzy
    if fuzzy_duplicates:
        fuzzy_df = pd.DataFrame(fuzzy_duplicates)

        # Conversion des colonnes booléennes pour éviter les erreurs de type
        fuzzy_df['dob_match'] = fuzzy_df['dob_match'].astype(bool)
        fuzzy_df['lieu_match'] = fuzzy_df['lieu_match'].astype(bool)

        stats['fuzzy_stats'] = {
            'avg_similarity': fuzzy_df['similarity'].mean(),
            'min_similarity': fuzzy_df['similarity'].min(),
            'max_similarity': fuzzy_df['similarity'].max(),
            'median_similarity': fuzzy_df['similarity'].median(),
            'similarity_distribution': {
                '0.7-0.8': len(fuzzy_df[(fuzzy_df['similarity'] >= 0.7) & (fuzzy_df['similarity'] < 0.8)]),
                '0.8-0.9': len(fuzzy_df[(fuzzy_df['similarity'] >= 0.8) & (fuzzy_df['similarity'] < 0.9)]),
                '0.9-1.0': len(fuzzy_df[(fuzzy_df['similarity'] >= 0.9) & (fuzzy_df['similarity'] <= 1.0)]),
            },
            'dob_matches': fuzzy_df['dob_match'].sum(),
            'lieu_matches': fuzzy_df['lieu_match'].sum(),
            'dob_and_lieu_matches': len(fuzzy_df[fuzzy_df['dob_match'] & fuzzy_df['lieu_match']]),
            'percent_with_dob_match': (fuzzy_df['dob_match'].sum() / len(fuzzy_df)) * 100 if len(fuzzy_df) > 0 else 0,
            'percent_with_lieu_match': (fuzzy_df['lieu_match'].sum() / len(fuzzy_df)) * 100 if len(fuzzy_df) > 0 else 0
        }
    else:
        stats['fuzzy_stats'] = {
            'avg_similarity': 0,
            'min_similarity': 0,
            'max_similarity': 0,
            'median_similarity': 0,
            'similarity_distribution': {'0.7-0.8': 0, '0.8-0.9': 0, '0.9-1.0': 0},
            'dob_matches': 0,
            'lieu_matches': 0,
            'dob_and_lieu_matches': 0,
            'percent_with_dob_match': 0,
            'percent_with_lieu_match': 0
        }

    return stats

def group_duplicates(df, exact_duplicates, fuzzy_duplicates):
    """
    Groupe les doublons pour identifier les clients uniques.
    """
    # Créer un graphe des relations entre enregistrements
    graph = defaultdict(set)

    # Ajouter les relations pour les doublons de pièce d'identité
    for piece, group in exact_duplicates['piece_identite'].groupby('clean_numero_piece'):
        ids = group['id'].tolist()
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                graph[ids[i]].add(ids[j])
                graph[ids[j]].add(ids[i])

    # Ajouter les relations pour les doublons de nom+dob
    for _, group in exact_duplicates['name_dob'].groupby(['full_name', 'date_de_naissance']):
        ids = group['id'].tolist()
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                graph[ids[i]].add(ids[j])
                graph[ids[j]].add(ids[i])

    # Ajouter les relations pour les doublons de nom+lieu
    for _, group in exact_duplicates['name_lieu'].groupby(['full_name', 'lieu_de_naissance']):
        ids = group['id'].tolist()
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                graph[ids[i]].add(ids[j])
                graph[ids[j]].add(ids[i])

    # Ajouter les relations pour les doublons fuzzy
    for dup in fuzzy_duplicates:
        graph[dup['id1']].add(dup['id2'])
        graph[dup['id2']].add(dup['id1'])

    # Identifier les composantes connexes (groupes) - version itérative
    visited = set()
    groups = []

    for start_node in graph:
        if start_node not in visited:
            # Utiliser une pile pour simuler la récursion
            stack = [start_node]
            group = set()

            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    group.add(node)

                    # Ajouter tous les voisins non visités à la pile
                    for neighbor in graph[node]:
                        if neighbor not in visited:
                            stack.append(neighbor)

            if len(group) > 1:  # Ignorer les singletons
                groups.append(group)

    # Trouver les enregistrements qui ne font partie d'aucun groupe
    all_grouped_ids = set().union(*groups) if groups else set()
    singles = [id for id in df['id'] if id not in all_grouped_ids]

    # Créer un DataFrame avec les informations des groupes
    group_data = []

    # Ajouter les groupes de doublons
    for i, group in enumerate(groups):
        for id in group:
            row = df[df['id'] == id].iloc[0]
            group_data.append({
                'group_id': i+1,
                'id': id,
                'nom_prenom': row['nom_prenom'],
                'date_de_naissance': row['date_de_naissance'],
                'lieu_de_naissance': row['lieu_de_naissance'],
                'type_piece_identite': row['type_piece_identite'],
                'numero_piece_identite': row['numero_piece_identite'],
                'is_duplicate': True,
                'in_group_size': len(group)
            })

    # Ajouter les enregistrements uniques
    for id in singles:
        row = df[df['id'] == id].iloc[0]
        group_data.append({
            'group_id': None,
            'id': id,
            'nom_prenom': row['nom_prenom'],
            'date_de_naissance': row['date_de_naissance'],
            'lieu_de_naissance': row['lieu_de_naissance'],
            'type_piece_identite': row['type_piece_identite'],
            'numero_piece_identite': row['numero_piece_identite'],
            'is_duplicate': False,
            'in_group_size': 1
        })

    # Convertir en DataFrame
    grouped_df = pd.DataFrame(group_data)

    # Identifier les "représentants" de chaque groupe (pour compter les clients uniques)
    grouped_df['is_representative'] = False

    for group_id in grouped_df['group_id'].dropna().unique():
        group = grouped_df[grouped_df['group_id'] == group_id]
        # Choisir l'enregistrement le plus complet comme représentant
        most_complete_idx = group.notna().sum(axis=1).idxmax()
        grouped_df.loc[most_complete_idx, 'is_representative'] = True

    # Marquer tous les singles comme représentants
    grouped_df.loc[grouped_df['group_id'].isna(), 'is_representative'] = True

    return grouped_df

def generate_html_dashboard(df, exact_duplicates, fuzzy_duplicates, grouped_df, stats):
    """Génère un dashboard HTML avec les résultats de l'analyse."""
    # Utiliser un template HTML simple
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analyse des doublons - Client EUMM</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ padding: 20px; }}
            .section {{ margin-bottom: 30px; }}
            .card {{ margin-bottom: 20px; }}
            table {{ width: 100%; }}
            th, td {{ padding: 8px; text-align: left; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="my-4">Analyse des doublons - Table client_eumm</h1>
            <p class="text-muted">Rapport généré le {date}</p>
            
            <div class="row section">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3>Statistiques des doublons fuzzy</h3>
                        </div>
                        <div class="card-body">
                            <table class="table">
                                <tr><th>Nombre total de doublons fuzzy</th><td>{fuzzy_count}</td></tr>
                                <tr><th>Similarité moyenne</th><td>{avg_similarity:.2f}</td></tr>
                                <tr><th>Similarité minimale</th><td>{min_similarity:.2f}</td></tr>
                                <tr><th>Similarité maximale</th><td>{max_similarity:.2f}</td></tr>
                                <tr><th>Similarité médiane</th><td>{median_similarity:.2f}</td></tr>
                                <tr><th>Correspondances de date de naissance</th><td>{dob_matches} ({percent_dob_match:.1f}%)</td></tr>
                                <tr><th>Correspondances de lieu</th><td>{lieu_matches} ({percent_lieu_match:.1f}%)</td></tr>
                                <tr><th>Correspondances date et lieu</th><td>{dob_lieu_matches}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3>Distribution des similarités</h3>
                        </div>
                        <div class="card-body">
                            <canvas id="similarityChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row section">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3>Vue d'ensemble des doublons</h3>
                        </div>
                        <div class="card-body">
                            <table class="table">
                                <tr><th>Nombre total d'enregistrements</th><td>{total_records}</td></tr>
                                <tr><th>Doublons de pièce d'identité</th><td>{piece_count}</td></tr>
                                <tr><th>Doublons de nom et date de naissance</th><td>{name_dob_count}</td></tr>
                                <tr><th>Doublons de nom et lieu de naissance</th><td>{name_lieu_count}</td></tr>
                                <tr><th>Clients uniques estimés</th><td>{unique_customers}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h3>Répartition des doublons</h3>
                        </div>
                        <div class="card-body">
                            <canvas id="duplicatesChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Doublons potentiels (noms similaires) ({fuzzy_count})</h2>
                <div class="card">
                    <div class="card-body">
                        <div style="max-height: 400px; overflow-y: auto;">
                            {fuzzy_table}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Doublons exacts</h2>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Doublons de pièce d'identité ({piece_count})</h3>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 400px; overflow-y: auto;">
                            {piece_table}
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Doublons de nom et date de naissance ({name_dob_count})</h3>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 400px; overflow-y: auto;">
                            {name_dob_table}
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h3>Doublons de nom et lieu de naissance ({name_lieu_count})</h3>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 400px; overflow-y: auto;">
                            {name_lieu_table}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Graphique de la distribution des similarités
            const ctxSim = document.getElementById('similarityChart').getContext('2d');
            const similarityChart = new Chart(ctxSim, {{
                type: 'bar',
                data: {{
                    labels: ['0.7-0.8', '0.8-0.9', '0.9-1.0'],
                    datasets: [{{
                        label: 'Nombre de doublons',
                        data: [{sim_dist_low}, {sim_dist_mid}, {sim_dist_high}],
                        backgroundColor: [
                            'rgba(255, 159, 64, 0.7)',
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Nombre de doublons'
                            }}
                        }},
                        x: {{
                            title: {{
                                display: true,
                                text: 'Indice de similarité'
                            }}
                        }}
                    }}
                }}
            }});
            
            // Graphique des doublons
            const ctx = document.getElementById('duplicatesChart').getContext('2d');
            const duplicatesChart = new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: ['Clients uniques', 'Doublons de pièce', 'Doublons nom/date naiss.', 'Doublons nom/lieu', 'Doublons fuzzy'],
                    datasets: [{{
                        data: [{unique}, {piece_count}, {name_dob_count}, {name_lieu_count}, {fuzzy_count}],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(153, 102, 255, 0.7)'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'right'
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    # Préparer les tables HTML
    def create_table(df, columns):
        if len(df) == 0:
            return "<p>Aucun doublon trouvé.</p>"

        table_html = "<table class='table table-striped'><thead><tr>"
        for col in columns:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead><tbody>"

        for _, row in df.head(100).iterrows():  # Limiter à 100 lignes
            table_html += "<tr>"
            for col in columns:
                value = row[col]
                if pd.isna(value):
                    value = ""
                elif isinstance(value, pd.Timestamp):
                    value = value.strftime('%Y-%m-%d')
                table_html += f"<td>{value}</td>"
            table_html += "</tr>"

        if len(df) > 100:
            table_html += f"<tr><td colspan='{len(columns)}'>... et {len(df) - 100} autres enregistrements</td></tr>"

        table_html += "</tbody></table>"
        return table_html

    # Créer un DataFrame à partir des doublons fuzzy
    fuzzy_df = pd.DataFrame(fuzzy_duplicates) if fuzzy_duplicates else pd.DataFrame()

    # Générer les tables HTML
    piece_table = create_table(
        exact_duplicates['piece_identite'],
        ['id', 'nom_prenom', 'date_de_naissance', 'numero_piece_identite', 'type_piece_identite']
    )

    name_dob_table = create_table(
        exact_duplicates['name_dob'],
        ['id', 'nom_prenom', 'date_de_naissance', 'lieu_de_naissance', 'numero_piece_identite']
    )

    name_lieu_table = create_table(
        exact_duplicates['name_lieu'],
        ['id', 'nom_prenom', 'lieu_de_naissance', 'date_de_naissance', 'numero_piece_identite']
    )

    fuzzy_table = "<table class='table table-striped'><thead><tr><th>ID 1</th><th>Nom 1</th><th>ID 2</th><th>Nom 2</th><th>Similarité</th><th>Date naiss.</th><th>Lieu naiss.</th></tr></thead><tbody>"

    if not fuzzy_df.empty:
        for _, row in fuzzy_df.head(100).iterrows():
            fuzzy_table += f"<tr><td>{row['id1']}</td><td>{row['name1']}</td><td>{row['id2']}</td><td>{row['name2']}</td><td>{row['similarity']:.2f}</td><td>{'✓' if row['dob_match'] else '✗'}</td><td>{'✓' if row['lieu_match'] else '✗'}</td></tr>"

        if len(fuzzy_df) > 100:
            fuzzy_table += f"<tr><td colspan='7'>... et {len(fuzzy_df) - 100} autres enregistrements</td></tr>"
    else:
        fuzzy_table += "<tr><td colspan='7'>Aucun doublon potentiel trouvé</td></tr>"

    fuzzy_table += "</tbody></table>"

    # Nombre de clients uniques
    unique_customers = grouped_df['is_representative'].sum()

    # Extraire les statistiques fuzzy
    fuzzy_stats = stats['fuzzy_stats']

    # Remplir le template
    html_content = html_template.format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_records=stats['total_records'],
        unique_customers=unique_customers,
        piece_count=len(exact_duplicates['piece_identite']),
        name_dob_count=len(exact_duplicates['name_dob']),
        name_lieu_count=len(exact_duplicates['name_lieu']),
        fuzzy_count=len(fuzzy_duplicates),
        avg_similarity=fuzzy_stats['avg_similarity'],
        min_similarity=fuzzy_stats['min_similarity'],
        max_similarity=fuzzy_stats['max_similarity'],
        median_similarity=fuzzy_stats['median_similarity'],
        dob_matches=fuzzy_stats['dob_matches'],
        lieu_matches=fuzzy_stats['lieu_matches'],
        dob_lieu_matches=fuzzy_stats['dob_and_lieu_matches'],
        percent_dob_match=fuzzy_stats['percent_with_dob_match'],
        percent_lieu_match=fuzzy_stats['percent_with_lieu_match'],
        sim_dist_low=fuzzy_stats['similarity_distribution']['0.7-0.8'],
        sim_dist_mid=fuzzy_stats['similarity_distribution']['0.8-0.9'],
        sim_dist_high=fuzzy_stats['similarity_distribution']['0.9-1.0'],
        unique=unique_customers,
        piece_table=piece_table,
        name_dob_table=name_dob_table,
        name_lieu_table=name_lieu_table,
        fuzzy_table=fuzzy_table
    )

    return html_content

def export_to_excel(exact_duplicates, fuzzy_duplicates, grouped_df, stats):
    """
    Exporte les résultats au format Excel.

    Args:
        exact_duplicates: Dictionnaire avec les doublons exacts
        fuzzy_duplicates: Liste des doublons fuzzy
        grouped_df: DataFrame avec les groupes de clients
        stats: Statistiques générales

    Returns:
        Nom du fichier Excel généré
    """
    wb = Workbook()

    # Feuille de résumé
    ws_summary = wb.active
    ws_summary.title = "Résumé"

    # En-tête
    ws_summary.append(["Analyse des doublons - Table client_eumm"])
    ws_summary.append(["Rapport généré le", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    ws_summary.append([])

    # Statistiques générales
    ws_summary.append(["Statistiques générales"])
    ws_summary.append(["Nombre total d'enregistrements", stats['total_records']])
    ws_summary.append(["Doublons de pièce d'identité", stats['exact_duplicates']['piece_identite']])
    ws_summary.append(["Doublons de nom et date de naissance", stats['exact_duplicates']['name_dob']])
    ws_summary.append(["Doublons de nom et lieu de naissance", stats['exact_duplicates']['name_lieu']])
    ws_summary.append(["Clients uniques identifiés", grouped_df['is_representative'].sum()])
    ws_summary.append([])

    # Détails sur les doublons fuzzy
    ws_summary.append(["Statistiques des doublons fuzzy"])
    ws_summary.append(["Nombre total de doublons fuzzy", stats['fuzzy_duplicates']])

    if stats['fuzzy_duplicates'] > 0:
        fuzzy_stats = stats['fuzzy_stats']
        ws_summary.append(["Similarité moyenne", f"{fuzzy_stats['avg_similarity']:.2f}"])
        ws_summary.append(["Similarité minimale", f"{fuzzy_stats['min_similarity']:.2f}"])
        ws_summary.append(["Similarité maximale", f"{fuzzy_stats['max_similarity']:.2f}"])
        ws_summary.append(["Similarité médiane", f"{fuzzy_stats['median_similarity']:.2f}"])
        ws_summary.append(["Distribution des similarités 0.7-0.8", fuzzy_stats['similarity_distribution']['0.7-0.8']])
        ws_summary.append(["Distribution des similarités 0.8-0.9", fuzzy_stats['similarity_distribution']['0.8-0.9']])
        ws_summary.append(["Distribution des similarités 0.9-1.0", fuzzy_stats['similarity_distribution']['0.9-1.0']])
        ws_summary.append(["Correspondances de date de naissance", fuzzy_stats['dob_matches']])
        ws_summary.append(["Correspondances de lieu de naissance", fuzzy_stats['lieu_matches']])
        ws_summary.append(["Correspondances date et lieu de naissance", fuzzy_stats['dob_and_lieu_matches']])
        ws_summary.append(["Pourcentage avec correspondance date", f"{fuzzy_stats['percent_with_dob_match']:.1f}%"])
        ws_summary.append(["Pourcentage avec correspondance lieu", f"{fuzzy_stats['percent_with_lieu_match']:.1f}%"])

    # Style pour les en-têtes
    header_font = Font(bold=True)
    for cell in ws_summary["1:1"]:
        cell.font = header_font
    for row_idx in [4, 16]:  # Indices des lignes d'en-tête
        for cell in ws_summary[row_idx:row_idx]:
            cell.font = header_font

    # Feuille des doublons pièce d'identité
    if len(exact_duplicates['piece_identite']) > 0:
        ws_piece = wb.create_sheet("Doublons Pièce Identité")
        columns = ['id', 'nom_prenom', 'date_de_naissance', 'numero_piece_identite', 'type_piece_identite', 'lieu_de_naissance']
        ws_piece.append(columns)

        for idx, row in exact_duplicates['piece_identite'].reset_index(drop=True).iterrows():
            ws_piece.append([row[col] if not pd.isna(row[col]) else "" for col in columns])

    # Feuille des doublons nom+dob
    if len(exact_duplicates['name_dob']) > 0:
        ws_name_dob = wb.create_sheet("Doublons Nom+DoB")
        columns = ['id', 'nom_prenom', 'date_de_naissance', 'lieu_de_naissance', 'numero_piece_identite', 'type_piece_identite']
        ws_name_dob.append(columns)

        for idx, row in exact_duplicates['name_dob'].reset_index(drop=True).iterrows():
            ws_name_dob.append([row[col] if not pd.isna(row[col]) else "" for col in columns])

    # Feuille des doublons nom+lieu
    if len(exact_duplicates['name_lieu']) > 0:
        ws_name_lieu = wb.create_sheet("Doublons Nom+Lieu")
        columns = ['id', 'nom_prenom', 'lieu_de_naissance', 'date_de_naissance', 'numero_piece_identite', 'type_piece_identite']
        ws_name_lieu.append(columns)

        for idx, row in exact_duplicates['name_lieu'].reset_index(drop=True).iterrows():
            ws_name_lieu.append([row[col] if not pd.isna(row[col]) else "" for col in columns])

    # Feuille des doublons fuzzy
    if len(fuzzy_duplicates) > 0:
        ws_fuzzy = wb.create_sheet("Doublons Similaires")

        columns = ['id1', 'name1', 'id2', 'name2', 'similarity', 'dob_match', 'lieu_match']
        ws_fuzzy.append(columns)

        fuzzy_df = pd.DataFrame(fuzzy_duplicates)
        for idx, row in fuzzy_df.iterrows():
            ws_fuzzy.append([row[col] if not pd.isna(row[col]) else "" for col in columns])

    # Feuille des clients uniques (représentants)
    ws_unique = wb.create_sheet("Clients Uniques")

    # En-têtes
    unique_columns = ['id', 'nom_prenom', 'date_de_naissance', 'lieu_de_naissance', 'numero_piece_identite', 'type_piece_identite', 'group_id', 'in_group_size']
    ws_unique.append(unique_columns)

    # Données
    unique_clients = grouped_df[grouped_df['is_representative']]
    for idx, row in unique_clients.reset_index(drop=True).iterrows():
        ws_unique.append([row[col] if not pd.isna(row[col]) else "" for col in unique_columns])

    # Feuille des groupes de doublons
    ws_groups = wb.create_sheet("Groupes de Doublons")

    # En-têtes
    group_columns = ['group_id', 'id', 'nom_prenom', 'date_de_naissance', 'lieu_de_naissance', 'numero_piece_identite', 'type_piece_identite', 'is_representative']
    ws_groups.append(group_columns)

    # Données - seulement pour les groupes avec plus d'un membre
    has_groups = grouped_df[~grouped_df['group_id'].isna()]
    for idx, row in has_groups.reset_index(drop=True).iterrows():
        ws_groups.append([row[col] if not pd.isna(row[col]) else "" for col in group_columns])

    # Enregistrer le fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"client_eumm_duplicates_{timestamp}.xlsx"
    wb.save(filename)

    return filename

def export_to_csv(exact_duplicates, fuzzy_duplicates, grouped_df, output_dir="exports"):
    """Exporte les résultats au format CSV."""
    # Créer le répertoire si nécessaire
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filenames = {}

    # Exporter les doublons de pièce d'identité
    if len(exact_duplicates['piece_identite']) > 0:
        filename = f"{output_dir}/doublons_piece_identite_{timestamp}.csv"
        exact_duplicates['piece_identite'].to_csv(filename, index=False)
        filenames['piece_identite'] = filename

    # Exporter les doublons de nom+dob
    if len(exact_duplicates['name_dob']) > 0:
        filename = f"{output_dir}/doublons_nom_dob_{timestamp}.csv"
        exact_duplicates['name_dob'].to_csv(filename, index=False)
        filenames['nom_dob'] = filename

    # Exporter les doublons de nom+lieu
    if len(exact_duplicates['name_lieu']) > 0:
        filename = f"{output_dir}/doublons_nom_lieu_{timestamp}.csv"
        exact_duplicates['name_lieu'].to_csv(filename, index=False)
        filenames['nom_lieu'] = filename

    # Exporter les doublons fuzzy
    if len(fuzzy_duplicates) > 0:
        filename = f"{output_dir}/doublons_similaires_{timestamp}.csv"
        fuzzy_df = pd.DataFrame(fuzzy_duplicates)
        fuzzy_df.to_csv(filename, index=False)
        filenames['similaires'] = filename

    # Exporter les clients uniques (représentants)
    filename = f"{output_dir}/clients_uniques_{timestamp}.csv"
    unique_clients = grouped_df[grouped_df['is_representative']]
    unique_clients.to_csv(filename, index=False)
    filenames['uniques'] = filename

    # Exporter tous les groupes
    filename = f"{output_dir}/tous_groupes_{timestamp}.csv"
    grouped_df.to_csv(filename, index=False)
    filenames['groupes'] = filename

    return filenames

def main():
    """Fonction principale du programme."""
    debut = time.time()
    print("Récupération des données...")
    df = fetch_data()

    if df is None:
        print("Impossible de continuer sans données.")
        return

    print(f"Données récupérées: {len(df)} enregistrements.")

    # Préparation des données
    df = prepare_data(df)

    # Recherche des doublons exacts
    print("Recherche des doublons exacts...")
    exact_duplicates = find_exact_duplicates(df)

    # Recherche des doublons fuzzy
    print("Recherche des doublons avec noms similaires...")
    fuzzy_duplicates = find_fuzzy_name_duplicates(df)

    # Grouper les doublons pour identifier les clients uniques
    print("Groupement des doublons et identification des clients uniques...")
    grouped_df = group_duplicates(df, exact_duplicates, fuzzy_duplicates)

    # Générer les statistiques
    print("Génération des statistiques...")
    stats = generate_summary_stats(df, exact_duplicates, fuzzy_duplicates)

    # Export Excel
    print("Export des données au format Excel...")
    excel_file = export_to_excel(exact_duplicates, fuzzy_duplicates, grouped_df, stats)
    print(f"Données exportées dans '{excel_file}'")

    # Export CSV
    print("Export des données au format CSV...")
    csv_files = export_to_csv(exact_duplicates, fuzzy_duplicates, grouped_df)
    print("Fichiers CSV exportés:")
    for key, filename in csv_files.items():
        print(f"- {key}: {filename}")

    # Créer le dashboard HTML
    print("Création du dashboard HTML...")
    html_content = generate_html_dashboard(df, exact_duplicates, fuzzy_duplicates, grouped_df, stats)

    # Enregistrer le dashboard
    html_file = "client_eumm_duplicates_dashboard.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nDashboard enregistré dans '{html_file}'")

    # Afficher des statistiques
    print("\nStatistiques générales:")
    print(f"Nombre total d'enregistrements: {stats['total_records']}")
    print(f"Doublons de pièce d'identité: {stats['exact_duplicates']['piece_identite']}")
    print(f"Doublons de nom et date de naissance: {stats['exact_duplicates']['name_dob']}")
    print(f"Doublons de nom et lieu de naissance: {stats['exact_duplicates']['name_lieu']}")
    print(f"Doublons potentiels (noms similaires): {stats['fuzzy_duplicates']}")

    if stats['fuzzy_duplicates'] > 0:
        print("\nStatistiques des doublons fuzzy:")
        print(f"Similarité moyenne: {stats['fuzzy_stats']['avg_similarity']:.2f}")
        print(f"Correspondances de date de naissance: {stats['fuzzy_stats']['dob_matches']} ({stats['fuzzy_stats']['percent_with_dob_match']:.1f}%)")
        print(f"Correspondances de lieu de naissance: {stats['fuzzy_stats']['lieu_matches']} ({stats['fuzzy_stats']['percent_with_lieu_match']:.1f}%)")

    print(f"Clients uniques identifiés: {grouped_df['is_representative'].sum()}")

    fin = time.time()
    duree = fin - debut
    print(f"\nTemps d'exécution: {duree:.2f} secondes ({duree/60:.2f} minutes)")

if __name__ == "__main__":
    main()