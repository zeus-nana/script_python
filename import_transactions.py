import os
import pandas as pd
import psycopg2
from psycopg2 import Error
from datetime import datetime
from pathlib import Path
import argparse
import time
import shutil  # Import the shutil module for moving files

class TransactionImporter:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.report_data = {
            'start_time': None,
            'end_time': None,
            'files_processed': [],
            'total_rows': 0,
            'successful_rows': 0,
            'failed_rows': 0,
            'errors': []
        }

    def check_transaction_exists(self, cur, service, reference):
        """Vérifie si une transaction existe déjà avec le même service et référence"""
        check_query = """
        SELECT EXISTS(
            SELECT 1
            FROM transactions
            WHERE service = %s AND reference = %s
        )
        """
        cur.execute(check_query, (service, reference))
        return cur.fetchone()[0]

    def import_transactions(self):
        """Importe les transactions depuis les fichiers CSV vers la base de données"""
        db_params = {
            'dbname': 'db_hswa',
            'user': 'postgres',
            'password': 'trinita',
            'host': 'localhost',
            'port': '5432'
        }

        self.report_data['start_time'] = datetime.now()
        conn = None

        try:
            conn = psycopg2.connect(**db_params)
            cur = conn.cursor()
            print("Connexion à la base de données établie.")

            folder_path = Path.home() / 'documents' / 'etats_bruts'
            logs_folder = folder_path / 'logs'  # Define logs folder
            processed_folder = folder_path / 'fichiers_traités' # Define processed folder

            # Create logs and fichiers_traités directories if they don't exist
            logs_folder.mkdir(parents=True, exist_ok=True)
            processed_folder.mkdir(parents=True, exist_ok=True)

            csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

            for csv_file in csv_files:
                file_data = {
                    'filename': csv_file,
                    'rows_processed': 0,
                    'rows_success': 0,
                    'rows_failed': 0,
                    'errors': []
                }

                file_path = folder_path / csv_file
                print(f"Traitement du fichier: {csv_file}")

                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                    if '#' in df.columns:
                        df = df.drop('#', axis=1)

                    file_data['rows_processed'] = len(df)
                    self.report_data['total_rows'] += len(df)

                    # Traitement ligne par ligne avec transaction individuelle
                    for index, row in df.iterrows():
                        try:
                            # Vérification préalable de l'existence
                            service = row.get('Service')
                            reference = row.get('Reférence')

                            # Si la transaction existe déjà, on l'ignore
                            if self.check_transaction_exists(cur, service, reference):
                                raise ValueError(f"L'opération {service} de référence {reference} existe déjà")

                            insert_query = """
                            INSERT INTO transactions (
                                guichet, agence, compagnie, groupe, service, reference,
                                ref_partenaire, id_trx_partenaire, reference_eg, expediteur,
                                beneficiaire, id_proof_benef, source, destination, devise_source,
                                numero_compte, intitule_compte, com_gui_envoyeur, com_age_envoyeur,
                                com_cmp_envoyeur, com_grp_envoyeur, com_grp_envoyeur_dev,
                                com_sys_envoie, com_sys_envoie_dev, montant, frais_ht, tva,
                                autres_taxes, frais_ttc, total, devise_destination,
                                montant_a_percevoir, date_transaction, date_paiement,
                                date_annulation, date_remboursement, date_derniere_modification,
                                statut, guichet_payeur, agence_payeur, compagnie_payeur,
                                groupe_payeur, com_gui_payeur, com_age_payeur, com_cmp_payeur,
                                com_grp_payeur, com_grp_payeur_dev, com_sys_paiement,
                                com_sys_paiement_dev, autres_taxe_p, remise, guichetier,
                                guichetier_payeur, tec, commission_partenaire, tec_partenaire,
                                status_partenaire
                            ) VALUES %s
                            """

                            values = self.prepare_values(row)
                            formatted_values = '(' + ','.join(['%s'] * len(values)) + ')'

                            if not self.test_mode:
                                cur.execute(insert_query % formatted_values, values)
                                conn.commit()  # Commit après chaque insertion réussie

                            file_data['rows_success'] += 1
                            self.report_data['successful_rows'] += 1

                        except ValueError as ve:
                            # Erreur de doublon détectée lors de la vérification
                            file_data['rows_failed'] += 1
                            self.report_data['failed_rows'] += 1
                            error_info = {
                                'row': index + 2,
                                'message': str(ve),
                                'is_duplicate': True # Mark as duplicate error
                            }
                            file_data['errors'].append(error_info)

                        except Exception as row_error:
                            # Autres erreurs
                            file_data['rows_failed'] += 1
                            self.report_data['failed_rows'] += 1
                            error_info = {
                                'row': index + 2,
                                'message': str(row_error),
                                'is_duplicate': False # Mark as not duplicate error
                            }
                            file_data['errors'].append(error_info)
                            if not self.test_mode:
                                conn.rollback()  # Rollback en cas d'erreur

                    print(f"Traitement terminé pour {csv_file}")
                    # Move file if no *critical* errors (excluding duplicates)
                    has_critical_errors = any(not error.get('is_duplicate', False) for error in file_data['errors'])
                    if not has_critical_errors:
                        processed_file_path = processed_folder / csv_file
                        # Add suffix to processed filename
                        file_name, file_ext = os.path.splitext(csv_file)
                        suffixed_file_name = f"{file_name}_traité{file_ext}"
                        processed_file_path_suffixed = processed_folder / suffixed_file_name

                        source_path_str = str(file_path) # Ensure path is string for shutil.move
                        destination_path_str = str(processed_file_path_suffixed) # Use suffixed path for moving

                        try:
                            shutil.move(source_path_str, destination_path_str)
                            print(f"Fichier déplacé vers: {destination_path_str}")
                        except Exception as e:
                            file_data['errors'].append({'row': 'File Move', 'message': f"Erreur lors du déplacement du fichier vers {destination_path_str}: {str(e)}", 'is_duplicate': False})
                            print(f"Erreur lors du déplacement du fichier vers {destination_path_str}: {e}")
                    else:
                        print(f"Fichier non déplacé en raison d'erreurs critiques lors du traitement.")


                except Exception as file_error:
                    self.report_data['errors'].append(f"Erreur sur le fichier {csv_file}: {str(file_error)}")

                self.report_data['files_processed'].append(file_data)

        except Error as e:
            self.report_data['errors'].append(f"Erreur de connexion PostgreSQL: {str(e)}")

        finally:
            if conn:
                cur.close()
                conn.close()
                print("Connexion à la base de données fermée.")

            self.report_data['end_time'] = datetime.now()
            report_path = self.generate_report()
            print(f"Rapport d'importation généré: {report_path}")

    def prepare_values(self, row):
        """Prépare et convertit les valeurs pour l'insertion"""
        def convert_numeric(value):
            if pd.isna(value):
                return None
            if isinstance(value, str):
                value = value.replace(',', '.')
            try:
                return float(value)
            except ValueError:
                return None

        def convert_status_partenaire(status_str):
            """Convertit le statut partenaire en numérique (si possible)."""
            status_mapping = {
                "CONFIRMED": "CONFIRMED",
                "CREATED": "CREATED",
                "Annulé": "Annulé"
            }
            return status_mapping.get(status_str, status_str) # return original if not found

        return (
            row.get('Guichet'), row.get('Agence'),
            row.get('Compagnie'), row.get('Groupe'), row.get('Service'),
            row.get('Reférence'), row.get('Ref Partenaire'),
            row.get('ID Trx Partenaire'), row.get('Référence EG'),
            row.get('Expéditeur'), row.get('Bénéficiaire'),
            row.get('IdProofBenef'), row.get('Src.'), row.get('Dest.'),
            row.get('Dev. Src'), row.get('Numéro Compte'),
            row.get('Intitulé Compte'), convert_numeric(row.get('Com_Gui_Envoyeur')),
            convert_numeric(row.get('Com_Age_Envoyeur')), convert_numeric(row.get('Com_Cmp_Envoyeur')),
            convert_numeric(row.get('Com_Grp_Envoyeur')), convert_numeric(row.get('Com_Grp_Envoyeur_Dev')),
            convert_numeric(row.get('Com_Sys_Envoie')), convert_numeric(row.get('Com_Sys_Envoie_Dev')),
            convert_numeric(row.get('Montant')), convert_numeric(row.get('Frais HT')), convert_numeric(row.get('TVA')),
            convert_numeric(row.get('Autres taxes')), convert_numeric(row.get('Frais TTC')), convert_numeric(row.get('Total')),
            row.get('Dev. Dest'), convert_numeric(row.get('Montant à percevoir')),
            self.convert_date(row.get('Date')),
            self.convert_date(row.get('Date Paiement')),
            self.convert_date(row.get('Date Annulation')),
            self.convert_date(row.get('Date Remboursement')),
            self.convert_date(row.get('Date Dernière Modification')),
            row.get('Statut'), row.get('Guichet Payeur'),
            row.get('Agence Payeur'), row.get('Compagnie Payeur'),
            row.get('Groupe Payeur'), convert_numeric(row.get('Com_Gui_Payeur')),
            convert_numeric(row.get('Com_Age_Payeur')), convert_numeric(row.get('Com_Cmp_Payeur')),
            convert_numeric(row.get('Com_Grp_Payeur')), convert_numeric(row.get('Com_Grp_Payeur_Dev')),
            convert_numeric(row.get('Com_Sys_Paiement')), convert_numeric(row.get('Com_Sys_Paiement_Dev')),
            convert_numeric(row.get('Autres Taxe P')), convert_numeric(row.get('Remise')),
            row.get('Guichetier'), row.get('Guichetier Payeur'),
            convert_numeric(row.get('TEC')), convert_numeric(row.get('Commission Partenaire')),
            convert_numeric(row.get('TEC Partenaire')), convert_status_partenaire(row.get('Status Partenaire')) # Apply conversion here
        )

    @staticmethod
    def convert_date(date_str):
        """Convertit une chaîne de date en objet datetime"""
        if pd.isna(date_str):
            return None

        date_formats = [
            '%d-%m-%Y %H:%M:%S',  # Format principal
            '%Y-%m-%d %H:%M:%S',  # Format alternatif
            '%d/%m/%Y %H:%M'      # Autre format possible
        ]

        for date_format in date_formats:
            try:
                return datetime.strptime(str(date_str), date_format)
            except ValueError:
                continue

        return None

    def generate_report(self):
        """Génère un rapport détaillé de l'importation"""
        folder_path = Path.home() / 'documents' / 'etats_bruts'
        logs_folder = folder_path / 'logs'  # Define logs folder
        report_path = logs_folder / f'import_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt' # Save report in logs folder

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT D'IMPORTATION DES TRANSACTIONS ===\n\n")
            f.write(f"Date d'exécution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode test: {'Oui' if self.test_mode else 'Non'}\n")

            if self.report_data['start_time'] and self.report_data['end_time']:
                duration = (self.report_data['end_time'] - self.report_data['start_time']).total_seconds()
                f.write(f"Durée totale: {duration:.2f} secondes\n\n")

            f.write("=== RÉSUMÉ ===\n")
            f.write(f"Total fichiers traités: {len(self.report_data['files_processed'])}\n")
            f.write(f"Total lignes traitées: {self.report_data['total_rows']}\n")
            f.write(f"Lignes réussies: {self.report_data['successful_rows']}\n")
            f.write(f"Lignes échouées: {self.report_data['failed_rows']}\n\n")

            f.write("=== DÉTAIL PAR FICHIER ===\n")
            for file_data in self.report_data['files_processed']:
                f.write(f"\nFichier: {file_data['filename']}\n")
                f.write(f"  Lignes traitées: {file_data['rows_processed']}\n")
                f.write(f"  Lignes réussies: {file_data['rows_success']}\n")
                f.write(f"  Lignes échouées: {file_data['rows_failed']}\n")
                if file_data['errors']:
                    f.write("  Erreurs rencontrées:\n")
                    for error in file_data['errors']:
                        f.write(f"    - Ligne {error['row']}: {error['message']}")
                        if error.get('is_duplicate', False):
                            f.write(" (Doublon)") # Indicate duplicate error in report
                        f.write('\n')

            if self.report_data['errors']:
                f.write("\n=== ERREURS GLOBALES ===\n")
                for error in self.report_data['errors']:
                    if not error.get('is_duplicate', False) : # Only show global errors that are not duplicates
                        f.write(f"- {error}\n")

        return report_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import de transactions avec mode test optionnel')
    parser.add_argument('--test', action='store_true', help='Exécuter en mode test sans faire d\'insertions')
    args = parser.parse_args()

    importer = TransactionImporter(test_mode=args.test)
    importer.import_transactions()