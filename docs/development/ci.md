# CI-Prüfungen und Auswertung

Die Workflows unter `.github/workflows/` prüfen Pull Requests nach `main`, Pushes auf `main` und manuelle Aufrufe. Änderungen an der Anwendung werden nicht automatisch veröffentlicht oder bereitgestellt.

## Verpflichtende und beratende Prüfungen

| Bereich | Verpflichtend | Beratend |
|---|---|---|
| Frontend | `npm ci`, Prettier für `src/`, Typprüfung, Vitest, Produktions-Build | ESLint |
| Backend | Django-Systemprüfung, Ruff `E9,F63,F7,F82,F821,F811`, Ruff-Formatprüfung, Django-Tests | Breite Ruff-Regeln einschließlich B/S |
| Infrastruktur | Compose-Konfigurationsprüfung | – |
| Secrets | Gitleaks | – |
| Abhängigkeiten | – | Python mit pip-audit; Frontend-Lockdatei mit npm audit einschließlich Entwicklungswerkzeugen |
| PR-Metadaten | Conventional-Commit-Titel | – |
| CodeQL | Eigener Workflow ohne Fehlerunterdrückung | Nicht erfolgreich validiert, solange Code Scanning nicht verfügbar ist |

Die Formatter prüfen den Bestand mit den versionierten Einstellungen. Die Frontend-Prüfung verwendet die mit `npm ci` installierte Prettier-Version. Für Python verwendet die CI die festgelegte Ruff-Version und die Ausschlüsse aus `ruff.toml`. Ein Formatverstoß lässt den jeweiligen CI-Job fehlschlagen. Ob dieser Status einen Merge verhindert, hängt von den Repository-Schutzregeln ab.

Die breitere Regelprüfung bleibt beratend, weil sie Befunde enthält, die einzeln bewertet werden müssen. Beratende Prüfungen verwenden `continue-on-error`.

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

Formatbefunde lassen sich lokal mit `npm run format` aus `frontend/` und `ruff format .` aus der Repository-Wurzel korrigieren. Danach den Diff prüfen und die Prüfkommandos erneut ausführen. Prettier behält die Zeilenendungen des ausgecheckten Textes bei, sodass Git unter Windows und Linux unterschiedliche Zeilenenden verwenden kann.

## Fehlgeschlagene Läufe und Berichte

Zuerst Commit, Lauf-ID, Job und fehlgeschlagenen Schritt zuordnen. Beratende Befunde getrennt von verpflichtenden Fehlern auswerten. Installation, Typprüfung und Build können vor dem Testschritt scheitern; dann gibt es keinen Testbericht.

Vitest erzeugt `frontend-tests` mit einem JUnit-Bericht. Coverage erzeugt `backend-coverage` mit XML und JSON auch nach fehlgeschlagenen Tests, sofern verwertbare Coverage-Daten vorhanden sind. Der Testschritt bleibt dabei fehlgeschlagen. Bei Abbruch oder fehlenden Daten kann kein vollständiger Bericht garantiert werden. Die Artefakte werden für 90 Tage angefordert; Repository- und Organisationsgrenzen gelten zusätzlich. Für die Abschlussarbeit Berichte und Laufmetadaten zeitnah außerhalb der kurzlebigen Actions-Artefakte sichern.

Ein grüner CI-Lauf bedeutet weder vollständige Testabdeckung noch erfolgreiches Deployment. CodeQL ist getrennt zu bewerten. Laufzeiten nur mit Runner, Datum und Konfiguration vergleichen; einzelne Läufe belegen keine typische Leistung.

## Kontrollierte Negativtests

Fehler nur in einem separaten Validierungsbranch oder einer temporären Kopie einbringen und anschließend vollständig zurücknehmen. Geeignete Fälle sind ein TypeScript-Typfehler, eine fehlschlagende Testassertion, ein undefinierter Python-Name, eine fehlschlagende Django-Assertion und eine ungültige Compose-Eigenschaft. Für jeden Fall Ausgangscommit, genaue Änderung, erwarteten Fehler, tatsächlichen Status und Log sichern. Für Secret-Scans ausschließlich einen künstlichen, nicht funktionsfähigen Kontrollwert verwenden; niemals echte Zugangsdaten einbringen.

Die Liste ist ein Prüfplan, kein Nachweis bereits durchgeführter Tests. Sicherheitsbefunde, CodeQL-Verfügbarkeit und Merge-Schutz benötigen eigene Nachweise. Release, SBOM, Backup und Deployment bleiben separate offene Arbeitspakete.


## Abhängigkeitsberichte

Die zwei getrennten beratenden Auditjobs erzeugen JSON-Rohberichte, eine Zusammenfassung und Kontextdateien mit Werkzeugversionen sowie Prüfsummen der Eingabedateien. Die Artefakte heißen `python-dependency-audit` und `frontend-dependency-audit`; angeforderte Aufbewahrung: 90 Tage. Die Berichte werden auch bei Befunden oder Scannerfehlern hochgeladen, soweit Dateien vorhanden sind. Der jeweilige Job bleibt bei Fehlern rot. Ein grüner Gesamtworkflow bedeutet keine Freigabe der Befunde.

`npm audit --package-lock-only --include=dev --json` prüft die vorhandene Lockdatei ohne Paketinstallation oder Korrektur. Entwicklungsabhängigkeiten werden ausdrücklich einbezogen. Das Ergebnis beschreibt den Abhängigkeitsbaum, nicht die tatsächlich im Browser ausgeführten Komponenten. `pip-audit` prüft die versionierte `requirements.txt`. Die Anzahlen beider Werkzeuge sind nicht direkt vergleichbar: npm nennt betroffene Pakete einschließlich abgeleiteter Befunde, pip-audit Paket-Advisory-Paare. Die Zusammenfassung hält beides getrennt; Alias-Kennungen werden nicht als zusätzliche unabhängige Schwachstellen gezählt.

`scripts/summarize_dependency_audits.py` liefert Status 0 für einen unauffälligen Bericht, 1 für Befunde und 2 für fehlende, unvollständige oder fehlerhafte Berichte. Übersprungene Python-Abhängigkeiten gelten als unvollständige Prüfung. Acht Vertragstests prüfen unter anderem Scannerfehler, fehlende Lockdatei-Einträge, Paketversionen und die Unterscheidung von Paket-Advisory-Paaren und eindeutigen Kennungen. Eine bereits fehlgeschlagene Scanner-Ausführung wird am Jobende nicht durch einen erfolgreichen Bericht überschrieben.

Befunde sind zunächst offen. Für eine Behebung sind Advisory, betroffene Version, Abhängigkeitsweg, mögliche Laufzeit-/Build-Nutzung und vorgeschlagene Fixversion zu prüfen. Anschließend gezielt aktualisieren und Regressionstests ausführen. npm-Fixvorschläge können auch größere oder rückwärts gerichtete Versionswechsel enthalten; deshalb kein ungeprüftes `npm audit fix --force`. Ein Dev-Paket ist nicht automatisch risikofrei: Auch Build- und CI-Prozesse verarbeiten Code und Eingaben.

Es gibt derzeit keine genehmigte pauschale Ausnahme oder behauptete vollständige Sicherheitsfreigabe. Ein späterer Ausnahmeeintrag braucht konkrete Kennung, Begründung, zuständige Person und erneuten Prüftermin. Fehlende CVSS-Daten werden nicht erfunden. Zur Auswahl von Aktualisierungen ist ein gesonderter, getesteter Änderungssatz erforderlich.

Die [Befundauswertung vom 03.11.2026](dependency-findings-2026-11-03.md) ordnet den ersten vollständigen npm-/Python-Audit ein. Sie bleibt eine datierte Momentaufnahme.

