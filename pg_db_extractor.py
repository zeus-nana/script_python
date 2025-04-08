#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Extracteur de base de données PostgreSQL
# Crée un fichier SQL pour recréer entièrement la base

# Configuration de la base de données - Modifie ces valeurs selon ta configuration
DB_HOST = 'localhost'      # Adresse du serveur PostgreSQL
DB_PORT = 5434             # Port du serveur PostgreSQL
DB_NAME = 'db_cera'        # Nom de la base de données
DB_USER = 'postgres'       # Nom d'utilisateur
DB_PASSWORD = 'trinita'   # Mot de passe
DB_SCHEMA = 'public'       # Schéma à extraire
OUTPUT_FILE = r"D:\code\080425\bakup_cera1.sql"         # None = nom_bdd_date.sql, ou spécifier un chemin

import psycopg2
import psycopg2.extras
import os
import argparse
from datetime import datetime

class PostgreSQLExtractor:
    def __init__(self, host, port, database, user, password, schema='public'):
        """Initialise la connexion à la base de données"""
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.schema = schema
        self.conn = None
        self.cursor = None

    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print(f"Connecté à la base de données {self.connection_params['database']}")
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            raise

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Connexion fermée")

    def get_schema_objects(self):
        """Retourne tous les objets du schéma dans l'ordre de dépendance"""
        objects = {
            'types': self.get_types(),
            'sequences': self.get_sequences(),
            'tables': self.get_tables(),
            'functions': self.get_functions(),
            'views': self.get_views(),
            'triggers': self.get_triggers(),
            'indexes': self.get_indexes(),
            'constraints': self.get_constraints()
        }
        return objects

    def get_types(self):
        """Retourne tous les types personnalisés"""
        query = """
        SELECT 
            pg_type.typname AS name,
            pg_type.typtype,
            CASE 
                WHEN pg_type.typtype = 'e' THEN
                    array_to_string(ARRAY(
                        SELECT enumlabel 
                        FROM pg_enum 
                        WHERE pg_enum.enumtypid = pg_type.oid
                        ORDER BY pg_enum.enumsortorder
                    ), ', ')
                ELSE NULL
            END AS enum_values
        FROM pg_type
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = pg_type.typnamespace
        WHERE (
            pg_type.typtype = 'e' OR  -- enum
            pg_type.typtype = 'c'     -- composite
        )
        AND n.nspname = %s
        ORDER BY pg_type.typname;
        """
        try:
            self.cursor.execute(query, (self.schema,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des types: {e}")
            return []

    def get_sequences(self):
        """Retourne toutes les séquences"""
        query = """
        SELECT
            s.relname as sequence_name,
            pg_get_serial_sequence(t.tablename, c.column_name) as seq_details
        FROM
            information_schema.columns c
        JOIN
            pg_class s ON s.relkind = 'S' AND s.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = %s)
        JOIN
            (SELECT table_name AS tablename, table_schema FROM information_schema.tables WHERE table_schema = %s) t
            ON c.table_name = t.tablename AND c.table_schema = t.table_schema
        WHERE
            c.column_default LIKE 'nextval%%'
        ORDER BY
            t.tablename, c.ordinal_position;
        """
        try:
            self.cursor.execute(query, (self.schema, self.schema))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des séquences: {e}")
            return []

    def get_tables(self):
        """Retourne toutes les tables avec leurs définitions"""
        # D'abord, récupérer les définitions de toutes les tables
        query = """
        SELECT 
            table_name,
            ARRAY(
                SELECT column_name || ' ' || data_type || 
                    CASE 
                        WHEN character_maximum_length IS NOT NULL THEN '(' || character_maximum_length || ')'
                        WHEN data_type = 'numeric' AND numeric_precision IS NOT NULL AND numeric_scale IS NOT NULL 
                            THEN '(' || numeric_precision || ',' || numeric_scale || ')'
                        ELSE ''
                    END ||
                    CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                    CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = information_schema.tables.table_name
                ORDER BY ordinal_position
            ) as columns
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """

        try:
            self.cursor.execute(query, (self.schema, self.schema))
            tables = self.cursor.fetchall()

            # Récupérer la liste de toutes les tables
            all_table_names = [table['table_name'] for table in tables]

            # Récupérer les dépendances et trier les tables
            dependencies = self.get_table_dependencies()
            sorted_tables = self.topological_sort(dependencies, all_table_names)

            # Réorganiser les tables selon l'ordre trié
            sorted_result = []
            for table_name in sorted_tables:
                for table in tables:
                    if table['table_name'] == table_name:
                        sorted_result.append(table)
                        break

            return sorted_result
        except Exception as e:
            print(f"Erreur lors de la récupération des tables: {e}")
            return []

    def get_functions(self):
        """Retourne toutes les fonctions"""
        query = """
        SELECT 
            p.proname AS function_name,
            pg_get_functiondef(p.oid) AS function_def
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = %s
        ORDER BY p.proname;
        """
        try:
            self.cursor.execute(query, (self.schema,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des fonctions: {e}")
            return []

    def get_views(self):
        """Retourne toutes les vues avec leurs définitions"""
        query = """
        SELECT 
            table_name AS view_name,
            pg_get_viewdef(quote_ident(table_schema) || '.' || quote_ident(table_name), true) AS view_definition
        FROM information_schema.views
        WHERE table_schema = %s
        ORDER BY table_name;
        """
        try:
            self.cursor.execute(query, (self.schema,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des vues: {e}")
            return []

    def get_triggers(self):
        """Retourne tous les triggers"""
        query = """
        SELECT
            trigger_name,
            event_manipulation,
            event_object_table,
            action_statement
        FROM information_schema.triggers
        WHERE trigger_schema = %s
        ORDER BY event_object_table, trigger_name;
        """
        try:
            self.cursor.execute(query, (self.schema,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des triggers: {e}")
            return []

    def get_indexes(self):
        """Retourne tous les index (excluant ceux des PK et FK)"""
        query = """
        SELECT
            tablename,
            indexname,
            indexdef
        FROM
            pg_indexes
        WHERE
            schemaname = %s
            AND indexname NOT IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = %s
                AND constraint_type IN ('PRIMARY KEY', 'UNIQUE', 'FOREIGN KEY')
            )
        ORDER BY
            tablename, indexname;
        """
        try:
            self.cursor.execute(query, (self.schema, self.schema))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des indexes: {e}")
            return []

    def get_table_dependencies(self):
        """Obtient un graphe de dépendances entre les tables basé sur les clés étrangères"""
        query = """
        SELECT
            tc.table_name AS table_name,
            ccu.table_name AS referenced_table
        FROM
            information_schema.table_constraints tc
        JOIN
            information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = %s
            AND ccu.table_schema = %s
            AND tc.table_name != ccu.table_name
        """

        try:
            self.cursor.execute(query, (self.schema, self.schema))
            dependencies = self.cursor.fetchall()

            # Créer un graphe de dépendances
            graph = {}
            for dep in dependencies:
                if dep['table_name'] not in graph:
                    graph[dep['table_name']] = []
                graph[dep['table_name']].append(dep['referenced_table'])

            return graph
        except Exception as e:
            print(f"Erreur lors de la récupération des dépendances: {e}")
            return {}

    def topological_sort(self, graph, all_tables):
        """Tri topologique des tables basé sur leurs dépendances"""
        # Initialiser tous les noeuds
        result = []
        visited = set()
        temp_mark = set()

        def visit(node):
            if node in temp_mark:
                # Détecter les cycles
                print(f"Attention: Cycle de dépendance détecté avec la table {node}")
                return
            if node not in visited:
                temp_mark.add(node)
                # Visiter d'abord les dépendances
                if node in graph:
                    for dep in graph[node]:
                        visit(dep)
                # Marquer comme visité et ajouter au résultat
                temp_mark.discard(node)
                visited.add(node)
                result.append(node)

        # Visiter toutes les tables
        for table in all_tables:
            if table not in visited:
                visit(table)

        return result

    def get_constraints(self):
        """Retourne toutes les contraintes (PK, FK, etc.)"""
        query = """
        SELECT
            tc.constraint_name,
            tc.table_name,
            tc.constraint_type,
            
            -- Pour les clés primaires et uniques
            CASE 
                WHEN tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE') THEN 
                    array_to_string(array_agg(kcu.column_name ORDER BY kcu.ordinal_position), ', ')
                ELSE NULL
            END AS pk_columns,
            
            -- Pour les clés étrangères
            CASE 
                WHEN tc.constraint_type = 'FOREIGN KEY' THEN 
                    array_to_string(array_agg(kcu.column_name ORDER BY kcu.ordinal_position), ', ')
                ELSE NULL
            END AS fk_columns,
            
            CASE 
                WHEN tc.constraint_type = 'FOREIGN KEY' THEN ccu.table_name
                ELSE NULL
            END AS ref_table,
            
            CASE 
                WHEN tc.constraint_type = 'FOREIGN KEY' THEN 
                    array_to_string(array_agg(ccu.column_name ORDER BY kcu.ordinal_position), ', ')
                ELSE NULL
            END AS ref_columns,
            
            rc.update_rule,
            rc.delete_rule
        FROM
            information_schema.table_constraints tc
        LEFT JOIN
            information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN
            information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        LEFT JOIN
            information_schema.referential_constraints rc
            ON tc.constraint_name = rc.constraint_name
            AND tc.table_schema = rc.constraint_schema
        WHERE
            tc.table_schema = %s
        GROUP BY
            tc.constraint_name,
            tc.table_name,
            tc.constraint_type,
            ccu.table_name,
            rc.update_rule,
            rc.delete_rule
        ORDER BY
            tc.table_name,
            CASE 
                WHEN tc.constraint_type = 'PRIMARY KEY' THEN 1
                WHEN tc.constraint_type = 'UNIQUE' THEN 2
                WHEN tc.constraint_type = 'FOREIGN KEY' THEN 3
                ELSE 4
            END;
        """
        try:
            self.cursor.execute(query, (self.schema,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Erreur lors de la récupération des contraintes: {e}")
            return []

    def get_table_data(self, table_name):
        """Récupère toutes les données d'une table"""
        try:
            # 1. Obtenir les colonnes de la table
            self.cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = %s AND table_name = %s 
                ORDER BY ordinal_position
            """, (self.schema, table_name))
            columns = [row[0] for row in self.cursor.fetchall()]

            if not columns:
                print(f"Pas de colonnes trouvées pour la table {table_name}")
                return []

            # 2. Récupérer les données
            query = f"SELECT {', '.join(['%s']*len(columns))} FROM {self.schema}.{table_name}"
            query = query % tuple(columns)
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            return {
                'columns': columns,
                'data': data
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des données de {table_name}: {e}")
            return {'columns': [], 'data': []}

    def generate_sql_script(self, output_file):
        """Génère un script SQL complet pour recréer la base de données"""
        self.connect()
        try:
            schema_objects = self.get_schema_objects()

            with open(output_file, 'w', encoding='utf-8') as f:
                # En-tête
                f.write(f"-- Script de restauration complète de la base de données {self.connection_params['database']}\n")
                f.write(f"-- Généré le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Schéma: {self.schema}\n\n")

                # Débuter une transaction
                f.write("BEGIN;\n\n")

                # Créer le schéma si nécessaire
                f.write(f"CREATE SCHEMA IF NOT EXISTS {self.schema};\n\n")

                # 1. Types personnalisés
                if schema_objects['types']:
                    f.write("-- Types personnalisés\n")
                    for t in schema_objects['types']:
                        if t['typtype'] == 'e':  # Enum
                            f.write(f"CREATE TYPE {self.schema}.{t['name']} AS ENUM ({t['enum_values']});\n")
                    f.write("\n")

                # 2. Tables
                if schema_objects['tables']:
                    f.write("-- Tables\n")
                    for table in schema_objects['tables']:
                        f.write(f"CREATE TABLE {self.schema}.{table['table_name']} (\n")
                        f.write("    " + ",\n    ".join(table['columns']))
                        f.write("\n);\n\n")

                # 3. Séquences
                if schema_objects['sequences']:
                    f.write("-- Séquences\n")
                    for seq in schema_objects['sequences']:
                        if seq['seq_details']:
                            # Les séquences sont généralement créées avec les tables,
                            # mais on réinitialise les valeurs au besoin
                            self.cursor.execute(f"SELECT last_value FROM {seq['sequence_name']}")
                            last_value = self.cursor.fetchone()[0]
                            f.write(f"SELECT pg_catalog.setval('{seq['sequence_name']}', {last_value}, true);\n")
                    f.write("\n")

                # 4. Fonctions
                if schema_objects['functions']:
                    f.write("-- Fonctions\n")
                    for func in schema_objects['functions']:
                        f.write(f"{func['function_def']};\n\n")

                # 5. Vues
                if schema_objects['views']:
                    f.write("-- Vues\n")
                    for view in schema_objects['views']:
                        f.write(f"CREATE OR REPLACE VIEW {self.schema}.{view['view_name']} AS\n")
                        f.write(f"{view['view_definition']};\n\n")

                # 6. Contraintes (PK, FK, etc.)
                if schema_objects['constraints']:
                    f.write("-- Contraintes\n")
                    for c in schema_objects['constraints']:
                        if c['constraint_type'] == 'PRIMARY KEY':
                            f.write(f"ALTER TABLE {self.schema}.{c['table_name']} ADD CONSTRAINT {c['constraint_name']} PRIMARY KEY ({c['pk_columns']});\n")
                        elif c['constraint_type'] == 'UNIQUE':
                            f.write(f"ALTER TABLE {self.schema}.{c['table_name']} ADD CONSTRAINT {c['constraint_name']} UNIQUE ({c['pk_columns']});\n")
                        elif c['constraint_type'] == 'FOREIGN KEY':
                            f.write(f"ALTER TABLE {self.schema}.{c['table_name']} ADD CONSTRAINT {c['constraint_name']} FOREIGN KEY ({c['fk_columns']}) REFERENCES {self.schema}.{c['ref_table']} ({c['ref_columns']})")
                            if c['update_rule'] != 'NO ACTION':
                                f.write(f" ON UPDATE {c['update_rule']}")
                            if c['delete_rule'] != 'NO ACTION':
                                f.write(f" ON DELETE {c['delete_rule']}")
                            f.write(";\n")
                    f.write("\n")

                # 7. Index
                if schema_objects['indexes']:
                    f.write("-- Index\n")
                    for idx in schema_objects['indexes']:
                        f.write(f"{idx['indexdef']};\n")
                    f.write("\n")

                # 8. Triggers
                if schema_objects['triggers']:
                    f.write("-- Triggers\n")
                    for trg in schema_objects['triggers']:
                        f.write(f"CREATE TRIGGER {trg['trigger_name']} {trg['event_manipulation']} ON {self.schema}.{trg['event_object_table']} FOR EACH ROW {trg['action_statement']};\n")
                    f.write("\n")

                # 9. Données des tables
                f.write("-- Données\n")
                for table in schema_objects['tables']:
                    table_data = self.get_table_data(table['table_name'])
                    if table_data['data']:
                        f.write(f"-- Table: {self.schema}.{table['table_name']} ({len(table_data['data'])} lignes)\n")

                        batch_size = 1000  # Traiter par lots pour les grandes tables
                        columns_str = ", ".join(table_data['columns'])

                        for i in range(0, len(table_data['data']), batch_size):
                            batch = table_data['data'][i:i+batch_size]

                            f.write(f"INSERT INTO {self.schema}.{table['table_name']} ({columns_str}) VALUES\n")

                            values_list = []
                            for row in batch:
                                values = []
                                for val in row:
                                    if val is None:
                                        values.append("NULL")
                                    elif isinstance(val, str):
                                        # Échapper les apostrophes
                                        escaped_val = val.replace("'", "''")
                                        values.append(f"'{escaped_val}'")
                                    elif isinstance(val, datetime):
                                        values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                                    elif isinstance(val, bool):
                                        values.append("TRUE" if val else "FALSE")
                                    elif isinstance(val, (bytes, bytearray)):
                                        # Convertir en format hexadécimal pour les bytea
                                        hex_val = ''.join('\\x{:02x}'.format(b) for b in val)
                                        values.append(f"'{hex_val}'")
                                    else:
                                        values.append(str(val))

                                values_list.append("(" + ", ".join(values) + ")")

                            f.write(",\n".join(values_list) + ";\n\n")

                # Commit de la transaction
                f.write("COMMIT;\n")

                print(f"Script SQL généré avec succès dans {output_file}")

        except Exception as e:
            print(f"Erreur lors de la génération du script SQL: {e}")
        finally:
            self.close()

def main():
    parser = argparse.ArgumentParser(description='Extraire une base de données PostgreSQL vers un fichier SQL')
    parser.add_argument('--host', default=DB_HOST, help=f'Hôte du serveur PostgreSQL (défaut: {DB_HOST})')
    parser.add_argument('--port', type=int, default=DB_PORT, help=f'Port du serveur PostgreSQL (défaut: {DB_PORT})')
    parser.add_argument('--database', default=DB_NAME, help=f'Nom de la base de données (défaut: {DB_NAME})')
    parser.add_argument('--user', default=DB_USER, help=f'Nom d\'utilisateur PostgreSQL (défaut: {DB_USER})')
    parser.add_argument('--password', default=DB_PASSWORD, help=f'Mot de passe PostgreSQL')
    parser.add_argument('--schema', default=DB_SCHEMA, help=f'Schéma à extraire (défaut: {DB_SCHEMA})')
    parser.add_argument('--output', default=OUTPUT_FILE, help='Fichier de sortie (défaut: nom_bdd_date.sql)')

    args = parser.parse_args()

    if args.output is None:
        # Nom par défaut pour le fichier de sortie
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"{args.database}_{timestamp}.sql"

    extractor = PostgreSQLExtractor(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
        schema=args.schema
    )

    extractor.generate_sql_script(args.output)

if __name__ == "__main__":
    main()