# LiveWeb Arena Continuous Audit Loop

You are a dual-role auditor+developer for the LiveWeb Arena project. Each iteration, pick ONE issue from the audit queue, red-team validate it, then fix it if validated.

## Execution Protocol

### Step 1: Load State
Read `/home/claudeuser/.claude2/projects/-home-claudeuser-work-liveweb-arena/memory/audit-findings.md` to see known issues and their status. Also read `CLAUDE.md` for project rules.

### Step 2: Select Next Issue
Choose the highest-priority **unfixed** issue. Priority order:
1. **High severity** bugs (correctness, data integrity, broken config)
2. **Medium severity** Rule 9 (No Fallback) violations — these mask real errors
3. **Medium severity** Rule 3 (Zero Redundancy) / dead code
4. **Medium severity** extensibility issues
5. **File size violations** (Rule 5)
6. **Test coverage gaps** for critical paths
7. **Macro-level audit** — new strategic issues (see Macro Audit Rotation below)

If all known issues are resolved, run a **Macro Audit Rotation** scan (see below).

### Step 3: Red-Team Validation (MANDATORY before any fix)

Before implementing ANY fix, you MUST pass the red-team gate. Ask these 5 questions:

1. **Is this a real problem?** — Read the actual code. Confirm the issue exists as described. If the audit finding is stale or wrong, update the findings file and skip.
2. **Is the fix necessary?** — Could the current behavior be intentional? Check git blame, commit messages, PR context. If ambiguous, document your reasoning.
3. **Does the fix introduce new problems?** — Will the change break existing behavior? Does removing a fallback cause unhandled crashes? Trace all callers.
4. **Is this the minimal fix?** — Apply Occam's Razor. Don't refactor the world. Fix exactly the issue identified, nothing more.
5. **Does this fix respect all CLAUDE.md rules?** — No new fallbacks, no file size increases, no redundancy, absolute imports for cross-package.

If ANY question fails: skip the fix, document why in the findings file, and move to the next issue.

### Step 4: Implement Fix
- Read the file(s) involved
- Make the minimal change
- Run relevant tests: `cd /home/claudeuser/work/liveweb-arena && python -m pytest tests/ -x -q`
- If tests fail, fix forward (don't revert and skip)
- Update the findings file: mark the issue as `[FIXED]` with date

### Step 5: Report
Output a brief summary:
```
[AUDIT] Issue: <one-line description>
[RED-TEAM] Passed: <yes/no, with reason if no>
[ACTION] <fixed / skipped / deferred>
[NEXT] <what remains highest priority>
```

---

## Macro Audit Rotation

When micro-issues are exhausted, cycle through these macro-level audit dimensions (one per iteration):

### A. Template Quality Audit
Pick one template at random. Run the full Red Team Review from CLAUDE.md:
1. API Semantic Verification — call the API, check data matches question intent
2. World Knowledge Attack — can an LLM answer without browsing? >60% = fail
3. Memorization Space Analysis — effective variant space must be >500
4. Answer Stability — same answer >30 days without >1000 variants = weak
5. Random Baseline — document chance probability
6. Cross-Parameter Collapse — do different params produce different answers?

### B. Architecture Debt Scan
Check for new violations of:
- File size limit (500 lines)
- Hardcoded site-specific logic in generic modules
- Missing plugin interface methods (should gt_collector/reward be plugin-driven?)
- Circular dependencies or import cycles

### C. Dependency & Config Health
- Are all imports resolvable?
- Does `pip install -e .` work?
- Are entry points valid?
- Do Docker builds succeed?

### D. Test Coverage Delta
- Identify the most critical untested code path
- Write ONE focused test that covers it
- Prioritize: interceptor > cache > gt_collector > reward > browser

### E. Competitive/Frontier Analysis
- Is the evaluation methodology sound vs. current LLM agent benchmarks?
- Are the difficulty tiers (easy/medium/hard) properly calibrated?
- Are there capability dimensions in the gap table that should be prioritized?
- Does the plugin portfolio cover enough diversity?

### F. Data Integrity Audit
- Pick a random plugin's `fetch_api_data()` and verify it returns correct structure
- Check that `_merge_api_data()` handles that plugin's data correctly
- Verify detail-page-overwrite priority logic works for that plugin

---

## Rules for This Loop

1. **One issue per iteration.** Don't batch fixes — each change should be independently reviewable.
2. **Always read before editing.** Never assume file contents from memory alone.
3. **Red-team gate is non-negotiable.** Skip fixes that fail validation, document why.
4. **Don't create new files** unless absolutely required (e.g., a test file for a previously untested module).
5. **Don't commit** — the user will review and commit when ready.
6. **Update the findings file** after every iteration (mark fixed, add new findings).
7. **If you discover a new issue** while fixing another, add it to the findings file with appropriate severity — don't fix it in the same iteration.
