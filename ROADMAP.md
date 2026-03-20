# ROADMAP - Frappe Claude Skill Package

> **📍 Dit is de SINGLE SOURCE OF TRUTH voor project status en voortgang.**
> Claude Project Instructies verwijzen hiernaar - geen dubbele tracking.

> **Laatste update**: 2026-03-20
> **Status**: V2.0 UPGRADE GEPLAND
> **V2 Tech Spec**: [frappe-skill-package-tech-spec-v2.md](docs/masterplan/frappe-skill-package-tech-spec-v2.md)
> **V2 Gap Analysis**: [frappe-skill-package-gap-analysis.md](docs/masterplan/frappe-skill-package-gap-analysis.md)
> **V1 Masterplan**: [erpnext-skills-masterplan-v4.md](docs/masterplan/erpnext-skills-masterplan-v4.md)
> **Structuur**: Engels-only, Anthropic-conform, V14/V15/V16 compatible

---

## V2.0 Upgrade — Frappe Framework Full Coverage

> **Doel**: Van 28 ERPNext-specifieke skills naar 53 Frappe Framework skills
> **Scope**: Rename + restructure + 25 nieuwe skills
> **Dekking**: ~16% → ~85% van het Frappe surface area

### V2 Status

| Categorie | Voltooid | Totaal |
|-----------|:--------:|:------:|
| Rename + frontmatter upgrade | 28 | 28 |
| Content upgrade bestaande skills | 0 | 28 |
| Nieuwe Syntax skills | 0 | 3 |
| Nieuwe Core skills | 0 | 4 |
| Nieuwe Impl skills | 0 | 5 |
| Nieuwe Ops skills | 0 | 8 |
| Nieuwe Agents | 0 | 3 |
| Nieuwe Testing skills | 0 | 2 |
| **TOTAAL v2.0** | **28** | **81** |

**V2 Progress**: ███░░░░░░░░░░░░░░░░░ **35%** — V2.2 Compleet

### V2 Fasen

| Fase | Beschrijving | Status |
|------|-------------|:------:|
| V2.1 | Gap analysis valideren | ✅ Compleet |
| V2.2 | Rename + frontmatter upgrade (28 skills) | ✅ Compleet |
| V2.3 | Directory herstructurering + 25 nieuwe stubs | ✅ Compleet |
| V2.4 | Content upgrade bestaande 28 skills (research + rewrite) | ⏳ Gepland |
| V2.5 | Nieuwe skills vullen (P0 → P1 → P2 → P3) | ⏳ Gepland |
| V2.6 | Validatie, README, repo rename, release | ⏳ Gepland |

### V2 Prioriteiten

| Prioriteit | Skills | Status |
|:----------:|--------|:------:|
| **P0** | doctypes, reports, workflow, testing, app-lifecycle | ⏳ |
| **P1** | notifications, ui-components, website, files, hooks-comprehensive | ⏳ |
| **P2** | bench, deployment, backup, performance, upgrades, frontend-build | ⏳ |
| **P3** | cloud, hosting, cache, integrations, architect, debugger, migrator | ⏳ |

---

## V1.x — Completed Releases

---

## Project Status

| Categorie | Voltooid | Totaal |
|-----------|:--------:|:------:|
| Research | 13 | 13 |
| Syntax Skills | 8 | 8 |
| Core Skills | 3 | 3 |
| Implementation Skills | 8 | 8 |
| Error Handling Skills | 7 | 7 |
| Agents | 2 | 2 |
| **TOTAAL Skills** | **28** | **28** |

**Skills**: ████████████████████ **100%** ✅  
**V16 Compatibility**: ████████████████████ **100%** ✅  
**Validation**: ████████████████████ **28/28 PASS** ✅  
**GitHub Community**: ██████████████████░░ **6/7** ✅

---

## Open Issues

| # | Titel | Prioriteit | Status |
|---|-------|:----------:|:------:|
| #14 | Repository topics toevoegen | 🟢 | Open (handmatig) |
| #15 | GitHub Community Standards | 🔴 | ✅ Compleet |

---

## ✅ Fase 8.8: GitHub Community Standards - COMPLEET

**Doel:** Repository klaarmaken voor public release met volledige GitHub community compliance.

### Score: 6/7 ✅

| Criterium | Status |
|-----------|:------:|
| README.md | ✅ |
| LICENSE | ✅ |
| CODE_OF_CONDUCT.md | ⏭️ Skipped |
| CONTRIBUTING.md | ✅ |
| SECURITY.md | ✅ |
| Issue Templates | ✅ |
| PR Template | ✅ |

### Substappen

| Stap | Bestand | Beschrijving | Status |
|------|---------|--------------|:------:|
| 8.8.1 | `CODE_OF_CONDUCT.md` | Contributor Covenant v2.1 | ⏭️ Skipped |
| 8.8.2 | `CONTRIBUTING.md` | Bijdrage richtlijnen | ✅ |
| 8.8.3 | `SECURITY.md` | Security vulnerability policy | ✅ |
| 8.8.4 | `CHANGELOG.md` | Versie geschiedenis (Keep a Changelog) | ✅ |
| 8.8.5 | `INSTALL.md` | Volledige installatie instructies | ✅ (exists) |
| 8.8.6 | `.github/ISSUE_TEMPLATE/bug_report.yml` | Bug report template | ✅ |
| 8.8.7 | `.github/ISSUE_TEMPLATE/feature_request.yml` | Feature request template | ✅ |
| 8.8.8 | `.github/ISSUE_TEMPLATE/config.yml` | Template configuratie | ✅ |
| 8.8.9 | `.github/PULL_REQUEST_TEMPLATE.md` | PR checklist | ✅ |

### Na Voltooiing
- [ ] Repository public maken (handmatig via GitHub UI)
- [ ] Topics toevoegen (Issue #14)
- [ ] Description toevoegen aan repo
- [ ] API tokens regenereren (security)

---

## Fase Overzicht

### ✅ Fase 1-7: v1.0 Release (Compleet)

Alle 28 skills en agents voltooid en gedocumenteerd.

### ✅ Fase 8.1-8.7: Post-release Verbeteringen (v1.1)

| Stap | Issue | Beschrijving | Status |
|------|:-----:|--------------|:------:|
| 8.1 | - | Kritische Reflectie | ✅ |
| 8.2 | #10, #4 | V16 skill updates | ✅ |
| 8.3 | - | Validatie & Testing | ✅ |
| 8.4 | #9 | Agent Skills review | ✅ |
| 8.5 | #5 | ~~Claude Code format~~ | ❌ Vervallen |
| 8.6 | #11 | How-to-use docs | ✅ |
| 8.7 | #12 | Final Polish & Release | ✅ |

### ✅ Fase 8.8: GitHub Community Standards (v1.2)

| Stap | Beschrijving | Status |
|------|--------------|:------:|
| 8.8.1 | CODE_OF_CONDUCT.md | ⏭️ Skipped |
| 8.8.2-8.8.4 | Community & Docs | ✅ |
| 8.8.5 | INSTALL.md | ✅ (exists) |
| 8.8.6-8.8.9 | Issue & PR Templates | ✅ |

**Fase 8 Voortgang**: ████████████████████ **100%** ✅

---

## Release History

### v1.2 (2026-01-18) - GitHub Ready ✅

- ✅ GitHub Community Standards compliance (6/7)
- ✅ Issue & PR templates
- ✅ CONTRIBUTING.md
- ✅ SECURITY.md
- ✅ CHANGELOG.md

### v1.1 (2026-01-18)

- ✅ V16 compatibility for all skills
- ✅ Agent Skills standard compliance
- ✅ Platform-specific usage guides (USAGE.md)
- ✅ Complete README overhaul
- ✅ Validation: 28/28 skills pass

### v1.0 (2026-01-17)

- 🎉 Initial release
- ✅ 28 skills and agents
- ✅ V14/V15 compatibility
- ✅ Full documentation

---

## Closed Issues

| # | Titel | Resolution |
|---|-------|:----------:|
| #4 | V16 compatibility review | ✅ Compleet |
| #5 | Claude Code native format | ❌ Niet meer nodig |
| #9 | Agent Skills standaard review | ✅ Compleet |
| #10 | V16 skill updates (9 skills) | ✅ Compleet |
| #11 | How-to-use documentatie | ✅ Compleet |
| #12 | Final Polish & v1.1 Release | ✅ Compleet |
| #15 | GitHub Community Standards | ✅ Compleet |

---

## Changelog

### 2026-03-20 (sessie 25) - V2.2 COMPLEET

**V2.0 Upgrade gestart:**
- Beslissingen D-016 t/m D-020 vastgelegd
- Research: hooks scope (95 hooks, split in 2 skills) + hosting setup (bench op Hetzner VPS)
- 28/28 skill directories hernoemd: `erpnext-*` -> `frappe-*`
- 64 bestanden bijgewerkt met nieuwe cross-referenties
- Alle YAML frontmatter geupgraded: MIT license, v2.0, Frappe v14-v16 compatibility
- Rename script: `tools/rename_skills.py`

**Status:** V2.2 compleet, V2.3 (directory herstructurering + stubs) is volgende stap.

---

### 2026-01-18 (sessie 24) - Fase 8.8 COMPLEET

**GitHub Community Standards:**
- CONTRIBUTING.md toegevoegd met skill development guidelines
- SECURITY.md toegevoegd met vulnerability policy
- CHANGELOG.md toegevoegd in Keep a Changelog format
- Issue templates: bug_report.yml, feature_request.yml, config.yml
- PR template: PULL_REQUEST_TEMPLATE.md
- CODE_OF_CONDUCT.md overgeslagen (content filter issues)
- Score: 6/7 ✅

**Status:** Repository ready for public release!

---

### 2026-01-18 (sessie 23) - Fase 8.8 Planning

**GitHub Best Practices Research:**
- Gap analyse uitgevoerd tegen GitHub community standards
- Huidige score: 2/7 (alleen README + LICENSE)
- 9 bestanden geïdentificeerd die ontbreken
- Fase 8.8 plan opgesteld

**Fase 8.6-8.7 Compleet:**
- USAGE.md + platform guides
- README.md volledig herschreven
- Issue #14 aangemaakt voor topics (handmatig)

---

### 2026-01-18 (sessie 22) - Fase 8.1-8.4

**Fase 8.1-8.4:**
- V16 skill updates (9 skills)
- 28/28 skills gevalideerd
- Agent Skills standaard review compleet
- Issues #4, #9, #10 gesloten

---

### Eerdere sessies

- **Sessie 21**: Fase 8 planning, V16 audit
- **Sessie 20**: 🎉 v1.0 RELEASE
- **Sessie 19**: Fase 6 - Agents
- **Sessie 18**: Fase 5 - Error handling
- **Sessie 17**: Fase 4.6-4.7
- **Sessie 16**: Fase 4.5
- **Sessie 15**: Fase 4.4
- **Sessie 14**: Fase 4.3
- **Sessie 13**: Masterplan v3
- **Sessie 12**: Documentatie sync
- **Sessie 11**: Fase 4.2
- **Sessie 10**: Engels-only herstructurering
- **Sessie 1-9**: Research, Syntax, Core skills

---

## Next Steps

🎉 **Project is feature-complete!**

Handmatige acties nog nodig:
1. Repository public maken via GitHub UI
2. Topics toevoegen (Issue #14): `erpnext`, `frappe`, `claude`, `anthropic`, `skills`, `ai-coding`
3. Description toevoegen: "28 deterministic skills for Claude to generate flawless ERPNext/Frappe code"
4. API tokens regenereren na public release

---

## Future Considerations

Deze items zijn niet gepland maar kunnen in de toekomst worden overwogen:

- [ ] Plugin marketplace publicatie
- [ ] Meer agents (debugging, migration, etc.)
- [ ] Community contributions
- [ ] Video tutorials

---

## Legenda

| Symbool | Betekenis |
|:-------:|----------:|
| ✅ | Voltooid |
| 🔄 | In progress |
| ⏳ | Gepland |
| ⏭️ | Skipped |
| ❌ | Vervallen |
| 🔴 | Hoge prioriteit |
| 🟡 | Medium prioriteit |
| 🟢 | Lage prioriteit |
