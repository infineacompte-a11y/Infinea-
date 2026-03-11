# Infinea — Repo Principal

Ce repo est le coeur du projet Infinea SaaS.

## Backup automatique
- Post-commit hook : auto-push vers GitHub après chaque commit
- Dropbox sync : continu
- Script global : `~/.claude/scripts/auto-backup.sh`

## Règles
- Toujours committer après chaque modification significative
- Ne jamais force push
- Créer un tag avant tout refactoring majeur : `git tag backup-avant-<description>`
- Organisation globale : `~/Dropbox/Infinea Globale/`
