#!/usr/bin/env python3
"""Skills-for-Claude installer — one script for Windows, macOS and Linux.

    python install.py                 # skills + core hook + settings + plugins
    python install.py --with-qa-gates # also the QA coverage reminder/stop hooks
    python install.py --with-beads    # also `bd prime` on SessionStart/PreCompact
    python install.py --dry-run       # show what would change, touch nothing

Safe to re-run: identical skills are skipped, changed ones are backed up to
~/.claude/backups/<timestamp>/ before being replaced, settings.json is merged
(never overwritten) and backed up first.
"""
import argparse
import datetime
import filecmp
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
CLAUDE = os.path.join(os.path.expanduser('~'), '.claude')
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
BACKUP = os.path.join(CLAUDE, 'backups', STAMP)

# Windows consoles default to cp1252 — keep the output readable everywhere
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

args = None


def step(msg):
    print(f'\n==> {msg}')


def ok(msg):
    print(f'    [OK] {msg}')


def warn(msg):
    print(f'    [!!] {msg}')


def backup(path):
    """Copy path into the run's backup folder, keeping its location relative to ~/.claude."""
    if args.dry_run or not os.path.exists(path):
        return
    dst = os.path.join(BACKUP, os.path.relpath(path, CLAUDE))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    (shutil.copytree if os.path.isdir(path) else shutil.copy2)(path, dst)


def same_tree(a, b):
    """True when both folders hold the same files with the same bytes (CRLF/LF counts as equal)."""
    def files(root):
        out = set()
        for d, dirs, fs in os.walk(root):
            dirs[:] = [x for x in dirs if x != '__pycache__']
            out |= {os.path.relpath(os.path.join(d, f), root) for f in fs if not f.endswith('.pyc')}
        return out
    if not os.path.isdir(b):
        return False
    fa, fb = files(a), files(b)
    if fa != fb:
        return False
    for rel in fa:
        pa, pb = os.path.join(a, rel), os.path.join(b, rel)
        if filecmp.cmp(pa, pb, shallow=False):
            continue
        with open(pa, 'rb') as x, open(pb, 'rb') as y:
            if x.read().replace(b'\r\n', b'\n') != y.read().replace(b'\r\n', b'\n'):
                return False
    return True


def install_tree(src_root, dst_root, label):
    os.makedirs(dst_root, exist_ok=True)
    new = updated = same = 0
    for name in sorted(os.listdir(src_root)):
        src = os.path.join(src_root, name)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(dst_root, name)
        if same_tree(src, dst):
            same += 1
            continue
        existed = os.path.isdir(dst)
        if not args.dry_run:
            if existed:
                backup(dst)
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if existed:
            updated += 1
            ok(f'{name} (updated — old copy backed up)')
        else:
            new += 1
            if args.verbose:
                ok(f'{name} (new)')
    print(f'    {label}: {new} new, {updated} updated, {same} unchanged')
    return updated


def python_cmd():
    """Interpreter path for hook commands. Absolute + forward slashes works in every shell."""
    return '"' + sys.executable.replace('\\', '/') + '"'


def render(obj, py, hooks_dir):
    text = json.dumps(obj).replace('{PYTHON}', py.replace('"', '\\"')).replace('{HOOKS}', hooks_dir)
    return json.loads(text)


def key(cmd):
    words = cmd.replace('"', ' ').split()
    scripts = [os.path.basename(w) for w in words if w.endswith('.py')]
    return scripts[0] if scripts else cmd


def merge_hooks(settings, groups):
    """Add hook entries whose command is not already registered. Never removes anything."""
    hooks = settings.setdefault('hooks', {})
    added = []
    for event, entries in groups.items():
        current = hooks.setdefault(event, [])
        present = ' '.join(h.get('command', '') for e in current for h in e.get('hooks', []))
        for entry in entries:
            cmds = [h['command'] for h in entry['hooks']]
            # match on the script name / command so an older `python3 ~/...` entry is not duplicated
            if all(key(c) in present for c in cmds):
                continue
            current.append(entry)
            added.append(f'{event}: {cmds[0]}')
    return added


def configure_settings(hook_sets):
    step('settings.json (merge, existing values are kept)')
    path = os.path.join(CLAUDE, 'settings.json')
    cfg = json.load(open(os.path.join(REPO, 'config', 'settings.base.json'), encoding='utf-8'))
    hooks_cfg = json.load(open(os.path.join(REPO, 'config', 'hooks.json'), encoding='utf-8'))

    settings = {}
    if os.path.exists(path):
        try:
            settings = json.load(open(path, encoding='utf-8'))
        except json.JSONDecodeError as e:
            warn(f'settings.json is not valid JSON ({e}) — left untouched, fix it and re-run')
            return
    before = json.dumps(settings, sort_keys=True)

    hooks_dir = os.path.join(CLAUDE, 'hooks').replace('\\', '/')
    added = []
    for name in hook_sets:
        added += merge_hooks(settings, render(hooks_cfg[name], python_cmd(), hooks_dir))
    for key in ('enabledPlugins', 'extraKnownMarketplaces'):
        for k, v in cfg.get(key, {}).items():
            settings.setdefault(key, {}).setdefault(k, v)
    perms = settings.setdefault('permissions', {}).setdefault('allow', [])
    for rule in cfg.get('permissions', {}).get('allow', []):
        if rule not in perms:
            perms.append(rule)

    # A dangling hook makes every Edit/Write print an error — flag the ones pointing at missing files
    for event, entries in settings.get('hooks', {}).items():
        for e in entries:
            for h in e.get('hooks', []):
                cmd = h.get('command', '')
                for part in cmd.replace('"', ' ').split():
                    if part.endswith('.py') and not os.path.exists(os.path.expanduser(part)):
                        warn(f'{event} hook points at a missing file: {part}')

    if json.dumps(settings, sort_keys=True) == before:
        ok('already up to date')
        return
    for a in added:
        ok(f'hook added — {a}')
    if not args.dry_run:
        backup(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write('\n')
    ok('settings.json written' + (' (dry run)' if args.dry_run else ''))


def install_plugins():
    step('Claude Code plugins')
    claude = shutil.which('claude')
    if not claude:
        warn('`claude` CLI not on PATH — plugins are listed in settings.json; install them from /plugin later')
        return
    cfg = json.load(open(os.path.join(REPO, 'config', 'settings.base.json'), encoding='utf-8'))
    run = lambda *a: subprocess.run([claude, 'plugin', *a], capture_output=True, text=True,
                                    encoding='utf-8', errors='replace', timeout=300)
    for name, m in cfg.get('extraKnownMarketplaces', {}).items():
        if not args.dry_run:
            run('marketplace', 'add', m['source']['repo'])  # "already exists" is fine
    try:
        listed = run('list').stdout
    except Exception:
        listed = ''
    for plugin in cfg.get('enabledPlugins', {}):
        short = plugin.split('@')[0]
        if short in listed:
            continue
        if args.dry_run:
            ok(f'{plugin} (would install)')
            continue
        r = run('install', plugin)
        if r.returncode == 0:
            ok(plugin)
        else:
            warn(f'{plugin}: {(r.stderr or r.stdout).strip().splitlines()[-1:] or "failed"}')


def check_tools():
    step('Optional tools (only needed by the skills that use them)')
    tools = [
        ('git', 'everything'),
        ('node', 'Playwright skills (npx playwright)'),
        ('maestro', 'maestro-* mobile skills'),
        ('adb', 'android-* / maestro on Android'),
        ('bd', 'beads skill + --with-beads/--with-qa-gates'),
    ]
    for exe, why in tools:
        if shutil.which(exe):
            ok(f'{exe}')
        else:
            print(f'    [--] {exe:<8} not found — needed for {why}')
    print('    Details and API keys: docs/REQUIREMENTS.md')


def main():
    global args
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--dry-run', action='store_true', help='print the plan, change nothing')
    p.add_argument('--with-qa-gates', action='store_true', help='install the QA coverage hooks')
    p.add_argument('--with-beads', action='store_true', help='run `bd prime` on SessionStart/PreCompact')
    p.add_argument('--skip-settings', action='store_true', help='do not touch settings.json')
    p.add_argument('--skip-plugins', action='store_true', help='do not install Claude Code plugins')
    p.add_argument('--project', metavar='DIR', help='also copy project-example skills into DIR/.claude/skills')
    p.add_argument('-v', '--verbose', action='store_true')
    args = p.parse_args()

    if sys.version_info < (3, 8):
        sys.exit('Python 3.8+ required')
    print(f'Skills-for-Claude installer  ->  {CLAUDE}' + ('   [DRY RUN]' if args.dry_run else ''))

    step('Skills')
    changed = install_tree(os.path.join(REPO, 'skills'), os.path.join(CLAUDE, 'skills'), 'skills')

    step('Hooks')
    hook_files = ['fix-flat-skill.py']
    if args.with_qa_gates:
        hook_files += ['qa-coverage-gate.py', 'qa-coverage-stop-gate.py']
    hooks_dst = os.path.join(CLAUDE, 'hooks')
    os.makedirs(hooks_dst, exist_ok=True)
    for h in hook_files:
        src, dst = os.path.join(REPO, 'hooks', h), os.path.join(hooks_dst, h)
        if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
            continue
        if not args.dry_run:
            backup(dst)
            shutil.copy2(src, dst)
        ok(h)

    step('shared-context (created only if missing)')
    for rel in ('memories', 'knowledge', 'tasks', 'results'):
        if not args.dry_run:
            os.makedirs(os.path.join(CLAUDE, 'shared-context', rel), exist_ok=True)
    for rel in ('registry.md', os.path.join('memories', '_shared.md')):
        dst = os.path.join(CLAUDE, 'shared-context', rel)
        if os.path.exists(dst):
            continue
        if not args.dry_run:
            shutil.copy2(os.path.join(REPO, 'config', 'shared-context', rel), dst)
        ok(f'{rel} (template — fill in your own projects)')

    if not args.skip_settings:
        sets = ['core'] + (['qa-gates'] if args.with_qa_gates else []) + (['beads'] if args.with_beads else [])
        configure_settings(sets)
    if not args.skip_plugins:
        install_plugins()

    if args.project:
        step(f'Project skills -> {args.project}')
        install_tree(os.path.join(REPO, 'project-example', '.claude', 'skills'),
                     os.path.join(os.path.abspath(args.project), '.claude', 'skills'), 'project skills')

    check_tools()
    if changed and not args.dry_run:
        print(f'\nReplaced skills were backed up to {BACKUP}')
    print('\nDone. Restart Claude Code to load the skills and hooks.')
    print('Start with:  "test <feature>"  -> qa-router picks the right skill.  Catalog: SKILLS.md')


if __name__ == '__main__':
    main()
