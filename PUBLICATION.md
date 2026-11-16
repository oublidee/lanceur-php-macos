# Publication sur GitHub

Le projet utilise la branche `main`. Ce document décrit la publication d’une nouvelle copie du projet et l’envoi des modifications suivantes.

Nom proposé : **lanceur-php-macos**

Description proposée : **Lanceur graphique en français pour le serveur PHP Homebrew sur macOS Apple Silicon, avec CustomTkinter.**

## Préparer un commit local

Placez les fichiers modifiés dans l’index Git, puis relisez le contenu du commit :

```bash
git status
git add .gitignore README.md PUBLICATION.md requirements.txt index.php php_server_launcher.py
git diff --cached --stat
git diff --cached
```

Définissez l’identité que vous souhaitez rendre publique pour ce dépôt. Pour masquer votre adresse personnelle, copiez l’adresse de commit privée fournie dans les paramètres de votre compte GitHub :

```bash
git config --local user.name "VOTRE_NOM_PUBLIC"
git config --local user.email "VOTRE_ADRESSE_DE_COMMIT_GITHUB"
git commit -m "Version initiale du lanceur PHP pour macOS"
```

Aucune licence n’a été choisie automatiquement. Si vous ajoutez un fichier `LICENSE`, incluez-le avec `git add LICENSE` avant le commit.

## Publier une nouvelle copie

Ces opérations sont à effectuer uniquement lorsque vous décidez de publier.

Sur GitHub, créez un dépôt public nommé `lanceur-php-macos`, vide, sans README, licence ni `.gitignore` générés par GitHub. Les fichiers locaux seront utilisés.

Remplacez `VOTRE_COMPTE` dans les commandes suivantes :

```bash
git remote add origin https://github.com/VOTRE_COMPTE/lanceur-php-macos.git
git push -u origin main
```

Le dossier `sites-locaux/`, les environnements Python, les fichiers `.env` et les journaux sont ignorés. Le fichier `index.php` suivi est uniquement la démonstration publique fournie avec le projet.

## Envoyer les modifications suivantes

Si `origin` est déjà configuré pour votre dépôt, utilisez ces commandes après avoir créé le commit :

```bash
git remote -v
git push origin main
```
