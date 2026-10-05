import json, sys, re, os, subprocess, shutil

# Maintainer-only hook: mirrors edits of ~/.claude/skills into this repo and pushes.
# Not installed by setup — see personal/README.md.
REPO = os.environ.get('SKILLS_REPO', 'C:/Users/wi/Skills-for-Claude')

data = json.load(sys.stdin)
f = data.get('tool_input', {}).get('file_path', '')
if not f:
    sys.exit(0)

normalized = f.replace('\\', '/')

skill_match  = re.search(r'\.claude/skills/(.+)', normalized)
memory_match = re.search(r'\.claude/shared-context/memories/(.+)', normalized)

if skill_match:
    rel = skill_match.group(1)
    # skip PT/sales flat skills
    if re.match(r'^(commission-calculator|contract-tracker|customer-segmentation|delivery-scheduler|order-|price-list|quote-builder|reorder-suggester|returns-processor|sales-pipeline)', rel):
        sys.exit(0)
    name = rel.split('/')[0]
    if rel == '_update-log.md' or os.path.isdir(os.path.join(REPO, 'personal', 'skills', name)):
        dst = os.path.join(REPO, 'personal', 'skills', rel)  # maintainer-only, not installed by setup
    else:
        dst = os.path.join(REPO, 'skills', rel)
elif memory_match:
    rel = memory_match.group(1)
    dst = os.path.join(REPO, 'personal', 'shared-context', 'memories', rel)
else:
    sys.exit(0)

if not os.path.isfile(f):
    sys.exit(0)

os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(f, dst)

label = rel.split('/')[0] if '/' in rel else rel.replace('.md', '')
msg = f'sync: update {label}'

repo_win = REPO.replace('/', '\\')

subprocess.run(['git', 'add', '-A'], cwd=repo_win,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

changed = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=repo_win)
if changed.returncode != 0:
    subprocess.run(['git', 'commit', '-m', msg], cwd=repo_win,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.Popen(['git', 'push'], cwd=repo_win,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(json.dumps({'systemMessage': f'[skills-repo] committed: {label}'}))
