# Contribuer a MultiSwitch

Merci de contribuer 🙌

## Workflow simple

1. Cree une branche feature
2. Fais de petits commits lisibles
3. Ajoute une doc courte si tu ajoutes une commande
4. Ouvre une PR avec exemples de test

## Style de code

- Fonctions courtes
- Noms explicites
- Messages d'erreur utiles
- Eviter les syntaxes complexes si une version simple existe

## Ajouter une feature

- Cree un dossier dans `src/multiswitch/features/<nom>`
- Cree une classe principale de feature
- Branche les commandes dans `src/multiswitch/shell/multiswitch_shell.py`
- Documente la feature dans le README

## Tests manuels minimum

- `main.py --version`
- `help`
- `list`
- `connect --help`
- test lab Docker
- test `aruba-preview`
