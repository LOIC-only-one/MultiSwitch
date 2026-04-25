# Architecture du projet

## Objectif

Rendre le code lisible, facile a deboguer et simple a faire evoluer.

## Couches

- `main.py`: point d'entree
- `src/multiswitch/app.py`: parsing des arguments et lancement shell
- `src/multiswitch/shell`: boucle interactive et handlers de commandes
- `src/multiswitch/core`: orchestration des connexions et execution parallele
- `src/multiswitch/models`: classes metier (`SwitchConfig`, `SwitchConnection`)
- `src/multiswitch/features`: modules fonctionnels independants
- `src/multiswitch/ui`: affichage Rich

## Flux d'une commande

1. L'utilisateur tape une commande dans le shell.
2. Le shell route vers un handler simple.
3. Le handler appelle `SwitchPool`.
4. `SwitchPool` execute en parallele et retourne des resultats.
5. Le module UI affiche les resultats.

## Flux Aruba

1. `aruba-preview <profil.json>` charge le profil.
2. `ArubaProvisioning` construit une liste de commandes.
3. `aruba-apply <profil.json>` envoie ces commandes sur la selection.

## Regles de code du projet

- Pas de logique metier dans `main.py`
- Une methode = un comportement clair
- Pas de magie dans les noms de variables
- Les features doivent vivre dans `src/multiswitch/features`
