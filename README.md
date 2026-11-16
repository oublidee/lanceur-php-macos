# Lanceur PHP · macOS Apple Silicon

Une interface graphique en français pour démarrer et arrêter le serveur PHP intégré de Homebrew. Le lanceur utilise CustomTkinter, avec un thème sombre par défaut et un journal horodaté en temps réel.

Choisissez votre fichier PHP, réglez le port et démarrez votre serveur depuis une seule fenêtre.

## Démarrage rapide

Depuis le dossier du projet :

```bash
python3 php_server_launcher.py
```

Au premier lancement, laissez le Terminal ouvert pendant la préparation de Python, Tkinter et CustomTkinter si nécessaire. Dans la fenêtre, attendez **« 🎉 Tout est OK – environnement prêt »**. Cliquez sur **Choisir un fichier…** pour sélectionner votre fichier PHP, puis sur **Démarrer le serveur**.

Pour un essai, sélectionnez le fichier facultatif [`exemples/index.php`](exemples/index.php). La démonstration sera accessible à l’adresse **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.

Votre propre fichier PHP n’a pas besoin d’être présent sur GitHub. Le lanceur peut servir un fichier situé ailleurs sur votre Mac.

## Fonctionnalités

- Interface sombre, coins arrondis et badge « Arrêté / En cours ».
- Bouton unique pour démarrer ou arrêter le serveur.
- Sélection d’un fichier PHP utilisé comme routeur pour les requêtes.
- Hôte au choix : `127.0.0.1`, `0.0.0.0` ou `localhost`.
- Port modifiable dans l’interface et dans le script.
- Ouverture automatique ou manuelle du navigateur.
- Journal PHP et Homebrew en direct, avec bouton d’effacement.
- Vérification de Homebrew, exécution de `brew update`, installation de PHP si nécessaire et affichage de sa version.
- Détection de l’ancien Tk système de macOS, sélection de Python Homebrew et installation de son module Tkinter si nécessaire.
- Installation automatique de CustomTkinter dans un environnement Python isolé si la bibliothèque est absente.
- Arrêt du serveur à la fermeture de la fenêtre, avec arrêt forcé en dernier recours.

## Prérequis

- macOS sur un Mac Apple Silicon.
- [Homebrew](https://brew.sh/fr/) installé ; `/opt/homebrew` est prioritaire.
- Une commande `python3` disponible pour lancer le script.
- Un accès Internet pour les installations nécessaires et la mise à jour de Homebrew.

Le lanceur recherche un Python compatible avec Tk. Si nécessaire, il installe Python Homebrew et la formule `python-tk@X.Y` correspondant à sa version. Les premières opérations de préparation s’affichent dans le Terminal, avant l’ouverture de la fenêtre.

## Utilisation

1. Lancez le script depuis le Terminal et attendez la fin des vérifications.
2. Cliquez sur **Choisir un fichier…** pour sélectionner le routeur de votre application PHP. Pour essayer le lanceur, vous pouvez choisir `exemples/index.php`.
3. Choisissez l’hôte et le port. Activez **Ouvrir le navigateur** si vous souhaitez une ouverture automatique.
4. Cliquez sur **Démarrer le serveur**. Le badge passe à **En cours** et le bouton devient **Arrêter le serveur**.
5. Consultez les requêtes et les erreurs dans le journal. Le bouton **Effacer** nettoie son affichage.
6. Cliquez sur **Arrêter le serveur** pour modifier les réglages, ou fermez la fenêtre pour quitter.

L’adresse par défaut est `http://127.0.0.1:8000/`. Le bouton **Ouvrir** permet de l’ouvrir à tout moment lorsque le serveur fonctionne.

Pour vérifier le routage avec la démonstration, ouvrez aussi `http://127.0.0.1:8000/bonjour` : la même page affiche le chemin demandé.

### Fichier par défaut et exemple facultatif

Le paramètre `DEFAULT_FILE = "index.php"` recherche votre fichier personnel à côté du script Python. Ce fichier local est ignoré par Git et n’est pas fourni à la racine du dépôt. S’il est absent, choisissez simplement un autre fichier depuis l’interface.

Pour essayer l’exemple sans utiliser le sélecteur de fichiers, vous pouvez en créer une copie locale, sans remplacer un éventuel `index.php` existant :

```bash
cp -n exemples/index.php index.php
python3 php_server_launcher.py
```

## Préparation automatique

Le lancement se déroule en deux étapes :

1. **Avant la fenêtre** : contrôle de Python et Tk sur macOS, recherche d’un interpréteur compatible, installation de Python Homebrew et de son module Tkinter au besoin, puis installation de CustomTkinter si la bibliothèque manque.
2. **Dans la fenêtre** : détection de Homebrew, exécution de `brew update`, recherche de PHP, installation via `brew install php` si nécessaire et affichage de sa version.

Les vérifications Homebrew s’exécutent en arrière-plan pour garder la fenêtre réactive. Elles sont répétées à chaque lancement et lorsque vous cliquez sur **Revérifier**. Le serveur PHP démarre uniquement lorsque vous cliquez sur son bouton.

## Configuration

Les paramètres sont regroupés en haut de `php_server_launcher.py` :

| Paramètre | Valeur par défaut | Usage |
| --- | --- | --- |
| `PORT` | `8000` | Port d’écoute |
| `DEFAULT_FILE` | `"index.php"` | Fichier routeur, relatif au script ou absolu |
| `HOST` | `"127.0.0.1"` | Adresse d’écoute |
| `AUTO_OPEN_BROWSER` | `True` | Ouverture du navigateur au démarrage |
| `THEME` | `"blue"` | Thème CustomTkinter |
| `APPEARANCE_MODE` | `"dark"` | Apparence : `dark`, `light` ou `system` |
| `WINDOW_WIDTH` | `980` | Largeur initiale de la fenêtre |
| `WINDOW_HEIGHT` | `740` | Hauteur initiale de la fenêtre |

Le dossier du fichier PHP sélectionné devient la racine du serveur et son répertoire de travail. Le fichier sélectionné est transmis à PHP comme routeur : il est exécuté pour chaque requête. Si votre routeur retourne `false`, PHP peut servir directement le fichier statique demandé.

La commande utilisée suit cette forme :

```bash
/opt/homebrew/opt/php/bin/php -S 127.0.0.1:8000 -t /chemin/du/site /chemin/du/site/index.php
```

Le chemin réel est déterminé par Homebrew. Une formule PHP versionnée déjà installée est également prise en charge.

## Fichiers du projet

```text
.
├── php_server_launcher.py  # Application et paramètres
├── exemples/
│   └── index.php           # Démonstration facultative du routage
├── requirements.txt        # Version CustomTkinter vérifiée
├── README.md               # Installation et utilisation
├── PUBLICATION.md          # Instructions de publication GitHub
└── .gitignore              # Exclusions des fichiers locaux
```

Vous pouvez conserver le script et votre routeur dans un même dossier, ou choisir un fichier PHP situé ailleurs sur votre Mac. Seul l’exemple de `exemples/` est suivi par Git ; le fichier `index.php` à la racine reste local.

## Dépendances Python

L’installation de CustomTkinter est automatique si nécessaire. Le dossier `.venv-php-launcher-X.Y` est créé à côté du script et exclu de Git.

Pour installer explicitement la version de CustomTkinter vérifiée avec ce projet, utilisez un environnement Python avec Tk récent :

```bash
/opt/homebrew/bin/python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python php_server_launcher.py
```

## Dépannage

**Fenêtre vide ou avertissement concernant le Tk système de macOS**

Utilisez la version actuelle du script : elle vérifie Python/Tk avant de créer la fenêtre et peut se relancer avec Python Homebrew. Si une installation échoue, consultez le message dans le Terminal.

**Homebrew introuvable**

Installez Homebrew depuis son site officiel, puis relancez le script ou cliquez sur **Revérifier**.

**Échec de `brew update`**

Vérifiez la connexion Internet et le message Homebrew dans le journal, puis cliquez sur **Revérifier**. Le démarrage reste désactivé tant que la préparation échoue.

**Port déjà utilisé**

Choisissez un autre port, par exemple `8001`, puis redémarrez le serveur.

**Fichier PHP introuvable**

Placez votre fichier `index.php` à côté du script ou sélectionnez un autre fichier avec le bouton prévu. Le fichier `exemples/index.php` est disponible pour un simple essai.

## Développement local

Le serveur intégré de PHP est destiné au développement. L’hôte `0.0.0.0` permet l’écoute sur les interfaces réseau ; le navigateur local utilise alors `127.0.0.1`.

Pour garder vos sites personnels hors du dépôt, placez-les dans `sites-locaux/`, un dossier ignoré par Git, puis choisissez leur routeur dans l’interface.

Vérifications réalisées : interface avec Python 3.15 et Tk 9.1, démarrage réel de PHP, routage de plusieurs URL, capture des journaux, libération du port et arrêt forcé. Les scénarios d’installation PHP ont été vérifiés avec des commandes Homebrew simulées.

## Licence

Aucune licence de réutilisation n’est fournie pour le moment.
