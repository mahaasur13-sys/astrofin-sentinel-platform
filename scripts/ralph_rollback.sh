#!/bin/bash
# Утилита восстановления после сбоя Ralph Loop
echo "🔄 Восстанавливаем последний stash..."
git checkout -- .
if git stash list | grep -q "ralph-attempt"; then
    git stash pop
    echo "✅ Stash восстановлен."
else
    echo "⚠️  Нет сохранённых stash от Ralph."
fi
echo "Текущий статус:"
git status
