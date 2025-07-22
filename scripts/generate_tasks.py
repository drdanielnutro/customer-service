#!/usr/bin/env python3
"""
Generate individual task files from tasks.md and create checklist.json according to AGENTS.md schema.
"""
import os
import sys
import re
import json
from datetime import datetime


def parse_tasks_md(path):
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    title = None
    sections = []  # list of (number_str, title, start_idx)
    for idx, line in enumerate(lines):
        # capture document title
        if idx == 0 and line.startswith('# '):
            title = line[2:].strip()
        # capture main sections '## N. Title'
        m = re.match(r'##\s+(\d+)\.\s*(.*)', line)
        if m:
            num = m.group(1)
            sec_title = m.group(2).strip()
            sections.append((num, sec_title, idx))

    # add end index for last section
    results = []
    for i, (num, sec_title, start) in enumerate(sections):
        end = sections[i+1][2] if i+1 < len(sections) else len(lines)
        chunk = lines[start:end]
        results.append((num, sec_title, chunk))
    return title or '', results


def write_task_files(out_dir, tasks_chunks):
    os.makedirs(out_dir, exist_ok=True)
    for num, sec_title, chunk in tasks_chunks:
        # safe filename: keep original numbering and title
        fname = f"{num}. {sec_title}.md"
        path = os.path.join(out_dir, fname)
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(chunk)


def generate_checklist_json(out_path, project_name, checklist_items, source_file):
    tasks = []
    for idx, item in enumerate(checklist_items, start=1):
        tasks.append({
            'id': idx,
            'title': item,
            'description': item,
            'status': 'pending',
            'dependencies': [],
            'priority': 'medium',
            'details': '',
            'testStrategy': ''
        })
    metadata = {
        'projectName': project_name,
        'totalTasks': len(tasks),
        'sourceFile': source_file,
        'generatedAt': datetime.utcnow().isoformat() + 'Z'
    }
    out = {'tasks': tasks, 'metadata': metadata}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def parse_checklist_items(tasks_md_lines):
    items = []
    for line in tasks_md_lines:
        m = re.match(r'- \[ ?\] ?(.*)', line)
        if m:
            items.append(m.group(1).strip())
    return items


def main():
    base = os.path.dirname(__file__)
    root = os.path.abspath(os.path.join(base, os.pardir))
    tasks_md = os.path.join(root, 'tasks.md')
    if not os.path.isfile(tasks_md):
        print(f"Error: tasks.md not found at {tasks_md}", file=sys.stderr)
        sys.exit(1)

    project_title, sections = parse_tasks_md(tasks_md)
    write_task_files(os.path.join(root, 'tasks'), sections)

    # extract checklist section (section number '7')
    checklist_lines = []
    for num, title, chunk in sections:
        if num == '7':
            checklist_lines = chunk
            break
    checklist_items = parse_checklist_items(checklist_lines)
    generate_checklist_json(
        os.path.join(root, 'checklist.json'),
        project_title,
        checklist_items,
        'tasks.md'
    )


if __name__ == '__main__':
    main()
