# Architecture — Smart Pool Filtration Manager

## Vue d'ensemble

```
pool_filtration/
├── __init__.py          # Point d'entrée, setup/unload de l'intégration
├── manifest.json        # Métadonnées HA (version, dépendances, iot_class)
├── const.py             # Constantes, table T°→durée, noms d'entités
├── coordinator.py       # Cerveau : logique de décision, accumulation runtime, persistance
├── config_flow.py       # UI de configuration (étape initiale + options)
├── sensor.py            # 4 capteurs de diagnostic
├── switch.py            # Switch de forçage manuel
├── select.py            # Sélecteur de mode
├── strings.json         # Traductions (référence)
└── translations/
    └── fr.json          # Traduction française
```

## Cycle de vie

```
HA démarre
    └─► async_setup_entry()         (__init__.py)
            ├─► async_load_state()  (coordinator) ← restaure runtime depuis .storage
            ├─► async_config_entry_first_refresh()
            └─► forward_entry_setups → sensor / switch / select

Toutes les 60s
    └─► _async_update_data()        (coordinator)
            ├─► _check_daily_reset()
            ├─► lire capteurs (T°, solaire, réseau)
            ├─► _should_pump_run()  ← décision centrale
            ├─► _set_pump(on/off)   ← appel service switch HA
            └─► _save_state()       ← persistance .storage
```

## Logique de décision (_should_pump_run)

```
┌─────────────────────────────────────────────┐
│              _should_pump_run()             │
├─────────────────────────────────────────────┤
│ MODE_MANUAL  → retourne _manual_override    │
│ MODE_OFF     → False                        │
│ quota atteint (runtime ≥ cible) → False     │
│ hors plage horaire → False                  │
│                                             │
│ MODE_SOLAR   → True si solaire ≥ seuil      │
│                                             │
│ MODE_AUTO    → True si solaire ≥ seuil      │
│               sinon : calcule si la prod    │
│               solaire restante suffira      │
│               → True si besoin réseau       │
└─────────────────────────────────────────────┘
```

## Persistance

Les données journalières sont sauvegardées dans `.storage/pool_filtration_data` via `homeassistant.helpers.storage.Store`. Au redémarrage de HA, si la date stockée correspond à aujourd'hui, les compteurs sont restaurés.

## Entités exposées

| Entité | Type | Description |
|--------|------|-------------|
| `sensor.*_daily_runtime` | Sensor | Minutes filtrées aujourd'hui |
| `sensor.*_target_duration` | Sensor | Durée cible calculée depuis T° |
| `sensor.*_solar_contribution` | Sensor | Minutes filtrées sur énergie solaire |
| `sensor.*_mode` | Sensor | Mode actif + attributs détaillés |
| `select.*_mode` | Select | Choix du mode (Auto/Solaire/Manuel/Arrêt) |
| `switch.*_manual_override` | Switch | Forçage pompe ON (passe en mode Manuel) |
