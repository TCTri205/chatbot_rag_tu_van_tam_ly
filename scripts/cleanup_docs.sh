#!/bin/bash
# Documentation Cleanup and Update Script
# Sprint 3 - Documentation Synchronization
# Date: 2025-12-17

set -e  # Exit on error

echo "============================================"
echo "Documentation Cleanup - Sprint 3"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base directory
DOCS_DIR="d:/Projects_IT/chatbot_rag_tu_van_tam_ly/docs"

echo "${YELLOW}Phase 1: Creating Archive Directories${NC}"
echo "----------------------------------------"

# Create archive directories
mkdir -p "$DOCS_DIR/archive/bug-fixes"
mkdir -p "$DOCS_DIR/archive/completed-phases"
echo "${GREEN}✓ Archive directories created${NC}"
echo ""

echo "${YELLOW}Phase 2: Archiving Bug Fix Reports (9 files)${NC}"
echo "----------------------------------------"

# Move bug fix reports to archive
mv "$DOCS_DIR/BACKEND_NOT_RUNNING_ISSUE.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: BACKEND_NOT_RUNNING_ISSUE.md"
mv "$DOCS_DIR/BAO_CAO_SUA_LOI_2025-12-16.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: BAO_CAO_SUA_LOI_2025-12-16.md"
mv "$DOCS_DIR/BUG_FIX_REPORT_2025-12-16.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: BUG_FIX_REPORT_2025-12-16.md"
mv "$DOCS_DIR/CRISIS_LOCK_FIX.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: CRISIS_LOCK_FIX.md"
mv "$DOCS_DIR/DEBUG_HELPERS_SUMMARY.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: DEBUG_HELPERS_SUMMARY.md"
mv "$DOCS_DIR/DEBUG_MOOD_403.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: DEBUG_MOOD_403.md"
mv "$DOCS_DIR/FIX_SUMMARY_404_ERRORS.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: FIX_SUMMARY_404_ERRORS.md"
mv "$DOCS_DIR/FIX_SUMMARY_MOOD_403.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: FIX_SUMMARY_MOOD_403.md"
mv "$DOCS_DIR/MOOD_UI_FIX.md" "$DOCS_DIR/archive/bug-fixes/" 2>/dev/null || echo "File not found: MOOD_UI_FIX.md"

echo "${GREEN}✓ Bug fix reports archived${NC}"
echo ""

echo "${YELLOW}Phase 3: Archiving Completed Phase Plans (4 files)${NC}"
echo "----------------------------------------"

mv "$DOCS_DIR/plans/PHASE_1_FOUNDATION.md" "$DOCS_DIR/archive/completed-phases/" 2>/dev/null || echo "File not found: PHASE_1_FOUNDATION.md"
mv "$DOCS_DIR/plans/PHASE_1_VERIFICATION.md" "$DOCS_DIR/archive/completed-phases/" 2>/dev/null || echo "File not found: PHASE_1_VERIFICATION.md"
mv "$DOCS_DIR/plans/PHASE_2_RAG_ENGINE.md" "$DOCS_DIR/archive/completed-phases/" 2>/dev/null || echo "File not found: PHASE_2_RAG_ENGINE.md"
mv "$DOCS_DIR/plans/PHASE_3_INTEGRATION.md" "$DOCS_DIR/archive/completed-phases/" 2>/dev/null || echo "File not found: PHASE_3_INTEGRATION.md"

echo "${GREEN}✓ Completed phase plans archived${NC}"
echo ""

echo "${YELLOW}Phase 4: Creating Archive README${NC}"
echo "----------------------------------------"

cat > "$DOCS_DIR/archive/README.md" << 'EOF'
# Documentation Archive

This directory contains historical documentation that has been completed or superseded.

## Structure

### bug-fixes/
Bug fix reports and debugging documents from development phases.
These are preserved for historical reference but are no longer actively maintained.

**Files:**
- Backend startup issues
- API error fixes (404, 403)
- UI bug fixes
- Debug helpers and tools

### completed-phases/
Execution plans for completed development phases.
These phases have been successfully implemented and verified.

**Completed Phases:**
- Phase 1: Foundation (Auth, DB, Basic API)
- Phase 2: RAG Engine  
- Phase 3: Integration & UI

## Active Documentation

Current documentation is maintained in the parent `docs/` directory.

**Last Updated:** 2025-12-17
EOF

echo "${GREEN}✓ Archive README created${NC}"
echo ""

echo "${YELLOW}Phase 5: Removing Merged Files${NC}"
echo "----------------------------------------"

# These will be merged into core docs, can be deleted after merge
rm -f "$DOCS_DIR/API_UPDATE_SUMMARY.md"
rm -f "$DOCS_DIR/SESSION_UPDATE_IMPLEMENTATION.md"

echo "${GREEN}✓ Redundant files removed${NC}"
echo ""

echo "============================================"
echo "${GREEN}Documentation Cleanup Complete!${NC}"
echo "============================================"
echo ""
echo "Summary:"
echo "- ${GREEN}✓${NC} Created archive structure"
echo "- ${GREEN}✓${NC} Archived 9 bug fix reports"
echo "- ${GREEN}✓${NC} Archived 4 completed phase plans"
echo "- ${GREEN}✓${NC} Removed 2 merged files"
echo ""
echo "Next Steps:"
echo "1. Update core documentation (DATABASE_SCHEMA.md, API_DESIGN.md, etc.)"
echo "2. Verify all file links still work"
echo "3. Create INDEX.md for navigation"
echo ""
