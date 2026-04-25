# Profil Aruba JSON

Le fichier JSON est pense pour etre lisible par une equipe.

## Champs supportes

- `hostname`
- `domain_name`
- `dns_servers` (liste)
- `ntp_servers` (liste)
- `default_gateway`
- `snmp`
- `vlans`
- `access_ports`
- `trunks`
- `admins`
- `ssh_enabled`
- `banner`

## Exemple rapide

Voir [aruba-profile.example.json](../aruba-profile.example.json).

## Commandes shell

```text
aruba-preview aruba-profile.example.json
select all
aruba-apply aruba-profile.example.json
```
