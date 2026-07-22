# 🔧 FIX PLAN: #213 (F821) + #215 (F401)

**Sprint:** 1 (Week 1)
**Issues:** #213 (95 errors), #215 (130 errors)
**Total:** 225 critical errors
**Estimated time:** 3-4 hours

---

## Issue #213: F821 undefined-name (95 errors)

### Problem
Variable used before definition or missing import.

### Strategy
1. Analyze each F821 case
2. Add missing import OR
3. Add variable declaration with default value OR
4. Reorder code (move definition before usage)

### Execution
```bash
# Get list of F821 errors
ruff check . --select F821 --output-format=json > /tmp/f821.json

# Analyze
cat /tmp/f821.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data:
    print(f\"{item['filename']}:{item['location']['row']}:{item['location']['column']} {item['message']}\")
" | head -20
```

---

## Issue #215: F401 unused-import (130 errors)

### Problem
Import statement not used in code.

### Strategy
1. Remove unused imports automatically
2. Verify tests still pass

### Execution
```bash
# Auto-fix F401
ruff check . --select F401 --fix

# Verify
ruff check . --select F401
```

---

## Verification

After both fixes:
```bash
# Check remaining errors
ruff check . --select F821,F401

# Run tests
pytest tests/ -v
```

---

## Expected Result

- F821: 95 → 0
- F401: 130 → 0
- Total reduction: 225 errors
- Tests: 572 passed (no regression)

---

**Status:** READY TO EXECUTE
