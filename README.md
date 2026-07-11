<div align="center">

![alt text](images\bandeau_filtration_piscine.png)


# 🏊 Smart Pool Filtration Manager — Custom Component Home Assistant


**Contrôle intelligent de la pompe de filtration de la piscine.**

![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.1+-blue.svg?logo=home-assistant)
[![Hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?logo=visual-studio-code&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?logo=python&logoColor=ffdd54)

[![GitHub release](https://img.shields.io/github/release/pvergezac/smartpoolfiltrationmanager.svg)](https://GitHub.com/pvergezac/smartpoolfiltrationmanager/releases/)
![GitHub Release Date](https://img.shields.io/github/release-date/pvergezac/smartpoolfiltrationmanager.svg?color=blue)
[![Github All Releases](https://img.shields.io/github/downloads/pvergezac/smartpoolfiltrationmanager/total.svg?color=blue&style=flat-square)]()
[![GitHub forks](https://img.shields.io/github/forks/pvergezac/smartpoolfiltrationmanager?style=flat-square)](https://GitHub.com/pvergezac/smartpoolfiltrationmanager/network/)
![GitHub Repo stars](https://img.shields.io/github/stars/pvergezac/SmartPoolFiltrationManager?style=flat-square)


</div>

---

## 📋 Description

**Smart Pool Filtration Manager** est une intégration personnalisée pour **Home Assistant** qui permet de controler la pompe de filtration de la piscine selon la **température de l'eau**, la **production solaire photovoltaïque**, la couleur du jour et plage horaire **EDF Tempo** (intégration RTE Tempo nécessaire) afin d'optimiser l'utilisation de l'energie solaire et des tarifs préférentiels, tout en privilégiant les autres besoins en energie de la maison.

---

## ✨ Fonctionnalités

- ⏱️ **Durée calculée automatiquement** selon la règle T°/2 (ex : 24°C → 6h de filtration)
- ☀️ **Priorité solaire** : la pompe tourne en priorité quand les panneaux produisent suffisamment
- **Priorité ECS** : la chauffe du ballon ECS peut être priorisé si sa température est disponible (en option)
- **Seuils Marche/Arret pompe** : controle de la pompe en fonction de la puissance solaire et de la consomation réseau
- **Couleur TEMPO** : limite de consommation réseau en fonction de la couleur du jour TEMPO (en option)
- 🔋 **Complétion intelligente** : si la production solaire ne suffit pas, complète sur le réseau en fin de journée
- 📊 **Suivi journalier** : durée filtrée, contribution solaire, progression
- 🔧 **4 modes de fonctionnement** : Automatique, Solaire uniquement, Manuel, Arrêt forcé
- 💾 **Persistance** : les compteurs survivent aux redémarrages de HA

---

## 📦 Installation via HACS (recommandé)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pvergezac&repository=SmartPoolFiltrationManager=integration)

### Prérequis

- Home Assistant version 2025.2.4 ou supérieure
- [HACS installé](https://hacs.xyz/docs/setup/download) sur votre instance Home Assistant

### Étape 1 — Ajouter le dépôt personnalisé dans HACS

> HACS ne référence pas encore ce dépôt par défaut. Ajoutez-le manuellement.

1. Dans Home Assistant, ouvrez **HACS** dans la barre latérale
2. Cliquez sur les **⋮** (trois points) en haut à droite
3. Sélectionnez **Dépôts personnalisés**
4. Dans le champ **Dépôt**, saisissez l'URL du dépôt GitHub :
   ```
   https://github.com/pvergezac/SmartPoolFiltrationManager
   ```
5. Dans **Catégorie**, sélectionnez **Intégration**
6. Cliquez sur **Ajouter**

### Étape 2 — Installer l'intégration

1. Toujours dans HACS, allez dans **Intégrations**
2. Cliquez sur **+ Explorer et télécharger des dépôts**
3. Recherchez **Smart Pool Filtration Manager**
4. Cliquez sur le résultat puis sur **Télécharger**
5. Confirmez en cliquant sur **Télécharger** dans la fenêtre de confirmation

### Étape 3 — Redémarrer Home Assistant

Après l'installation, un redémarrage est nécessaire :

**Paramètres → Système → Redémarrer → Redémarrer Home Assistant**

Attendez que Home Assistant soit complètement redémarré avant de continuer.

## 🔧 Installation Manuel

1. Copier le dossier `custom_components/smartpoolfiltmgr/` dans votre dossier `config/custom_components/`
2. Redémarrer Home Assistant

---

## ⚙️ Configuration

### Étape 1 — Si vous n'avez pas de sonde de température piscine

Si vous n'avez pas de sonde de température de l'eau de la piscine, vous pouvez la remplacer par une entité de capteur fictif, basée sur une entrée numerique.

Ajouter le code suivant dans le fichier **configuration.yml** de Home Assistant.

```
# Entités fictives pour tester sans vrai matériel
template:
  - sensor:
      - name: "Temperature Piscine (simulée)"
        state: "{{ states('input_number.pool_temperature_simu') }}"
        unit_of_measurement: "°C"
        device_class: temperature

input_number:
  pool_temperature_simu:
    name: "Température de la piscine (simulée)"
    initial: 28
    min: 10
    max: 35
    step: 1
```
Selectionner le capteur **Temperature Piscine (simulée)** lors de la configuration de l'intégration à l'étape suivante.

Ajouter également l'entré nurérique dans votre Dashboard de contrôle de la filtration. Le changement de mode de filtration ré-actualise le calcul de la durée cible.


### Étape 2 — Ajouter l'intégration

**Paramètres → Appareils et services → Ajouter une intégration → Smart Pool Filtration Manager**

Renseignez :
| Champ                | Description  | Exemple |
|----------------------|------------- |---------|
| Switch de la pompe   | Entité switch qui allume/éteint la pompe | `switch.pompe_piscine` |
| Température de l'eau | Capteur de température dans le bassin | `sensor.temperature_piscine` |
| Production solaire   | Capteur de puissance instantanée des panneaux (W) | `sensor.solaire_puissance` |
| Consommation réseau  | Capteur de puissance consommée sur le réseau | `sensor.consommation_reseau` |
| Couleur Tempo        | Entité couleur Tempo (optionnel) | `sensor.rte_tempo_couleur_actuelle` |
| Heures crause        | Entité Heures Creuses Tempo (optionnel) | `binary_sensor.rte_tempo_heures_creuses` |
| Température ballon   | Capteur de température du ballon ECS (optionnel) | `sensor.temperature_ballon` |

### Étape 3 — Options avancées

Accessible via le bouton **Configurer** sur la carte de l'intégration :

| Option                      | Défaut     | Description                                   |
| --------------------------- | ---------- | --------------------------------------------- |
| Heure de réinitialisation   | 6 h        | la journée de filtration (fin des HC de nuit) |
| Durée minimale/jour         | 2 h        | Garantie même si température froide           |
| Durée maximale/jour         | 12 h       | Plafond absolu                                |
| Plage solaire - début       | 8 h        | Début de la filtration sur production solaire |
| Plage solaire - fin         | 20 h       | Fin de la filtration sur production solaire   |
| Puiss solaire min           | 500 W      | Solaire minimum pour autoriser la pompe       |
| Temp Ballon ECS min         | 40°        | Temp ballon minimum pour autoriser la pompe   |
| Hystérésis ECS              | 2°         | Ecart min pour éviter les oscilations         |
| Conso max démarrage pompe   | 50 W       | Seuil de démarrage                            |
| Conso max arret pompe       | 500 W      | Seuil conso max (jour BLEU ou sans TEMPO)     |
| Conso max arret pompe BLANC | 100 W      | Seuil conso max (jour BLANC)                  |
| Conso max arret pompe       | 50 W       | Seuil conso max (jour ROUGE)                  |
|                             |            |                                               |
| Plage compl réseau - début  | 22 h       | Début de complément de filtration (nuit)      |
| Plage solaire - fin         | 6 h        | Fin de complément de filtration (nuit)        |
| Complément réseau           | ✅         | Validé (jour BLEU ou sans TEMPO)              |
| Complément réseau BLANC     | ❌         | Validé (jour BLANC)                           |
| Complément réseau ROUGE     | ❌         | Validé (jour ROUGE)                           |

---

## Entités créées

### Capteurs

| Entité                                        | Description                                  |
| --------------------------------------------- | -------------------------------------------- |
| `sensor.pool_filtration_duree_journaliere`    | Minutes de filtration effectuées aujourd'hui |
| `sensor.pool_filtration_duree_cible`          | Durée cible de filtration, calculée selon T° de l'eau       |
| `sensor.pool_filtration_contribution_solaire` | Minutes filtrées grâce au solaire            |
| `sensor.pool_filtration_mode`                 | Mode actif + état détaillé                   |
| `sensor.pool_filtration_water_temp`           | Température de l'eau de la piscine                          |
| `sensor.pool_filtration_water_heater`         | Température du ballon ECS                       |

### Contrôles

| Entité                                  | Description                                                |
| --------------------------------------- | ---------------------------------------------------------- |
| `select.pool_filtration_mode`           | Sélecteur de mode (Automatique / Solaire / Manuel / Arrêt) |
| `switch.pool_filtration_forcage_manuel` | Force la pompe ON (passe en mode Manuel)                   |

---

## Logique de décision

```
Toutes les 5 minutes :
│
├─ Mode MANUEL ?     → respecter l'état du switch de forçage manuel
├─ Mode ARRÊT ?      → pompe OFF
├─ Quota atteint ?   → pompe OFF (durée cible dépassée)
├─ Hors plage horaire ? → pompe OFF
│
├─ Plage solaire (en Mode SOLAIRE ou AUTO)
│   ├─ Production < seuil → pompe OFF
│   ├─ Température ballon ECS < seuil priorité → pompe OFF
│   ├─ Durée réalisée >= durée cible → pompe OFF
│   ├─ Consomation < seuil de démarrage → pompe ON ☀️
│   └─ Consomation > seuil d'arret (suivant couleur TEMPO) → pompe OFF
│
└─ Plage complementaire (en Mode AUTO) :
    ├─ Complement non autorisé pour la couleur du jour → pompe OFF
    └─ Durée réalisée < durée cible → pompe ON (réseau) 🔌
```
### Cas d'utilisation conjointe d'un routeur solaire

Si comme moi, vous utilisez un **routeur solaire\*** pour chauffer votre ballon ECS, le réglage des differents seuils de consommation et production est particuliairement important pour une bonne optimisation et la stabilité de fonctionnement.

En effet, le fonctionnement du routeur *"fausse en partie la mesure de consomation"*, en faisant apparaitre une consomation de la maison nulle ou inférueure à la réalité, si il y a du soleil, alors que le ballon ECS est en chauffe. Le réglage des seuils de consommation de démarrage et d'arret sont alors particulierement pointus.

En été, le fonctionnement de la pompe de filtration dans la journée est prioritaire sur celle du ballon ECS. En selectionnant un seuil de consomation pour le démarrage de la pompe faible mais positif (50 à 100w), le routeur conserve sont fonctionnement, mais n'est pas priorisé. Pour éviter de démarrer la pompe trop taux et une consommation sur le réseau, il est nécessaire de relever le seuil de production solaire minumun pour que la production puisse alimenté au moins partiellement la pompe (exemple 800W pour une pompe de 1000W). En acceptant une legère consommation sur le réseau (1/4 à 1/2 de la puissance de la pompe) l'intégration et le routeur pourront jouer pleinement leurs role Il en résultera une faible consommation sur le reseau, mais demarrera la filtration bien plus taux au levé du soleil.

**\* Voir le projet** : [MSunPV Intégration](https://github.com/pvergezac/MSunPVIntegration) pour le routeur solaire de [Ard-Tek](https://ard-tek.com/)


### Table de durée selon température

| Température | Durée de filtration |
| ----------- | ------------------- |
| ≤ 10°C      | 1 h                 |
| 15°C        | 2 h                 |
| 20°C        | 4 h                 |
| 24°C        | 6 h                 |
| 28°C        | 9 h                 |
| 30°C        | 15 h                |
| >35°C       | 24 h                |

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

Mon tableau de bord

![alt text](images\image.png)

```
views:
  - type: masonry
    title: Piscine
    path: piscine
    cards:
      - show_current: true
        show_forecast: false
        type: weather-forecast
        entity: weather.forecast_st_cyprien
        forecast_type: daily
      - type: entities
        entities:
          - entity: >-
              select.smart_pool_filtration_manager_pool_filtration_mode_de_fonctionnement
          - entity: >-
              switch.smart_pool_filtration_manager_pool_filtration_forcage_manuel
            name: Forçage manuel
            icon: mdi:debug-step-over
          - entity: switch.smart_plug_outlet
            icon: mdi:power
            name: Pompe piscine
            secondary_info: last-changed
          - entity: sensor.temperature_piscine_simulee
          - entity: sensor.smart_pool_filtration_manager_duree_cible_filtration
            name: Durée cible
            secondary_info: none
          - entity: sensor.smart_pool_filtration_manager_duree_filtration_realisee
            name: Durée réalisée
            secondary_info: last-updated
          - entity: sensor.smart_pool_filtration_manager_contribution_solaire
            name: Contribution solaire
          - entity: sensor.smart_pool_filtration_manager_pool_filtration_tempo
            name: Couleur TEMPO
          - entity: sensor.smart_plug_energy
            name: Consommé aujourd'hui
          - entity: input_number.pool_temperature_simu
        title: Filtration Piscine
        show_header_toggle: false
        state_color: false
```

---

## 🛠️ Dépannage

**La pompe ne démarre pas malgré du solaire disponible**
- Vérifier que l'heure actuelle est dans la plage solaire autorisée
- Vérifier que la production dépasse le seuil configuré (défaut 500W)
- Vérifier que la température du ballon ECS est supérieure au seuil de priorisation (défaut 40°)
- Vérifier que la consomation réseau est inférieure aux seuils de démarrage et d'arret de la pompe

**La pompe alterne entre arret et démarre toutes les 5mn, en plage solaire**
- augmenter le seuils de consommation d'arret, en tenant compte de la puissance de la pompe
- augmenter le seul de production solaire minimun, ou ajuster le seuil de démarrage

**Les compteurs ne se remettent pas à zéro**
→ Le reset se fait automatiquement à l'heure choisie. Vérifier les logs HA pour `Daily reset`

**Erreur `entity_not_found`**
→ Les entités doivent exister dans HA avant la configuration de l'intégration

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour signaler un bug ou proposer une amélioration, ouvrez une [issue](https://github.com/pvergezac/SmartPoolFiltrationManager/issues) sur GitHub.

---

## 📄 Licence

Ce projet est distribué sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">
Fait avec ❤️ pour la communauté Home Assistant francophone

Si vous aimez ce projet, ajouter une ⭐ étoile sur [Github](https://github.com/pvergezac/SmartPoolFiltrationManager)
</div>