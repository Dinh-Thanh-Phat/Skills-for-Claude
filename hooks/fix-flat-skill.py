import json, sys, re, os, shutil

data = json.load(sys.stdin)
f = data.get('tool_input', {}).get('file_path', '')
if not f:
    sys.exit(0)

normalized = f.replace(chr(92), '/')
# Only the user skill folder; '_'-prefixed files (e.g. _update-log.md) are notes, not skills
if re.search(r'/[.]claude/skills/[^/_][^/]*[.]md$', normalized) and os.path.isfile(f):
    dir_path = f[:-3]
    os.makedirs(dir_path, exist_ok=True)
    shutil.move(f, os.path.join(dir_path, 'SKILL.md'))
    name = os.path.basename(dir_path)
    print(json.dumps({'systemMessage': f'Auto-fixed: {name}/SKILL.md (flat skill converted to directory)'}))
