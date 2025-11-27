#!/bin/bash
# Cleanup Script for DeceptiCloud
# Removes redundant/confusing files and organizes structure

set -e

echo "=========================================="
echo "DeceptiCloud File Cleanup"
echo "=========================================="

# Create archive directory for removed files (in case user needs them)
mkdir -p .archive

echo ""
echo "[1/4] Archiving redundant documentation files..."

# Archive redundant docs
mv LOCAL_TESTING.md .archive/ 2>/dev/null && echo "  ✓ Archived LOCAL_TESTING.md (redundant with COMPLETE_TESTING_GUIDE.md)"
mv LOCAL_TEST_README.md .archive/ 2>/dev/null && echo "  ✓ Archived LOCAL_TEST_README.md (auto-generated)"
mv GUIDE.md .archive/ 2>/dev/null && echo "  ✓ Archived GUIDE.md (old guide, replaced by COMPLETE_TESTING_GUIDE.md)"
mv CHANGELOG.md .archive/ 2>/dev/null && echo "  ✓ Archived CHANGELOG.md (use git log instead)"

echo ""
echo "[2/4] Organizing AWS deployment files..."

# Move AWS-specific docs to docs/aws/
mkdir -p docs/aws
mv PRODUCTION_QUICK_START.md docs/aws/ 2>/dev/null && echo "  ✓ Moved PRODUCTION_QUICK_START.md → docs/aws/"
mv docs/PRODUCTION_DEPLOYMENT.md docs/aws/ 2>/dev/null && echo "  ✓ Moved PRODUCTION_DEPLOYMENT.md → docs/aws/"

echo ""
echo "[3/4] Organizing advanced feature docs..."

# Keep advanced docs in docs/advanced/
mkdir -p docs/advanced
mv docs/ANTI_DETECTION.md docs/advanced/ 2>/dev/null && echo "  ✓ Moved ANTI_DETECTION.md → docs/advanced/"
mv docs/ATTACK_FRAMEWORKS.md docs/advanced/ 2>/dev/null && echo "  ✓ Moved ATTACK_FRAMEWORKS.md → docs/advanced/"

echo ""
echo "[4/4] Updating .gitignore..."

# Update .gitignore to exclude archive
if ! grep -q "^\.archive/$" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Archived files" >> .gitignore
    echo ".archive/" >> .gitignore
    echo "  ✓ Updated .gitignore to exclude .archive/"
fi

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Final Structure:"
echo ""
echo "📁 Root (Local Testing - START HERE!)"
echo "  ├── README.md                          ← Main entry point"
echo "  ├── COMPLETE_TESTING_GUIDE.md          ← Full local testing guide"
echo "  ├── TESTING_QUICK_REFERENCE.md         ← Quick commands"
echo "  ├── WINDOWS_QUICKSTART.md              ← Windows-specific guide"
echo "  ├── main_local.py                      ← Run this for local testing"
echo "  └── docker-compose.local.yml           ← Local honeypots"
echo ""
echo "📁 docs/aws/ (AWS Deployment - AFTER local testing)"
echo "  ├── PRODUCTION_QUICK_START.md          ← AWS quick start"
echo "  └── PRODUCTION_DEPLOYMENT.md           ← Detailed AWS guide"
echo ""
echo "📁 docs/advanced/ (Advanced Features - Optional)"
echo "  ├── ANTI_DETECTION.md                  ← Honeypot hardening"
echo "  └── ATTACK_FRAMEWORKS.md               ← Realistic attacks"
echo ""
echo "📁 .archive/ (Archived Files - Can delete if not needed)"
echo "  ├── LOCAL_TESTING.md"
echo "  ├── LOCAL_TEST_README.md"
echo "  ├── GUIDE.md"
echo "  └── CHANGELOG.md"
echo ""
echo "Next Steps:"
echo "  1. Test locally:  bash scripts/test_complete_local.sh"
echo "  2. Read guide:    cat COMPLETE_TESTING_GUIDE.md"
echo "  3. After success: Deploy to AWS (docs/aws/)"
echo ""
