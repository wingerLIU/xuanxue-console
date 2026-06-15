@echo off
python -B -X utf8 scripts\audit_project_hygiene.py || exit /b 1
python -B -X utf8 scripts\audit_source_register.py || exit /b 1
python -B -X utf8 scripts\audit_source_documentation.py || exit /b 1
python -B -X utf8 scripts\audit_promotion_manifest.py || exit /b 1
python -B -X utf8 scripts\check_source_urls.py --type classical_text --evidence-mode online_public_entry --max-sources 1 --dry-run || exit /b 1
python -B -X utf8 scripts\audit_knowledge_base.py || exit /b 1
python -B -X utf8 scripts\audit_rule_cards.py || exit /b 1
python -B -X utf8 scripts\audit_case_retrospectives.py || exit /b 1
python -B -X utf8 scripts\audit_knowledge_coverage.py || exit /b 1
python -B -X utf8 -m unittest discover -s scripts -p "test_*.py" || exit /b 1
