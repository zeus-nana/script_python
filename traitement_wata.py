import pandas as pd
import numpy as np
from datetime import datetime
import os

def process_transactions(csv_path):
    df = pd.read_csv(csv_path, encoding='utf-8')
    output_dir = os.path.dirname(csv_path)
    output_path = os.path.join(output_dir, 'arret_journee_' + datetime.now().strftime('%Y%m%d%H%M%S') + '.xlsx')

    writer = pd.ExcelWriter(output_path, engine='xlsxwriter')

    # EMI-PPHOP
    emi_df = df[df['Groupe'] == 'GROUPE EMI MONEY SARL']

    emi_envois = pd.to_numeric(emi_df[
                                   (emi_df['Service'].str.contains('ENVOI', na=False)) &
                                   (emi_df['Statut'] != 'Annulé')
                                   ]['Montant'], errors='coerce').sum()

    emi_paiements = pd.to_numeric(emi_df[
                                      emi_df['Service'].str.contains('PAIEMENT', na=False)
                                  ]['Montant à percevoir'], errors='coerce').sum()

    # NETX
    netx_countries = ['TOGO', 'MALI', 'NIGER', 'BURKINA-FASO', 'SENEGAL', 'GUINEE', 'CIV']
    netx_results = []

    for pays in netx_countries:
        pays_df = df[df['Compagnie'].str.contains(pays, na=False, case=False)]
        pays_envois = pd.to_numeric(pays_df[
                                        (pays_df['Service'].str.contains('ENVOI', na=False)) &
                                        (pays_df['Statut'] != 'Annulé') &
                                        (pays_df['Groupe'] == 'GROUPE GT BANK')
                                        ]['Montant'], errors='coerce').sum()

        pays_paiements = pd.to_numeric(pays_df[
                                           (pays_df['Service'].str.contains('PAIEMENT', na=False)) &
                                           (pays_df['Groupe'] == 'GROUPE GT BANK')
                                           ]['Montant à percevoir'], errors='coerce').sum()

        netx_results.append({
            'Pays': pays,
            'Envois': pays_envois,
            'Paiements': pays_paiements
        })

    # THUNES
    thunes_df = df[df['Service'].str.contains('THUNES', na=False)]
    thunes_paiements = pd.to_numeric(thunes_df[thunes_df['Statut'] != 'Annulé']['Montant'], errors='coerce').sum() + \
                       pd.to_numeric(thunes_df[thunes_df['Statut'] != 'Annulé']['Commission Partenaire'], errors='coerce').sum()

    thunes_annulations = pd.to_numeric(thunes_df[thunes_df['Statut'] == 'Annulé']['Montant'], errors='coerce').sum() + \
                         pd.to_numeric(thunes_df[thunes_df['Statut'] == 'Annulé']['Commission Partenaire'], errors='coerce').sum()

    pd.DataFrame({
        'Type': ['Envois', 'Paiements'],
        'Montant': [emi_envois, emi_paiements]
    }).to_excel(writer, sheet_name='EMI-PPHOP', index=False)

    pd.DataFrame(netx_results).to_excel(writer, sheet_name='NETX', index=False)

    pd.DataFrame({
        'Type': ['Paiements', 'Annulations'],
        'Montant': [thunes_paiements, thunes_annulations]
    }).to_excel(writer, sheet_name='THUNES', index=False)

    writer.close()
    return output_path

output_file = process_transactions(r"d:/code/transactions0.csv")
print(f"Fichier créé : {output_file}")