$ErrorActionPreference = "Stop"

function Invoke-Checked {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Command)
  & $Command[0] @($Command[1..($Command.Length - 1)])
  if ($LASTEXITCODE -ne 0) {
    throw "command failed with exit code ${LASTEXITCODE}: $($Command -join ' ')"
  }
}

Invoke-Checked python -B -X utf8 scripts\audit_project_hygiene.py
Invoke-Checked python -B -X utf8 scripts\audit_source_register.py
Invoke-Checked python -B -X utf8 scripts\audit_source_documentation.py
Invoke-Checked python -B -X utf8 scripts\audit_promotion_manifest.py
Invoke-Checked python -B -X utf8 scripts\check_source_urls.py --type classical_text --evidence-mode online_public_entry --max-sources 1 --dry-run
Invoke-Checked python -B -X utf8 scripts\audit_knowledge_base.py
Invoke-Checked python -B -X utf8 scripts\audit_rule_cards.py
Invoke-Checked python -B -X utf8 scripts\audit_case_retrospectives.py
Invoke-Checked python -B -X utf8 scripts\audit_knowledge_coverage.py
Invoke-Checked python -B -X utf8 -m unittest discover -s scripts -p "test_*.py"
