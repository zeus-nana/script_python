import pandas as pd
import matplotlib.pyplot as plt

# Lire le fichier Excel avec le chemin complet
df = pd.read_excel(r"C:\Users\fnana\Documents\analyse.xlsx")

# Grouper par mois et année, et calculer la somme des frais totaux
totaux_mensuels = df.groupby(['année', 'mois'])['total_frais'].sum().reset_index()

# Ajouter une liste des mois en ordre
mois_ordre = [
    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
]

# Convertir 'mois' en catégorie ordonnée
totaux_mensuels['mois'] = pd.Categorical(totaux_mensuels['mois'], categories=mois_ordre, ordered=True)

# Trier les données par mois
totaux_mensuels = totaux_mensuels.sort_values(['année', 'mois'])

# Créer le pivot pour comparer les années
pivot = totaux_mensuels.pivot(index='mois', columns='année', values='total_frais')

# Afficher le tableau comparatif
print("Tableau comparatif des totaux par mois :")
print(pivot)

# Créer les visualisations
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Graphique en barres
pivot.plot(kind='bar', ax=ax1, width=0.8)
ax1.set_title('Comparaison des frais mensuels par année')
ax1.set_xlabel('Mois')
ax1.set_ylabel('Total des frais')
ax1.tick_params(axis='x', rotation=45)

# Ajouter les valeurs sur les barres
for container in ax1.containers:
    ax1.bar_label(container, fmt='%.0f', padding=3)

# Courbe d'évolution
for annee in pivot.columns:
    ax2.plot(pivot.index, pivot[annee], marker='o', label=str(annee))

ax2.set_title('Évolution des frais totaux')
ax2.set_xlabel('Mois')
ax2.set_ylabel('Total des frais')
ax2.tick_params(axis='x', rotation=45)
ax2.legend(title='Année')

# Ajouter les valeurs sur les points
for annee in pivot.columns:
    for x, y in zip(pivot.index, pivot[annee]):
        if not pd.isna(y):  # Vérifier si la valeur n'est pas NaN
            ax2.annotate(f'{y:.0f}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center')

plt.tight_layout()  # Ajuster automatiquement l'espacement
plt.show()
