set -euo pipefail
printf '%s' "${PR_BODY:-}" \
  | tr -d '\000-\010\013-\037\177' \
  | perl -0777 -pe 's/<!--.*?-->//gs' \
  | head -c 2000 > body.txt
d="__ATLAS_EOF_$RANDOM$RANDOM"
{
  printf 'text<<%s\n' "$d"
  cat body.txt
  if [ -s body.txt ] && [ -n "$(tail -c1 body.txt)" ]; then echo; fi
  printf '%s\n' "$d"
} >> "$GITHUB_OUTPUT"
