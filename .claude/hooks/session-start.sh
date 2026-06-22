#!/bin/bash
# SessionStart hook — تجهيز بيئة Claude Code على الويب.
# يثبّت تبعيات البوت + أدوات الفحص حتى تعمل الاختبارات (python3 test_bot.py)
# والتحليل الساكن (ruff/pyflakes) مباشرةً في الجلسة. آمن للتكرار، بلا تفاعل.
set -euo pipefail

# يقتصر على البيئة البعيدة (الويب)؛ محليًا لا يفعل شيئًا.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# كل المخرجات إلى stderr حتى يبقى stdout نظيفًا (لا يُحقن في سياق الجلسة).
{
  echo "🔧 تثبيت تبعيات البوت (requirements.txt)..."
  python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt

  echo "🔧 تثبيت أدوات الفحص (ruff, pyflakes)..."
  python3 -m pip install --quiet --disable-pip-version-check ruff pyflakes

  echo "✅ البيئة جاهزة: python3 test_bot.py + ruff/pyflakes."
} >&2
