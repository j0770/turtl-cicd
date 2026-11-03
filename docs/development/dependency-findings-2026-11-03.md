# Abhängigkeitsbefunde – 03.11.2026

Status: offen; keine pauschale Risikoakzeptanz und keine behobenen Befunde behauptet. Lauf [41697228419](https://github.com/j0770/turtl-cicd/actions/runs/41697228419), Commit `8b52057af98718d75c57a6e7b0be97f2a3e2e64a`. Die JSON-Artefakte und Eingabeprüfsummen sind die maßgeblichen Nachweise. Werkzeugdatenbanken ändern sich; dies ist eine Momentaufnahme.

## Messbereich und Zählung

npm: 38 betroffene Pakete; 26 moderat, elf hoch, eines kritisch. Enthalten sind direkte, transitive und Entwicklungsabhängigkeiten. Paketstufen können aus Abhängigkeiten übernommen sein und sind keine Anzahl unabhängiger CVEs.

pip-audit: 14 betroffene Pakete, 108 Paket-Advisory-Paare und 73 unterschiedliche primäre Kennungen. Letzteres ist keine unabhängig geprüfte Zahl verschiedener Schwachstellen. Aliase werden nicht zusätzlich gezählt. Der Bericht liefert keine durchgängigen Schweregrade; sie werden hier nicht ergänzt.

## Zuerst zu prüfende Aktualisierungen

1. **Build-/CI-Abhängigkeit shell-quote:** Lockversion 1.8.4, als Dev-Abhängigkeit markiert. Der kritische Befund GHSA-pqg4-j6r4-53mv betrifft quote(); der veröffentlichte Fix ist 1.11.0. Die Nutzung durch npm-run-all und der Umgang mit unkontrollierten Argumenten sind vor einer Risikoentscheidung zu prüfen. Dev-Abhängigkeiten sind nicht automatisch ungefährlich. [Advisory](https://github.com/advisories/GHSA-pqg4-j6r4-53mv).
2. **Direkte Frontend-Abhängigkeiten Axios und Vue:** Axios 1.17.0 wird in APIRequests.ts verwendet. Die einzelnen Adapter und Voraussetzungen der Advisories müssen getrennt betrachtet werden. Beispiel GHSA-gcfj-64vw-6mp9 betrifft den Node-HTTP-Adapter; die Browsernutzung belegt dessen Erreichbarkeit nicht. Vue erhält im npm-Bericht unter anderem einen abgeleiteten Befund über den Server-Renderer. main.ts startet eine Browseranwendung mit createApp; eine tatsächliche SSR-Erreichbarkeit ist damit nicht nachgewiesen. Keine dieser Feststellungen ersetzt die Prüfung weiterer Befunde. [Axios-Advisory](https://github.com/advisories/GHSA-gcfj-64vw-6mp9).
3. **Backend-Framework und Serverkette:** Django, DRF, Daphne sowie Twisted/Autobahn und die Authentifizierungsabhängigkeiten priorisiert auf Upgradepfade prüfen. requirements.in begrenzt Django auf <5.3 und DRF auf <3.16. Die gemeldeten DRF-Fixversionen liegen außerhalb dieser bisherigen Grenze. Ein bloßes Neuberechnen der Lockdatei löst diesen Zielkonflikt nicht; es braucht eine geprüfte Anpassung der Vorgaben und Regressionstests.
4. **Weitere direkte und transitive Pakete:** Die nachfolgenden Tabellen und Rohberichte abarbeiten. npm-Fixvorschläge mit Major-Wechsel oder rückwärts gerichteter Zielversion nicht ungeprüft übernehmen. Keine automatischen Änderungen an package-lock.json, requirements.txt oder requirements.in wurden vorgenommen.

Die Reihenfolge ist eine Arbeitspriorisierung aus Scanner-Schweregrad, deklarierter Nutzung und Upgrade-Konflikten. Sie ist keine Ausnutzbarkeitsbewertung. Verantwortliche und Freigaben werden nicht erfunden.

## npm-Paketübersicht

| Paket | Lockversion(en) | Direkt | Nur Dev-Instanzen laut Lock | Scannerstufe |
|---|---|---|---|---|
| @eslint-community/eslint-utils | 4.9.1 | nein | ja | moderate |
| @eslint/eslintrc | 2.1.4 | nein | ja | moderate |
| @humanwhocodes/config-array | 0.13.0 | nein | ja | moderate |
| @typescript-eslint/eslint-plugin | 5.62.0 | nein | ja | moderate |
| @typescript-eslint/parser | 5.62.0 | nein | ja | moderate |
| @typescript-eslint/type-utils | 5.62.0 | nein | ja | moderate |
| @typescript-eslint/utils | 5.62.0 | nein | ja | moderate |
| @vitest/mocker | 4.1.8 | nein | ja | moderate |
| @vue/eslint-config-prettier | 7.1.0 | ja | ja | moderate |
| @vue/eslint-config-typescript | 11.0.3 | ja | ja | moderate |
| @vue/server-renderer | 3.5.35 | nein | nein / gemischt | high |
| axios | 1.17.0 | ja | nein / gemischt | high |
| brace-expansion | 1.1.15, 2.1.1 | nein | ja | high |
| editorconfig | 1.0.7 | nein | ja | moderate |
| esbuild | 0.21.5 | nein | nein / gemischt | moderate |
| eslint | 8.57.1 | ja | ja | moderate |
| eslint-config-prettier | 8.10.2 | nein | ja | moderate |
| eslint-plugin-prettier | 4.2.5 | nein | ja | moderate |
| eslint-plugin-vue | 9.33.0 | ja | ja | moderate |
| file-entry-cache | 6.0.1 | nein | ja | moderate |
| flat-cache | 3.2.0 | nein | ja | moderate |
| follow-redirects | 1.16.0 | nein | nein / gemischt | high |
| form-data | 4.0.5 | nein | nein / gemischt | high |
| glob | 10.5.0, 7.2.3 | nein | ja | moderate |
| js-beautify | 1.15.4 | nein | ja | moderate |
| js-yaml | 4.2.0 | nein | ja | high |
| minimatch | 3.1.5, 9.0.9 | nein | ja | moderate |
| nanoid | 3.3.12 | nein | nein / gemischt | high |
| npm-run-all | 4.1.5 | ja | ja | moderate |
| postcss | 8.5.15 | nein | nein / gemischt | high |
| postcss-selector-parser | 6.1.2 | nein | ja | moderate |
| rimraf | 3.0.2 | nein | ja | moderate |
| shell-quote | 1.8.4 | nein | ja | critical |
| source-map-js | 1.2.1 | nein | nein / gemischt | high |
| vite | 5.4.21, 8.0.16 | ja | nein / gemischt | high |
| vitest | 4.1.8 | ja | ja | moderate |
| vue | 3.5.35 | ja | nein / gemischt | high |
| vue-eslint-parser | 9.4.3 | nein | ja | moderate |

Die Dev-Markierung stammt aus der Lockdatei. Sie ist weder ein Beleg für die tatsächlich gebündelten Dateien noch für den Ausschluss eines Angriffswegs.

## Python-Paketübersicht

| Paket | Version | Direkt in requirements.in | Advisory-Paare | Gemeldete Fixversionen, nicht als gemeinsames Upgradeziel validiert |
|---|---|---|---|---|
| autobahn | 25.12.2 | nein | 1 | 26.7.1 |
| certifi | 2026.4.22 | nein | 2 | 2026.10.18 |
| msgpack | 1.1.2 | nein | 3 | 1.2.1, 1.2.3 |
| cryptography | 47.0.0 | nein | 7 | 48.0.1, 49.0.0, 50.0.0 |
| daphne | 4.2.1 | ja | 4 | 4.2.2 |
| django | 5.2.13 | ja | 25 | 5.2.14, 5.2.15, 5.2.16, 5.2.17, 6.0.5, 6.0.6, 6.0.7, 6.0.8, 6.1.1 |
| djangorestframework | 3.15.2 | ja | 5 | 3.17.2, 3.18.2 |
| idna | 3.13 | nein | 2 | 3.15 |
| pyasn1 | 0.6.3 | nein | 10 | 0.6.4, 0.6.5 |
| pyjwt | 2.12.1 | nein | 19 | 2.13.0, 2.14.0, 2.15.0 |
| urllib3 | 2.6.3 | nein | 7 | 2.7.0, 2.8.0 |
| sqlparse | 0.5.5 | nein | 9 | 0.6.0 |
| twisted | 25.5.0 | nein | 10 | 26.10.0rc1, 26.4.0, 26.4.0rc2 |
| ujson | 5.12.0 | nein | 4 | 5.12.1, 5.13.0 |

Die Vereinigung der Fixversionen löst nicht zwangsläufig alle Befunde gleichzeitig. Einzelne Advisories, Versionsgrenzen und Kompatibilität müssen vor einem Upgrade geprüft werden.

## Durchgeführte Prüfung und offene Arbeit

Die Berichtsauswertung wurde mit acht lokalen Vertragstests und im Auditjob geprüft. Befunde führen zu Status 1, fehlende/unvollständige/fehlerhafte Daten zu Status 2. Die Auditjobs bleiben beratend und ihre fehlgeschlagenen Schritte sichtbar. JSON-Rohberichte, Zusammenfassungen und Kontextdateien werden auch bei Befunden gesichert.

Nicht durchgeführt: Paketaktualisierung, Exploitversuch, vollständige Erreichbarkeitsanalyse, Behebung oder fachliche Risikoakzeptanz. Nach einer gezielten Aktualisierung sind Lockdiff, Audit, Typprüfung, zwölf Frontend-Tests, Build und 14 Backend-Tests erneut zu prüfen. CodeQL-Verfügbarkeit bleibt ein separates Repository-Problem.

Werkzeuggrundlagen: [npm audit](https://docs.npmjs.com/cli/v11/commands/npm-audit/), [pip-audit](https://github.com/pypa/pip-audit). Die verlinkten Advisory-/Werkzeugquellen wurden am 03.11.2026 geprüft; die übrigen Einträge stammen direkt aus den gesicherten Scannerberichten.
