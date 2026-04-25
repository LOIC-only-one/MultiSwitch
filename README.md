# MultiSwitch Community 🚀

MultiSwitch est un shell Python pour piloter plusieurs switches en parallele.
Le projet est maintenant modulaire et simple a maintenir pour une equipe communautaire.

## Apercu GIF 🎬

Ajoute tes GIFs dans `docs/gifs` puis ils seront visibles ici:

![Demo shell](docs/gifs/demo-shell.gif)
![Demo Aruba](docs/gifs/demo-aruba.gif)

## Pourquoi ce repo ✅

- Structure claire: classes, core, shell, features
- Ajout de features sans casser le coeur
- Commandes Aruba via profil JSON
- Lab virtualise Docker pour tester sans materiel

## Arborescence 📁

```text
MultiSwitch/
├─ main.py
├─ src/
│  └─ multiswitch/
│     ├─ app.py
│     ├─ config/
│     ├─ core/
│     ├─ models/
│     ├─ shell/
│     ├─ ui/
│     └─ features/
│        └─ aruba/
├─ docker-compose.lab.yml
├─ switches.lab.json
├─ aruba-profile.example.json
├─ lab-commands.txt
└─ docs/
```

## Installation ⚙️

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install rich netmiko pyreadline3
```

## Lancer le shell 💻

```powershell
c:/Users/loicm/Desktop/MultiSwitch/.venv/Scripts/python.exe main.py
```

## Test rapide avec lab Docker 🧪

```powershell
docker compose -f docker-compose.lab.yml up -d
c:/Users/loicm/Desktop/MultiSwitch/.venv/Scripts/python.exe main.py --inventory switches.lab.json
```

Puis dans le shell:

```text
list
connect all
select all
hostname
whoami
script lab-commands.txt
```

## Feature Aruba A a Z 🌴

Le flux Aruba repose sur un profil JSON lisible.

1. Previsualiser les commandes generees:

```text
aruba-preview aruba-profile.example.json
```

2. Appliquer la configuration sur la selection:

```text
select all
aruba-apply aruba-profile.example.json
```

Le profil couvre:
- hostname
- VLANs
- ports access et trunks
- DNS, NTP, gateway
- SNMP
- comptes admin
- banner

## Contribution 🤝

Lis [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) pour proposer une feature.

## Architecture 🧠

Lis [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) pour comprendre la logique module par module.
