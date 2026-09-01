# Minimal gated donor action checklist

No command in this checklist is authorised merely because this file exists.
Run it only after recording the applicable explicit donor-mutation gate and
substituting the reviewed candidate paths and exact receipt hash.

Proposed annotated tag: `migration-final-20260821`
Required target commit: `b40587f1b1aec7356a0f623916fcc8212397d283`

1. Re-read the Prompt 19 verification receipt and confirm the donor is archived,
   `main` resolves to the required commit, the tag is absent, and the candidate
   README and tag-message hashes equal the reviewed values.
2. Record the pre-action GitHub API response, headers, request time, archive
   status, default branch, head, existing refs, README blob, and response hashes.
3. Unarchive the donor once through the authenticated repository API.
4. In a fresh clone, require `HEAD` and `origin/main` to equal the required
   commit. Apply only the reviewed README candidate and commit it with explicit
   migration scope. Do not merge or modify runtime code, workflows, state,
   datasets, releases, settings, secrets, issues, or historical evidence.
5. Create annotated tag `migration-final-20260821` from the required operational
   commit using the exact reviewed message. Push the single README commit and
   single tag explicitly; never use `--mirror`, `--all`, `--force`, or blanket
   refspecs.
6. Re-archive the donor immediately. A failure after unarchive is an emergency
   incomplete state: retain logs, stop other writes, and re-archive before any
   closeout claim.
7. Independently read the public repository API, `main`, tag object/target,
   README bytes, ref set, archive status, and timestamps. Require archived=true,
   the expected README hash, the annotated tag target equal to the required
   operational commit, and no unexpected ref or setting change.
8. Add a superseding action receipt to the target and run its schema/fixity
   validation. Do not rewrite pre-action or failed-attempt evidence.

If this gate is not granted, perform none of steps 3–7. Return the reviewed
candidate hashes, proposed tag, exact required commit, and this checklist as the
handoff.

## Exact command template after approval

Run from a new private parent directory. Set `PROMPT19_CANDIDATES` to the
reviewed target checkout's `docs/migrations/corpus-legislation-nz/donor-archival`
directory. The preflight must verify the recorded candidate hashes before these
commands begin.

```sh
set -euo pipefail
DONOR_REPOSITORY=edithatogo/corpus-legislation-nz
OPERATIONAL_COMMIT=b40587f1b1aec7356a0f623916fcc8212397d283
FINAL_TAG=migration-final-20260821
TEST_WORKSPACE="$PWD/corpus-legislation-nz-prompt19"

test ! -e "$TEST_WORKSPACE"
test "$(gh api "repos/$DONOR_REPOSITORY" --jq .archived)" = true
test "$(gh api "repos/$DONOR_REPOSITORY/commits/main" --jq .sha)" = "$OPERATIONAL_COMMIT"
if gh api "repos/$DONOR_REPOSITORY/git/ref/tags/$FINAL_TAG" --silent 2>/dev/null; then
  exit 2
fi

gh api --method PATCH "repos/$DONOR_REPOSITORY" -F archived=false >/tmp/prompt19-unarchive-response.json
archived_again=false
rearchive_on_exit() {
  if [ "$archived_again" != true ]; then
    gh api --method PATCH "repos/$DONOR_REPOSITORY" -F archived=true \
      >/tmp/prompt19-emergency-rearchive-response.json
  fi
}
trap rearchive_on_exit EXIT
gh repo clone "$DONOR_REPOSITORY" "$TEST_WORKSPACE"
test "$(git -C "$TEST_WORKSPACE" rev-parse origin/main)" = "$OPERATIONAL_COMMIT"
cp "$PROMPT19_CANDIDATES/README.candidate.md" "$TEST_WORKSPACE/README.md"
git -C "$TEST_WORKSPACE" add -- README.md
git -C "$TEST_WORKSPACE" diff --cached --check
git -C "$TEST_WORKSPACE" commit -m "Add final migration redirect"
git -C "$TEST_WORKSPACE" tag -a "$FINAL_TAG" "$OPERATIONAL_COMMIT" \
  -F "$PROMPT19_CANDIDATES/final-tag-message.txt"
git -C "$TEST_WORKSPACE" push origin HEAD:main
git -C "$TEST_WORKSPACE" push origin "refs/tags/$FINAL_TAG:refs/tags/$FINAL_TAG"
gh api --method PATCH "repos/$DONOR_REPOSITORY" -F archived=true >/tmp/prompt19-rearchive-response.json
archived_again=true

test "$(gh api "repos/$DONOR_REPOSITORY" --jq .archived)" = true
test "$(gh api "repos/$DONOR_REPOSITORY/git/ref/tags/$FINAL_TAG" --jq .object.sha)" = \
  "$(git -C "$TEST_WORKSPACE" rev-parse "$FINAL_TAG")"
```

The exit trap re-archives the donor if any command after unarchive fails. A
separate authenticated session should still be ready to verify or repair that
emergency action. `/tmp` response files are bounded local attempt evidence;
sanitize and hash them before committing a receipt, and never commit
authentication material or response headers containing credentials.
