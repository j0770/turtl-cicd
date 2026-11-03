# CI-Prüfungen und Auswertung

Die Workflows unter `.github/workflows/` prüfen Pull Requests nach `main`, Pushes auf `main` und manuelle Aufrufe. Änderungen an der Anwendung werden nicht automatisch veröffentlicht oder bereitgestellt.

## Verpflichtende und beratende Prüfungen

| Bereich | Verpflichtend | Beratend |
|---|---|---|
| Frontend | `npm ci`, Typprüfung, Vitest, Produktions-Build | Prettier und ESLint |
| Backend | Django-Systemprüfung, Ruff `E9,F63,F7,F82,F821,F811`, Django-Tests | Breite Ruff-Regeln einschließlich B/S sowie Formatierung |
| Infrastruktur | Compose-Konfigurationsprüfung | – |
| Secrets | Gitleaks | – |
| Abhängigkeiten | – | Python-Abhängigkeiten mit pip-audit |
| PR-Metadaten | Conventional-Commit-Titel | – |
| CodeQL | Eigener Workflow ohne Fehlerunterdrückung | Nicht erfolgreich validiert, solange Code Scanning nicht verfügbar ist |

Beratende Prüfungen verwenden `continue-on-error`. Ihr Befund ist weiterhin zu bearbeiten und kein erfolgreicher Test. Die bestehende Formatierung wird nicht pauschal verändert. Die B-Regeln bleiben vorerst beratend, weil sie im übernommenen Code bekannte Befunde melden. Diese Entscheidung hebt den verpflichtenden Teststatus nicht auf. Ob ein fehlgeschlagener Check einen Merge verhindert, hängt zusätzlich von den Repository-Schutzregeln ab.

## Lokal prüfen

Node.js 24 und Python 3.12 verwenden. Aus `frontend/`:

```sh
npm ci
npm run format:check
npm run lint:check
npm run type-check
npm run test:ci
npm run build-only
```

Die Check-Befehle verändern keine Quelldateien. `npm run lint` und `npm run format` sind dagegen bestehende Korrekturbefehle und dürfen nicht mit Prüfbefehlen verwechselt werden. Vitest scheitert bei fehlenden Tests; `passWithNoTests` wird nicht verwendet. Die ersten API-Tests prüfen Fehlerklassen, öffentliche und authentifizierte Anfragen sowie Token-Erneuerung und deren Abbruch. HTTP-Client, Store und Router sind dabei simuliert. Sie sind keine Browser- oder Backend-Integrationstests.

Für das Backend die Testumgebung gemäß Entwicklungsanleitung mit separater PostgreSQL-Datenbank und Redis einrichten. Keine Produktionsdatenbank verwenden. Dann aus der Repository-Wurzel:

```sh
python -m pip install -r requirements.txt
python -m pip install coverage==7.16.0 ruff==0.16.6
python manage.py check
ruff check --select E9,F63,F7,F82,F821,F811 .
ruff check .
ruff format --check .
coverage run --source=analytics,authentication,catalog,enrollments,seeder,shell,turtl,vm_manager manage.py test
coverage report --show-missing
coverage xml
coverage json
```

Die CI stellt PostgreSQL und Redis als Servicecontainer bereit. Test-Zugangsdaten im Workflow sind ausschließlich für diese kurzlebige Umgebung vorgesehen. Die Proxmox-bezogenen Backend-Tests ersetzen externe Aufrufe durch Mocks. Die Compose-Prüfung erzeugt nur Platzhalterdateien und startet keine Anwendung.

## Fehlgeschlagene Läufe und Berichte

Zuerst Commit, Lauf-ID, Job und fehlgeschlagenen Schritt zuordnen. Beratende Befunde getrennt von verpflichtenden Fehlern auswerten. Installation, Typprüfung und Build können vor dem Testschritt scheitern; dann gibt es keinen Testbericht.

Vitest erzeugt `frontend-tests` mit einem JUnit-Bericht. Coverage erzeugt `backend-coverage` mit XML und JSON auch nach fehlgeschlagenen Tests, sofern verwertbare Coverage-Daten vorhanden sind. Der Testschritt bleibt dabei fehlgeschlagen. Bei Abbruch oder fehlenden Daten kann kein vollständiger Bericht garantiert werden. Die Artefakte werden für 90 Tage angefordert; Repository- und Organisationsgrenzen gelten zusätzlich. Für die Abschlussarbeit Berichte und Laufmetadaten zeitnah außerhalb der kurzlebigen Actions-Artefakte sichern.

Ein grüner CI-Lauf bedeutet weder vollständige Testabdeckung noch erfolgreiches Deployment. CodeQL ist getrennt zu bewerten. Laufzeiten nur mit Runner, Datum und Konfiguration vergleichen; einzelne Läufe belegen keine typische Leistung.

## Kontrollierte Negativtests

Fehler nur in einem separaten Validierungsbranch oder einer temporären Kopie einbringen und anschließend vollständig zurücknehmen. Geeignete Fälle sind ein TypeScript-Typfehler, eine fehlschlagende Testassertion, ein undefinierter Python-Name, eine fehlschlagende Django-Assertion und eine ungültige Compose-Eigenschaft. Für jeden Fall Ausgangscommit, genaue Änderung, erwarteten Fehler, tatsächlichen Status und Log sichern. Für Secret-Scans ausschließlich einen künstlichen, nicht funktionsfähigen Kontrollwert verwenden; niemals echte Zugangsdaten einbringen.

Die Liste ist ein Prüfplan, kein Nachweis bereits durchgeführter Tests. Sicherheitsbefunde, CodeQL-Verfügbarkeit und Merge-Schutz benötigen eigene Nachweise. Release, SBOM, Backup und Deployment bleiben separate offene Arbeitspakete.
