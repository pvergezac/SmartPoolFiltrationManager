# 🏊 Smart Pool Filtration Manager — Custom Component Home Assistant

![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white) [![Hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs) ![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

[![GitHub release](https://img.shields.io/github/release/pvergezac/smartpoolfiltrationmanager.svg)](https://GitHub.com/pvergezac/smartpoolfiltrationmanager/releases/)
![GitHub Release Date](https://img.shields.io/github/release-date/pvergezac/smartpoolfiltrationmanager)
[![Github All Releases](https://img.shields.io/github/downloads/pvergezac/smartpoolfiltrationmanager/total.svg)]()
[![GitHub license](https://badgen.net/github/license/pvergezac/smartpoolfiltrationmanager)](https://github.com/pvergezac/smartpoolfiltrationmanager/blob/master/LICENSE)
[![GitHub forks](https://badgen.net/github/forks/pvergezac/smartpoolfiltrationmanager/)](https://GitHub.com/pvergezac/smartpoolfiltrationmanager/network/)

[![GitHub stars](https://badgen.net/github/stars/pvergezac/smartpoolfiltrationmanager)](https://GitHub.com/pvergezac/SmartPoolFiltrationManager/stargazers/)
![GitHub Repo stars](https://img.shields.io/github/stars/pvergezac/SmartPoolFiltrationManager)

Contrôle intelligent de la pompe de filtration piscine selon la **température de l'eau** et la **production solaire photovoltaïque**, ainsi que la couleur du jour et plage horaire **EDF Tempo** (intégration RTE Tempo nécessaire).

---

## Fonctionnalités

- ⏱️ **Durée calculée automatiquement** selon la règle T°/2 (ex : 24°C → 6h de filtration)
- ☀️ **Priorité solaire** : la pompe tourne en priorité quand les panneaux produisent suffisamment
- 🔋 **Complétion intelligente** : si la production solaire ne suffit pas, complète sur le réseau en fin de plage horaire
- 📊 **Suivi journalier** : durée filtrée, contribution solaire, progression
- 🔧 **4 modes de fonctionnement** : Automatique, Solaire uniquement, Manuel, Arrêt forcé
- 💾 **Persistance** : les compteurs survivent aux redémarrages de HA

---

## Installation

### Via HACS (recommandé)

1. Dans HACS → Intégrations → ⋮ → Dépôts personnalisés
2. Ajouter : `https://github.com/pvergezac/SmartPoolFiltrationManager` (type : Intégration)
3. Installer "Smart Pool Filtration Manager"
4. Redémarrer Home Assistant

### Manuel

1. Copier le dossier `custom_components/smartpoolfiltmgr/` dans votre dossier `config/custom_components/`
2. Redémarrer Home Assistant

---

## Configuration

### Étape 1 — Ajouter l'intégration

**Paramètres → Appareils et services → Ajouter une intégration → Smart Pool Filtration Manager**

Renseignez :
| Champ | Description | Exemple |
|-------|-------------|---------|
| Switch de la pompe | Entité switch qui allume/éteint la pompe | `switch.pompe_piscine` |
| Température de l'eau | Sonde de température dans le bassin | `sensor.temperature_piscine` |
| Production solaire | Puissance instantanée des panneaux (W) | `sensor.solaire_puissance` |
| Consommation réseau | Puissance soutirée au réseau (optionnel) | `sensor.consommation_reseau` |

### Étape 2 — Options avancées

Accessible via le bouton **Configurer** sur la carte de l'intégration :

| Option                      | Défaut     | Description                                   |
| --------------------------- | ---------- | --------------------------------------------- |
| Production solaire minimale | 500 W      | Seuil en-dessous duquel le solaire est ignoré |
| Priorité solaire            | ✅ Activée | Favorise les heures de production PV          |
| Durée minimale/jour         | 2 h        | Garantie même si température froide           |
| Durée maximale/jour         | 12 h       | Plafond absolu                                |
| Heure de début              | 8h         | Aucune filtration avant cette heure           |
| Heure de fin                | 20h        | Aucune filtration après cette heure           |

---

## Entités créées

### Capteurs

| Entité                                        | Description                                  |
| --------------------------------------------- | -------------------------------------------- |
| `sensor.pool_filtration_duree_journaliere`    | Minutes de filtration effectuées aujourd'hui |
| `sensor.pool_filtration_duree_cible`          | Durée cible calculée selon T° de l'eau       |
| `sensor.pool_filtration_contribution_solaire` | Minutes filtrées grâce au solaire            |
| `sensor.pool_filtration_mode`                 | Mode actif + état détaillé                   |

### Contrôles

| Entité                                  | Description                                                |
| --------------------------------------- | ---------------------------------------------------------- |
| `select.pool_filtration_mode`           | Sélecteur de mode (Automatique / Solaire / Manuel / Arrêt) |
| `switch.pool_filtration_forcage_manuel` | Force la pompe ON (passe en mode Manuel)                   |

---

## Logique de décision

```
Toutes les 60 secondes :
│
├─ Mode MANUEL ?     → respecter l'état du switch manuel
├─ Mode ARRÊT ?      → pompe OFF
├─ Quota atteint ?   → pompe OFF (durée cible dépassée)
├─ Hors plage horaire ? → pompe OFF
│
├─ Mode SOLAIRE ?
│   └─ Production >= seuil → pompe ON
│
└─ Mode AUTO (défaut) :
    ├─ Solaire dispo → pompe ON ☀️
    └─ Pas de solaire :
        ├─ Temps restant > estimation solaire → pompe ON (réseau) 🔌
        └─ Sinon → pompe OFF (attendre le solaire)
```

### Table de durée selon température

| Température | Durée de filtration |
| ----------- | ------------------- |
| ≤ 10°C      | 1 h                 |
| 15°C        | 2 h                 |
| 20°C        | 4 h                 |
| 24°C        | 6 h                 |
| 28°C        | 9 h                 |
| ≥ 30°C      | 12 h                |

_(Interpolation linéaire entre les points)_

---

## Tableau de bord Lovelace (exemple)

```yaml
type: vertical-stack
cards:
  - type: glance
    title: Filtration Piscine
    entities:
      - entity: sensor.pool_filtration_mode
        name: Mode
      - entity: sensor.pool_filtration_duree_journaliere
        name: Durée aujourd'hui
      - entity: sensor.pool_filtration_duree_cible
        name: Objectif

  - type: gauge
    entity: sensor.pool_filtration_duree_journaliere
    name: Progression filtration
    min: 0
    max: 720 # 12h en minutes
    severity:
      green: 0
      yellow: 300
      red: 600

  - type: entities
    title: Contrôles
    entities:
      - entity: select.pool_filtration_mode
      - entity: switch.pool_filtration_forcage_manuel
```

---

## Dépannage

**La pompe ne démarre pas malgré du solaire disponible**
→ Vérifier que la production dépasse le seuil configuré (défaut 500W)
→ Vérifier que l'heure actuelle est dans la plage autorisée

**Les compteurs ne se remettent pas à zéro**
→ Le reset se fait automatiquement à minuit. Vérifier les logs HA pour `Daily reset`

**Erreur `entity_not_found`**
→ Les entités doivent exister dans HA avant la configuration de l'intégration

---

## Licence

MIT — Libre d'utilisation et de modification.
