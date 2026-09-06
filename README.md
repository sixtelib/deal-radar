# Deal Radar

Surveillance automatique d'annonces de cession d'entreprise (Fusacq, Transentreprise) selon tes critères, avec alerte email et une landing page listant les annonces retenues.

**Critères actuels** (modifiables dans `config.py`) :
- Île-de-France
- CA entre 500 k€ et 1 M€
- Motif de cession : départ à la retraite
- Apport en fonds propres max : 150 k€

---

## ⚠️ À lire avant de déployer

1. **CGU des sites** — Fusacq et Transentreprise interdisent probablement le scraping automatisé dans leurs conditions d'utilisation. Ce n'est pas illégal en soi pour un usage personnel et raisonnable (1 vérification/jour, pas de revente de données), mais tu t'exposes en théorie à un blocage d'IP. Le script respecte une pause de 3 secondes entre requêtes par courtoisie — ne la réduis pas.
2. **Le parseur est une heuristique** — il repose sur les libellés de champs qu'on retrouve sur le réseau Fusacq/Transentreprise/CCI-CMA ("Forme juridique", "Raison principale de la cession", tableau CA/EBE/REX/RN). Si un site change son gabarit, certains champs peuvent ne plus être détectés — ils apparaîtront alors en "à vérifier" plutôt que d'exclure l'annonce à tort.
3. **Toujours vérifier l'annonce d'origine** avant toute décision. Ce script fait un premier tri, pas une analyse financière.

---

## Comment ça marche

```
config.py         → tes critères + les pages de recherche à surveiller
scraper/           → récupération et extraction du texte des annonces
filters.py         → applique tes critères, calcule un score
storage.py         → mémorise les annonces déjà vues (data/seen.json)
notifier.py        → envoie l'email d'alerte pour les nouvelles annonces pertinentes
render.py          → génère la landing page statique (public/index.html)
main.py            → orchestre tout — c'est ce script qu'on exécute chaque jour
```

## Installation en local (pour tester avant de déployer)

```bash
cd deal-radar
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis remplis tes identifiants SMTP dans .env
```

**Vérifier que tout fonctionne sans réseau** (avec des annonces factices) :
```bash
python test_pipeline.py
open public/index.html   # ou double-clique dessus
```

## Étape indispensable : configurer les recherches

Le script ne devine pas les paramètres de recherche des sites (ils changent souvent). Toi :

1. Va sur fusacq.com et transentreprise.com
2. Fais une recherche filtrée sur Île-de-France (et le secteur qui t'intéresse, si tu veux)
3. Copie l'URL de la page de résultats
4. Colle-la dans `config.py`, section `SEARCH_SOURCES` → `search_urls`

```python
SEARCH_SOURCES = [
    {
        "name": "fusacq",
        "search_urls": [
            "https://www.fusacq.com/......",   # colle ton URL ici
        ],
        "detail_link_pattern": r"/annonce[s]?[-/][a-z0-9-]+",
    },
    ...
]
```

Si `detail_link_pattern` ne capture pas les bons liens (le script en trouve 0), ouvre le code source de la page de résultats (clic droit → "Afficher le code source") et ajuste le pattern regex pour qu'il corresponde aux URLs des fiches individuelles.

Lance ensuite `python main.py` en local pour vérifier que des annonces sont bien trouvées, avant de déployer.

## Déploiement (pour que ça tourne vraiment tout seul)

**Option recommandée — GitHub Actions (gratuit, pas de serveur à gérer) :**

1. Crée un repo GitHub et pousse ce dossier dedans
2. Dans les paramètres du repo → **Settings → Secrets and variables → Actions**, ajoute :
   `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO`, `ALERT_EMAIL_FROM`
3. Dans **Settings → Pages**, source = "GitHub Actions"
4. Le workflow `.github/workflows/deal-radar.yml` est déjà configuré : il tourne chaque jour à 7h UTC, envoie les alertes email, et publie la landing page sur `https://<ton-user>.github.io/<ton-repo>/`
5. Pour tester tout de suite sans attendre le lendemain : onglet **Actions** du repo → "Deal Radar" → "Run workflow"

**Alternative — Render.com ou Railway** (si tu préfères ne pas utiliser GitHub Pages) : crée un "Cron Job" pointant sur `python main.py`, avec les mêmes variables d'environnement que le `.env.example`. Dans ce cas, prévois un stockage persistant (disque payant) ou un bucket externe (S3, etc.) pour conserver `data/seen.json` et `public/index.html` d'une exécution à l'autre — sans ça, l'historique des annonces déjà vues sera perdu à chaque run.

## Gmail pour l'envoi d'email

Le mot de passe normal de ton compte Gmail ne fonctionnera pas avec SMTP. Il faut :
1. Activer la validation en 2 étapes sur ton compte Google
2. Créer un "mot de passe d'application" sur https://myaccount.google.com/apppasswords
3. Utiliser ce mot de passe généré comme `SMTP_PASSWORD`
