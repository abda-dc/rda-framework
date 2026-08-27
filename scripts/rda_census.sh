#!/usr/bin/env bash
# RDA-02 Repository Census -- deterministic inventory. Produces census.json with the command behind every count.
# Usage: rda_census.sh [repo_path] [output_dir]
# Degrades gracefully: records which tool produced each number, and null+reason when none is available.
set -uo pipefail
REPO="${1:-.}"; OUT="${2:-./rda-out}"; mkdir -p "$OUT"
cd "$REPO" || { echo "cannot enter $REPO" >&2; exit 3; }
have() { command -v "$1" >/dev/null 2>&1; }
jstr() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
[ -z "$SHA" ] && { echo "not a git repository: $REPO" >&2; exit 3; }
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
SHALLOW=$(git rev-parse --is-shallow-repository 2>/dev/null || echo unknown)
COMMITS=$(git rev-list --count HEAD 2>/dev/null || echo 0)
FIRST=$(git log --reverse --format=%aI 2>/dev/null | head -1)
LAST=$(git log -1 --format=%aI 2>/dev/null)
AUTHORS=$(git log --format='%ae' 2>/dev/null | sort -u | wc -l | tr -d ' ')
TAGS=$(git tag 2>/dev/null | wc -l | tr -d ' ')
# grep -c prints 0 AND exits 1 when there are no matches, so `&& grep || echo 0` would emit "0\n0"
# and corrupt the JSON. Branch explicitly instead.
if [ -f .gitmodules ]; then SUBS=$(grep -c 'path = ' .gitmodules 2>/dev/null); else SUBS=0; fi
[ -z "$SUBS" ] && SUBS=0
FILES=$(git ls-files 2>/dev/null | wc -l | tr -d ' ')

# ---- language / LOC: prefer scc > tokei > cloc > wc fallback -------------------------------------
LOC_TOOL="wc"; LOC_CMD="git ls-files | xargs wc -l"; LOC_DETAIL="loc.txt"
if have scc;  then LOC_TOOL="scc";  LOC_CMD="scc --format json";  LOC_DETAIL="loc.json"; scc --format json  > "$OUT/loc.json" 2>/dev/null
elif have tokei; then LOC_TOOL="tokei"; LOC_CMD="tokei --output json"; LOC_DETAIL="loc.json"; tokei --output json > "$OUT/loc.json" 2>/dev/null
elif have cloc;  then LOC_TOOL="cloc";  LOC_CMD="cloc --json .";      LOC_DETAIL="loc.json"; cloc --json . > "$OUT/loc.json" 2>/dev/null
else git ls-files -z | xargs -0 wc -l 2>/dev/null | tail -1 > "$OUT/loc.txt"; fi
# A detail file that was never written is a dangling evidence pointer; only cite what exists.
[ -s "$OUT/$LOC_DETAIL" ] || LOC_DETAIL=""
TOTAL_LOC=$(git ls-files -z 2>/dev/null | xargs -0 cat 2>/dev/null | wc -l | tr -d ' ')

# ---- path classification (each tracked path counted exactly once, first match wins) --------------
classify() {
  git ls-files | awk '
    /(^|\/)(vendor|third_party|node_modules|\.yarn)\//              {v++; next}
    /(\.min\.js|\.pb\.go|_pb2\.py|\.generated\.|\.g\.dart|\.designer\.cs)$/ {g++; next}
    /(^|\/)(test|tests|spec|__tests__|e2e|it)\//                    {t++; next}
    /(_test\.|\.test\.|\.spec\.|Test\.java|_spec\.rb)/              {t++; next}
    /(^|\/)(docs?|documentation)\//                                 {d++; next}
    /\.(md|rst|adoc|txt)$/                                          {d++; next}
    /(^|\/)(terraform|infra|infrastructure|deploy|helm|charts|k8s|kubernetes|ansible|pulumi)\// {i++; next}
    /\.(tf|tfvars|bicep)$/                                          {i++; next}
    /\.(ya?ml|json|toml|ini|conf|properties|env|xml)$/              {c++; next}
    /\.(png|jpg|jpeg|gif|ico|pdf|zip|tar|gz|jar|war|so|dll|dylib|exe|bin|woff2?|ttf|mp4|wasm)$/ {b++; next}
                                                                    {s++}
    END{printf "%d %d %d %d %d %d %d %d", s+0,t+0,c+0,i+0,d+0,g+0,v+0,b+0}'
}
# BIN must come from the same first-match-wins pass as every other bucket. Recounting it with an
# independent grep double-counts binaries that already matched an earlier rule (e.g. docs/logo.png),
# so the buckets stop summing to files.tracked -- fatal in a framework built on denominators.
read -r SRC TST CFG INF DOC GEN VEN BIN < <(classify)
CLASSIFIED=$((SRC + TST + CFG + INF + DOC + GEN + VEN + BIN))
if [ "$CLASSIFIED" -eq "$FILES" ]; then RECON="ok"; else RECON="MISMATCH: buckets sum to $CLASSIFIED, tracked is $FILES"; fi

# ---- structural units ---------------------------------------------------------------------------
cnt() { git ls-files | grep -Ec "$1" || true; }
MANIFESTS=$(cnt '(^|/)(package\.json|pom\.xml|go\.mod|Cargo\.toml|pyproject\.toml|requirements\.txt|build\.gradle(\.kts)?|.*\.csproj|Gemfile|composer\.json)$')
LOCKFILES=$(cnt '(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|go\.sum|Cargo\.lock|poetry\.lock|Gemfile\.lock|composer\.lock|packages\.lock\.json)$')
DOCKER=$(cnt '(^|/)(Dockerfile|Containerfile)([^/]*)$')
COMPOSE=$(cnt '(^|/)docker-compose.*\.ya?ml$')
K8S=$(git grep -lE '^(apiVersion|kind):' -- '*.yaml' '*.yml' 2>/dev/null | wc -l | tr -d ' ')
IAC=$(cnt '\.(tf|bicep)$')
CI=$(cnt '(^\.github/workflows/|^\.gitlab-ci\.yml|^azure-pipelines|Jenkinsfile|^\.circleci/|^\.buildkite/)')
MIGRATIONS=$(cnt '(^|/)(migrations?|db/migrate|alembic|liquibase|flyway)/')

# ---- risk-surface indicators (counted, never judged) --------------------------------------------
g() { git grep -lIEi "$1" 2>/dev/null | wc -l | tr -d ' '; }
ROUTES=$(g '@(app|router|blueprint)\.(get|post|put|patch|delete)|@(Get|Post|Put|Patch|Delete)Mapping|app\.(get|post|put|patch|delete)\(|http\.HandleFunc|\[HttpGet|\[HttpPost|routes\.(draw|resources)')
AUTHZ=$(g 'authoriz|authenticat|permission|@PreAuthorize|require_role|is_admin|access_control|rbac')
CRYPTO=$(g 'crypto|cipher|AES|RSA|hashlib|bcrypt|scrypt|pbkdf2|jwt|hmac')
SQL=$(g 'SELECT .*FROM|INSERT INTO|UPDATE .*SET|execute\(|raw\(|createQuery|\.query\(')
PII=$(g 'ssn|social_security|date_of_birth|dob|passport|national_id|credit_card|card_number|cvv|iban|patient|diagnosis|medical_record|email_address|phone_number|home_address')
SUBPROC=$(g 'subprocess|exec\(|system\(|ProcessBuilder|Runtime\.getRuntime|child_process|os/exec')
DESER=$(g 'pickle\.loads|yaml\.load\(|ObjectInputStream|unserialize|Marshal\.load|JsonConvert\.DeserializeObject')
SECRETS_HINT=$(g '(api[_-]?key|secret|password|token|private[_-]?key)\s*[=:]\s*["'"'"'][A-Za-z0-9/+=_-]{12,}')

# ---- change topology ----------------------------------------------------------------------------
if [ "$SHALLOW" = "true" ]; then HOTSPOT_NOTE="shallow clone: history metrics INVALID"; else HOTSPOT_NOTE="ok"
  git log --since='24 months ago' --name-only --format='' 2>/dev/null | grep -v '^$' | sort | uniq -c | sort -rn \
    | head -200 | awk '{print $1","$2}' > "$OUT/hotspots.csv"
  git log --since='24 months ago' --format='%ae' 2>/dev/null | sort -u | wc -l > "$OUT/active_authors.txt"
fi

cat > "$OUT/census.json" <<JSON
{
  "schema": "rda/census/1.0",
  "repo": "$(jstr "$(basename "$(pwd)")")",
  "commit": "$SHA",
  "default_branch": "$(jstr "$BRANCH")",
  "shallow": $( [ "$SHALLOW" = "true" ] && echo true || echo false ),
  "generated_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "history":   {"commits": $COMMITS, "first_commit": "$FIRST", "last_commit": "$LAST",
                "author_identities": $AUTHORS, "tags": $TAGS, "submodules": $SUBS,
                "validity": "$(jstr "$HOTSPOT_NOTE")"},
  "files":     {"tracked": $FILES, "source": $SRC, "test": $TST, "config": $CFG,
                "infrastructure": $INF, "docs": $DOC, "generated": $GEN, "vendored": $VEN, "binary": $BIN,
                "classified_total": $CLASSIFIED, "reconciliation": "$(jstr "$RECON")"},
  "loc":       {"total_lines_all_tracked": $TOTAL_LOC, "tool": "$LOC_TOOL", "detail_file": $( [ -n "$LOC_DETAIL" ] && printf '"%s"' "$LOC_DETAIL" || echo null )},
  "units":     {"build_manifests": $MANIFESTS, "lockfiles": $LOCKFILES, "containerfiles": $DOCKER,
                "compose_files": $COMPOSE, "k8s_manifests": $K8S, "iac_files": $IAC,
                "ci_workflows": $CI, "migration_dirs": $MIGRATIONS},
  "risk_surface": {"route_files": $ROUTES, "authz_files": $AUTHZ, "crypto_files": $CRYPTO,
                "sql_files": $SQL, "personal_data_files": $PII, "subprocess_files": $SUBPROC,
                "deserialisation_files": $DESER, "secret_pattern_files": $SECRETS_HINT},
  "commands":  {"loc": "$(jstr "$LOC_CMD")", "files": "git ls-files", "history": "git log/rev-list",
                "risk_surface": "git grep -lIE <pattern> (patterns in scripts/rda_census.sh)"},
  "caveats": [
    "Counts describe the tree at this commit, not the running system.",
    "Every tracked path is classified exactly once, first match wins; files.classified_total must equal files.tracked.",
    "risk_surface counts are FILE COUNTS matching lexical patterns -- they are a sampling frame, not findings.",
    "k8s_manifests counts YAML files with apiVersion+kind, which over-counts CRDs and templates.",
    "A shallow clone invalidates every history and hotspot metric."
  ]
}
JSON
echo "census written: $OUT/census.json"
