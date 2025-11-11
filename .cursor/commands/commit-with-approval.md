# Git Commit Command (With Approval)

You are helping the user create a git commit with proper staging and commit message formatting. This command requires explicit user approval before executing the commit.

## Important Rules

1. **NEVER use `git add .` or `git add -A`** - Always stage files with explicit paths
2. **Always list files explicitly** - Show the user what will be committed
3. **Use a single `git add` command** - List all files in one command, not multiple individual commands
4. **Create meaningful commit messages** - Follow conventional commit format
5. **NEVER use `--no-verify` or `-n`** - Always run pre-commit and commit-msg hooks
6. **ALWAYS wait for approval** - Never commit without explicit user confirmation

---

## Workflow

### Step 1: Check Git Status

Run:
```bash
git status --short
```

Analyze the output and categorize files:
- Modified files (M)
- New files (??)
- Deleted files (D)
- Renamed files (R)

---

### Step 2: List Changed Files

Present to the user:
```
Files ready to commit:

Modified:
  - file1.py
  - file2.py

New:
  - file3.py

Deleted:
  - file4.py

Total: X files
```

---

### Step 3: Draft Commit Message

Follow this format:

```
<type>: <short description>

<detailed description if needed>

<succinct list of key changes>
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, config, etc.)
- `perf`: Performance improvements

**Examples:**

```
feat: Implement configuration management system

Add Pydantic-based configuration with environment support:
- Multi-environment support (dev, staging, prod)
- Type-safe configuration loading
- Helper methods for DynamoDB and AWS endpoints
```

```
chore: Update dependencies to latest versions

- Upgrade pytest to 8.0.0
- Update black to 24.0.0
- Add pydantic-settings for config management
```

---

### Step 4: Safety Checks

Before presenting for approval, verify:
- [ ] No `.env` or `.env.local` files being committed (unless it's `.env.example`)
- [ ] No `node_modules/` or `__pycache__/` being committed
- [ ] No large binary files (> 10MB) unless intentional
- [ ] No API keys or secrets in code
- [ ] Files are actually ready to commit (not work-in-progress)

If any safety issues found, warn the user clearly.

---

### Step 5: Present for Approval

Present the proposed commit for user review:

```
PROPOSED COMMIT

Files to stage (X files):
  - path/to/file1.py
  - path/to/file2.py
  - path/to/file3.py

Commit message:
───────────────────────────────────────
<type>: <short description>

<detailed description>

- Key change 1
- Key change 2
- Key change 3
───────────────────────────────────────

Safety checks:
✅ No secrets or credentials
✅ No large binary files
✅ No dependency directories
✅ Files are ready to commit

Commands to execute:
1. git add path/to/file1.py path/to/file2.py path/to/file3.py
2. git commit -m "$(cat <<'EOF'
   <commit message>
   EOF
   )"

───────────────────────────────────────

Please review and respond:
- "approved" or "yes" to proceed with commit
- "no" or "cancel" to abort
- Provide feedback to revise commit message
- Suggest files to add/remove from commit
```

---

### Step 6: Wait for User Response

**CRITICAL**: Do NOT proceed until user responds with one of the following:

#### Response: "approved" or "yes"
- Proceed to Step 7 (Execute Commit)

#### Response: "no" or "cancel"
- Abort the commit process
- Output: "Commit cancelled by user"

#### Response: Feedback/Suggestions
Examples:
- "Change commit message to ..."
- "Don't include file3.py"
- "Add file4.py to the commit"
- "Use 'fix' instead of 'feat'"

**Action**:
1. Incorporate the feedback
2. Revise the commit proposal
3. Present updated proposal for approval again
4. Return to Step 5

#### Response: User asks "Why X?"
Examples:
- "Why is file3.py included?"
- "Why use 'feat' instead of 'chore'?"

**Action**:
1. Provide clear reasoning for the decision
2. If reasoning is weak, offer to change it
3. Wait for user's decision (approved/change/cancel)

---

### Step 7: Execute Commit (Only After Approval)

Once approved, execute the commit:

```bash
# Stage files explicitly
git add path/to/file1.py path/to/file2.py path/to/file3.py

# Create commit with heredoc
git commit -m "$(cat <<'EOF'
<commit message here>
EOF
)"
```

**CRITICAL**: NEVER use `--no-verify` or `-n` flags. Pre-commit hooks MUST run to ensure:
- Code formatting (black, prettier, etc.)
- Linting (ruff, eslint, etc.)
- Type checking (mypy, tsc, etc.)
- Tests passing
- Security checks

Only skip hooks if the user explicitly requests it for a valid reason (e.g., fixing broken hooks).

---

### Step 8: Handle Pre-commit Hook Failures

If pre-commit hooks fail:

```
Pre-commit hooks failed:

[Error output from hooks]

The commit was not created.

Options:
1. Fix the issues and try again
2. Review the changes made by hooks (if any)
3. Investigate why hooks failed

Would you like me to:
- Show the git diff to see what changed?
- Run the specific failing check manually?
- Abort this commit?
```

**If hooks auto-fixed files** (e.g., black reformatted code):
```
Pre-commit hooks made changes:

Modified files:
  - path/to/file1.py (auto-formatted by black)

The commit was not created yet.

Options:
1. Review the changes: git diff
2. Stage the auto-fixed files and retry commit
3. Abort

Please respond with your choice.
```

---

### Step 9: Verify Commit

After successful commit:

```
✅ COMMIT SUCCESSFUL

Commit: a1b2c3d feat: Implement configuration management system
Files: 3 files changed
Author: [name] <[email]>
Date: [timestamp]

You can verify with: git log --oneline -1
```

Run verification:
```bash
git log --oneline -1
```

---

## Safety Checks Details

### Critical Issues (Block commit)

❌ **Secrets/Credentials**:
- `.env` files (except `.env.example`)
- `credentials.json`, `service-account.json`
- Files containing API keys, tokens, passwords
- AWS credentials files

❌ **Large Files**:
- Binary files > 10MB
- Database dumps
- Media files (unless intentional)

❌ **Dependency Directories**:
- `node_modules/`
- `__pycache__/`
- `.pytest_cache/`
- `venv/`, `.venv/`

### Warnings (Ask for confirmation)

⚠️ **Many files** (> 10 files):
```
Warning: This commit includes 15 files.

Consider breaking into smaller, focused commits:
- Commit 1: Core functionality
- Commit 2: Tests
- Commit 3: Documentation

Proceed anyway? (yes/no/help)
```

⚠️ **Mixed concerns**:
```
Warning: This commit includes both feature code and documentation.

Consider separating:
- Commit 1: feat: Add feature X
- Commit 2: docs: Document feature X

Proceed anyway? (yes/no/help)
```

---

## Special Cases

### Case 1: Committing .env.example
✅ **Allowed** - This is a template file

### Case 2: Committing package-lock.json or requirements.txt
✅ **Allowed** - These are dependency lockfiles

### Case 3: Committing Memory Bank updates
Use commit type: `docs: Update Memory Bank - <what changed>`

### Case 4: Large refactoring (10+ files)
Suggest breaking into multiple commits:
1. Refactor module A
2. Refactor module B
3. Update tests
4. Update documentation

### Case 5: WIP commits
```
Warning: Files may not be ready to commit.

Are you creating a WIP commit? Consider:
- Using git stash instead
- Creating a feature branch
- Waiting until implementation is complete

Proceed with WIP commit? (yes/no)
```

---

## Handling User Feedback

### Example 1: Change commit message

**User**: "Change the message to use 'fix' instead of 'feat'"

**Action**:
```
Updated commit message:

fix: Implement configuration management system

Add Pydantic-based configuration with environment support:
- Multi-environment support (dev, staging, prod)
- Type-safe configuration loading
- Helper methods for DynamoDB and AWS endpoints

Approved? (yes/no/feedback)
```

### Example 2: Remove file from commit

**User**: "Don't commit file3.py"

**Action**:
```
Updated file list (2 files):
  - path/to/file1.py
  - path/to/file2.py

Removed:
  - path/to/file3.py

Updated commit proposal:
───────────────────────────────────────
[Updated proposal with new file list]
───────────────────────────────────────

Approved? (yes/no/feedback)
```

### Example 3: Add file to commit

**User**: "Also include tests/test_config.py"

**Action**:
```
Updated file list (4 files):
  - path/to/file1.py
  - path/to/file2.py
  - path/to/file3.py
  - tests/test_config.py (added)

Updated commit proposal:
───────────────────────────────────────
[Updated proposal with new file list]
───────────────────────────────────────

Approved? (yes/no/feedback)
```

### Example 4: Why question

**User**: "Why is this a 'feat' commit?"

**Action**:
```
Reasoning for 'feat' commit type:

This commit introduces new functionality:
- New configuration management system
- New Pydantic models
- New helper methods

According to conventional commits:
- 'feat': A new feature (user-facing or internal)
- 'chore': Maintenance/tooling (no feature added)

Since this adds new capabilities to the codebase, 'feat' is appropriate.

Would you like to:
1. Keep it as 'feat' (approved)
2. Change to 'chore' (provide reason)
3. Use different type (specify)
```

---

## Approval Loop

The command will loop until one of these conditions:

1. ✅ **User approves** → Execute commit
2. ❌ **User cancels** → Abort commit
3. 🔄 **User provides feedback** → Revise and re-present for approval

Maximum 5 revision iterations. After 5 iterations:
```
Maximum revisions reached (5 attempts).

Would you like to:
1. Approve current version
2. Cancel commit
3. Start over with fresh proposal
```

---

## Output Format

### Success
```
✅ COMMIT SUCCESSFUL

Commit: [hash] [message first line]
Files: [count] files changed, [insertions] insertions(+), [deletions] deletions(-)

Next steps:
- Review: git show
- Push: git push
```

### Cancelled
```
❌ COMMIT CANCELLED

No changes were committed.
Staged files remain staged.

To unstage: git reset
```

### Failed (hooks)
```
❌ COMMIT FAILED

Pre-commit hooks failed. See errors above.

To fix:
1. Address the issues
2. Run the commit command again
```

---

## Rules & Constraints

### MUST DO

1. ✅ Read git status first
2. ✅ List all files explicitly
3. ✅ Draft commit message following conventional format
4. ✅ Run safety checks
5. ✅ Present for approval
6. ✅ **WAIT for user approval**
7. ✅ Stage files by name (one command)
8. ✅ Use heredoc for commit message
9. ✅ Verify commit created

### MUST NOT DO

1. ❌ Use `git add .` or `git add -A`
2. ❌ Use `--no-verify` or `-n` (unless explicitly requested)
3. ❌ Commit without approval
4. ❌ Ignore safety check warnings
5. ❌ Commit secrets or credentials
6. ❌ Proceed if user says "no" or "cancel"
7. ❌ Skip presenting the proposal

---

## Example Full Execution

**User**: `/commit-with-approval`

**AI**:
```
Checking git status...

Files ready to commit:

Modified:
  - .cursor/commands/batch.md
  - .cursor/commands/commit.md
  - .cursor/commands/one-shot.md

Total: 3 files

Safety checks:
✅ No secrets or credentials
✅ No large binary files
✅ No dependency directories
✅ Files are ready to commit

───────────────────────────────────────

PROPOSED COMMIT

Files to stage (3 files):
  - .cursor/commands/batch.md
  - .cursor/commands/commit.md
  - .cursor/commands/one-shot.md

Commit message:
───────────────────────────────────────
chore: Add safety rules to commit commands

Forbid use of git add shortcuts and hook bypass:
- NEVER use git add . or git add -A
- NEVER use --no-verify or -n flags
- Stage files explicitly by name
- Pre-commit hooks must always run
───────────────────────────────────────

Commands to execute:
1. git add .cursor/commands/batch.md .cursor/commands/commit.md .cursor/commands/one-shot.md
2. git commit -m "$(cat <<'EOF'
   chore: Add safety rules to commit commands

   Forbid use of git add shortcuts and hook bypass:
   - NEVER use git add . or git add -A
   - NEVER use --no-verify or -n flags
   - Stage files explicitly by name
   - Pre-commit hooks must always run
   EOF
   )"

───────────────────────────────────────

Please review and respond:
- "approved" or "yes" to proceed
- "no" or "cancel" to abort
- Provide feedback to revise
```

**User**: approved

**AI**:
```
Executing commit...

Staging files...
Creating commit...
[pre-commit hooks run...]

✅ COMMIT SUCCESSFUL

Commit: f8e3a9b chore: Add safety rules to commit commands
Files: 3 files changed, 24 insertions(+), 3 deletions(-)

Next steps:
- Review: git show
- Push: git push
```

---

**Remember**: This command prioritizes user control. NEVER commit without explicit approval. Always incorporate user feedback and re-present for approval.
