<?php
// Routeur de démonstration : toutes les URL affichent cette page.
// Exemple facultatif : sélectionnez-le dans le lanceur pour essayer le routage.
// Votre propre fichier index.php reste local et ne doit pas être publié avec ce projet.
declare(strict_types=1);

header('Content-Type: text/html; charset=UTF-8');
$chemin = htmlspecialchars(
    $_SERVER['REQUEST_URI'] ?? '/',
    ENT_QUOTES | ENT_SUBSTITUTE,
    'UTF-8'
);
?>
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Votre serveur PHP fonctionne</title>
    <style>
        :root { color-scheme: dark; }
        * { box-sizing: border-box; }
        body {
            margin: 0; min-height: 100vh; display: grid; place-items: center;
            padding: 24px; background: #10151f; color: #eef2ff;
            font: 16px/1.6 -apple-system, BlinkMacSystemFont, sans-serif;
        }
        main {
            width: min(100%, 620px); padding: clamp(24px, 6vw, 48px);
            background: #192231; border: 1px solid #2e3c50; border-radius: 16px;
        }
        .statut {
            display: inline-block; padding: 5px 12px; border-radius: 12px;
            background: #17482f; color: #a7f3c1; font-size: 14px;
        }
        h1 { font-size: clamp(26px, 5vw, 36px); line-height: 1.2; }
        p { color: #c6d0e0; }
        code {
            padding: 3px 7px; border-radius: 6px; background: #10151f;
            overflow-wrap: anywhere;
        }
    </style>
</head>
<body>
    <main>
        <span class="statut">● En cours</span>
        <h1>Votre serveur PHP fonctionne.</h1>
        <p>Le lanceur utilise ce fichier comme routeur pour les requêtes.</p>
        <p>Adresse demandée : <code><?= $chemin ?></code></p>
        <p>Pour utiliser votre application, sélectionnez son fichier PHP
            depuis le lanceur.</p>
    </main>
</body>
</html>
