#!/usr/bin/env bash
# Crea labels, milestones e Issues de las historias de usuario (docs/issues/HU-*.md) en GitHub.
# Requiere GitHub CLI autenticado (gh auth status). Es idempotente: no duplica lo que ya existe.
# Uso (Git Bash):  bash tools/crear_issues.sh
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Repositorio: $REPO"

crear_label() {  # nombre color descripción
  gh label create "$1" --color "$2" --description "$3" --force >/dev/null
  echo "  label: $1"
}
echo "Labels..."
crear_label hu   "0E8A16" "Historia de usuario"
crear_label inc1 "1D76DB" "Incremento 1 (PMV)"
crear_label inc2 "5319E7" "Incremento 2"
crear_label bug  "D73A4A" "Defecto encontrado en pruebas"
crear_label docs "C5DEF5" "Documentación"

crear_milestone() {  # título descripción
  local existe
  existe="$(gh api "repos/$REPO/milestones?state=all&per_page=100" -q ".[] | select(.title==\"$1\") | .number")"
  if [[ -z "$existe" ]]; then
    gh api "repos/$REPO/milestones" -f title="$1" -f description="$2" >/dev/null
    echo "  milestone creado: $1"
  else
    echo "  milestone existente: $1"
  fi
}
echo "Milestones..."
crear_milestone "Incremento 1 (PMV)" "HU-01 a HU-04 · tag v1.0-PMV"
crear_milestone "Incremento 2" "HU-05 a HU-08 · tag v2.0-Inc2"

# Lee un campo del encabezado YAML simple de un archivo de Issue.
campo() { sed -n "s/^$1: *//p" "$2" | head -1 | sed 's/^"\(.*\)"$/\1/'; }

echo "Issues..."
for f in docs/issues/HU-*.md; do
  titulo="$(campo titulo "$f")"
  labels="$(campo labels "$f")"
  milestone="$(campo milestone "$f")"
  cuerpo="$(awk 'BEGIN{n=0} /^---$/{n++; next} n>=2' "$f")"

  if gh issue list --state all --limit 200 --json title -q '.[].title' | grep -Fxq "$titulo"; then
    echo "  existente: $titulo"
    continue
  fi
  gh issue create --title "$titulo" --body "$cuerpo" --label "$labels" --milestone "$milestone" >/dev/null
  echo "  creado: $titulo"
done
echo "Listo."
