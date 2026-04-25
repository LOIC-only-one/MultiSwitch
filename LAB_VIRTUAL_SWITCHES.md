# Tester MultiSwitch avec des switches virtualises

Ce lab cree 3 cibles SSH locales qui servent de switches virtualises pour valider:
- connexions paralleles
- selection de cibles
- execution de commandes en masse
- mode script

## Prerequis
- Docker Desktop lance
- Python venv deja configure pour ce projet

## 1) Demarrer le lab
Depuis le dossier du projet:

```powershell
docker compose -f docker-compose.lab.yml up -d
```

Verifier que les 3 conteneurs sont UP:

```powershell
docker compose -f docker-compose.lab.yml ps
```

## 2) Lancer MultiSwitch avec l'inventaire de lab

```powershell
c:/Users/loicm/Desktop/MultiSwitch/.venv/Scripts/python.exe main.py --inventory switches.lab.json
```

## 3) Scenario de test rapide
Dans le shell MultiSwitch:

```text
list
connect all
select all
uname -a
hostname
whoami
script lab-commands.txt
disconnect all
exit
```

## 4) Exemple de script de commandes
Cree un fichier `lab-commands.txt` a cote de main.py:

```text
hostname
whoami
uptime
```

Puis execute:

```text
script lab-commands.txt
```

## 5) Arreter / supprimer le lab

```powershell
docker compose -f docker-compose.lab.yml down
```

## Notes
- Pour ce lab, le type Netmiko utilise est `linux`.
- Ce n'est pas un vrai NOS (Aruba/Comware), mais c'est ideal pour valider la logique parallele du shell.
- Pour des tests plus realistes NOS, tu peux ensuite evoluer vers EVE-NG/GNS3/containerlab avec des images reseau dediees.
