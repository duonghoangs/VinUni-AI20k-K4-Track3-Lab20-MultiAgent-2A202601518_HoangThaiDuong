#!/usr/bin/env bash
set -euo pipefail

if rg -n "TODO\(student\)" src tests docs notebooks -g '!*.egg-info/**'; then
  echo "Student TODO markers remain."
  exit 1
fi

echo "No student TODO markers found."
