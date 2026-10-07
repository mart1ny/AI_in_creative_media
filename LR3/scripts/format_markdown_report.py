"""Оформление Markdown без изменения проверенного Word-отчёта."""
from pathlib import Path
import re


def format_report(text: str) -> str:
    if not text.startswith('# '):
        text = '# Лабораторная работа 3 Подготовка изображений и визуализация в Engee\n\n' + (
            '**Вариант 3.** Уменьшение изображения в четыре раза и возврат к исходному размеру.\n\n'
            'Власюк Данил Витальевич, группа Т26ИИКТ-МИК11. 7 октября 2026 года.\n\n'
        ) + '## 1' + text.split('## 1', 1)[1]
    text = text.replace('| Метрика | База | s | После | Δ | |Δ|/s | >2s |',
                        '| Метрика | База | s | После | Δ | Модуль Δ / s | >2s |')
    text = text.replace('## 6 Контрольные вопросы продолжение\n\n', '')
    text = re.sub(r'(?m)^([0-9a-f]{32})\n([0-9a-f]{32})$',
                  r'```text\n\1\2\n```', text)
    code = 'include("lab03_lib.jl")\ng = luma_images(make_scene(101; scene_preset(1)...))\nh = apply_factor(g, 3)\nvariant_summary(3)'
    if '```julia\n' + code not in text:
        text = text.replace(code, '```julia\n' + code + '\n```')
    text = text.replace('В Engee из папки с исходниками:\ninclude("LR03_3.jl")\n\nНезависимая проверка локально из LR3:\npython3 scripts/verify_results.py',
                        'В Engee из папки с исходниками:\n\n```julia\ninclude("LR03_3.jl")\n```\n\nНезависимая проверка локально из LR3:\n\n```bash\npython3 scripts/verify_results.py\n```')
    text = text.replace('ЛР03_Вариант_3_Сдача.zip лежит в папке LR3 рядом с README.md.',
                        '[Архив для сдачи](../ЛР03_Вариант_3_Сдача.zip) лежит в папке LR3 рядом с README.md.')
    text = text.replace('Полный паспорт доступен в reports/passport.md и reports/passport.json.',
                        'Полный паспорт доступен в [Markdown](passport.md) и [JSON](passport.json).')
    return text.rstrip() + '\n'


if __name__ == '__main__':
    path = Path(__file__).resolve().parents[1] / 'reports/ЛР03_Вариант_3_Отчёт.md'
    path.write_text(format_report(path.read_text()))
