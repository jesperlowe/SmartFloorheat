# SmartFloorHeat (Home Assistant custom integration)

SmartFloorHeat er en custom integration til Home Assistant, distribueret via HACS.

## Repo-struktur (HACS-kompatibel)

Denne struktur er den forventede for en integration i HACS:

- `custom_components/smartfloorheat/` → integrationskode
- `hacs.json` → HACS metadata
- `README.md` → vises i HACS (`render_readme: true`)
- `.github/workflows/` → validering og release-flow

## Installation via HACS

1. HACS → **Integrations** → menu (⋮) → **Custom repositories**.
2. Tilføj dette repo som type **Integration**.
3. Søg efter **SmartFloorHeat** i HACS og installér.
4. Genstart Home Assistant.
5. Gå til **Settings → Devices & Services → Add integration** og vælg **SmartFloorHeat**.

## Release-flow

- Opret et tag med format `vX.Y.Z` (fx `v0.2.0`).
- Push tagget til GitHub.
- Workflowet `release.yml` opretter automatisk en GitHub Release.
- HACS følger tags/releases, så nye versioner kan opdateres i HACS.

## Lokal udvikling

Kør validering med Home Assistant tooling (fx `hassfest`) før release.
