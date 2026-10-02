"""Prepare authored navigation and metadata for publication; never pushes or opens devices."""
from pathlib import Path
from urllib.parse import quote
import hashlib, json, os, re, subprocess, shlex
from datetime import datetime
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
LIB = REPO/'机器人开发参考库'
PAPER = LIB/'15_小纸壳机器人'
GUIDE_NAME = 'Made_by_Z_纸板机器人图文复刻指南 (1).docx'
top_files = ['EDUHK-SRE机器人项目.xmind','AI创意造物课程与学生平台｜产品与教学方案.md',
             '开源机器人项目参考与后续开发规划.docx']

md_files = list(REPO.glob('*.md')) + list(LIB.glob('*.md'))
for folder in LIB.iterdir():
    if folder.is_dir() and re.match(r'^\d\d_',folder.name): md_files += list(folder.glob('*.md'))
changes=[]
for filename in md_files:
    text=filename.read_text()
    def replace(match):
        target=match.group(1)
        if not target.startswith('/'): return match.group(0)
        actual=Path(target)
        if not actual.is_relative_to(REPO) and actual.name==GUIDE_NAME:
            actual=PAPER/'原始资料'/GUIDE_NAME
        if not actual.is_relative_to(REPO):
            raise RuntimeError('Unmapped external file link in '+str(filename.relative_to(REPO)))
        if not actual.exists(): raise RuntimeError('Missing local target: '+str(actual))
        rel=os.path.relpath(actual,filename.parent)
        return '](<'+quote(rel,safe='/.-_~')+'>)'
    updated=re.sub(r'\]\(<([^>]+)>\)',replace,text)
    updated=updated.replace(str(REPO)+'/', '')
    if updated!=text:
        filename.write_text(updated);changes.append(str(filename.relative_to(REPO)))

metadata=[p for p in LIB.glob('*.json')]
for folder in LIB.iterdir():
    if folder.is_dir() and re.match(r'^\d\d_',folder.name): metadata+=list(folder.glob('*.json'))
def portable(value):
    if isinstance(value,dict): return {key:portable(val) for key,val in value.items()}
    if isinstance(value,list): return [portable(item) for item in value]
    if isinstance(value,str) and value.startswith(str(REPO)+'/'):
        return str(Path(value).relative_to(REPO))
    return value
for filename in metadata:
    data=json.loads(filename.read_text())
    if filename==PAPER/'来源与版本.json':
        for row in data:
            row['original_source_note']='User-provided local attachment. The canonical original is preserved in 原始资料; source paths are relative to the repository root.'
            row['original_path']=row['saved_path']
    filename.write_text(json.dumps(portable(data),ensure_ascii=False,indent=2))

manifest=LIB/'仓库下载清单.json'
snapshots=json.loads(manifest.read_text())
for row in snapshots:
    if row.get('status')!='downloaded': continue
    folder=LIB/row['relative_path']
    omitted=[str((Path(base)/'.DS_Store').relative_to(folder))
             for base,_,names in os.walk(folder) if '.DS_Store' in names]
    row['publication_omitted_files']=sorted(set(row.get('publication_omitted_files',[])+omitted))
manifest.write_text(json.dumps(snapshots,ensure_ascii=False,indent=2))

package=LIB/'README.md'
text=package.read_text()
marker='## GitHub发布整理'
if marker not in text:
    text+='\n'+marker+'\n\n文档本机链接已转换为仓库相对路径，元数据里的本机地址已转换为仓库根目录相对路径。上游跟踪文件中一处硬编码API凭据已脱敏，见[记录](<上游源码脱敏记录.json>)。大型文件使用Git LFS；原始许可和版本记录保留。\n'
    package.write_text(text)

files=[]
for base,dirs,names in os.walk(LIB):
    dirs[:]=[d for d in dirs if d!='.git']
    for name in names:
        if name=='.DS_Store': continue
        f=Path(base)/name;files.append(f)
files += [REPO/name for name in top_files]
large=[f for f in files if f.stat().st_size>=2*1024*1024]
lfs=REPO/'.git/tools/bin/git-lfs'
subprocess.run([str(lfs),'track','--filename',*[str(f.relative_to(REPO)) for f in large]],
               cwd=REPO,check=True,stdout=subprocess.DEVNULL)

# Use a repository-local executable; no global Git configuration is changed.
command=shlex.quote(str(lfs))
for key,value in [('filter.lfs.process',command+' filter-process'),('filter.lfs.clean',command+' clean -- %f'),
                  ('filter.lfs.smudge',command+' smudge -- %f'),('filter.lfs.required','true'),
                  ('alias.lfs','!'+command)]:
    subprocess.run(['git','config',key,value],cwd=REPO,check=True)
for event in ['pre-push','post-commit','post-checkout','post-merge']:
    hook=REPO/'.git/hooks'/event
    hook.write_text('#!/bin/sh\nexec "$(dirname "$0")/../tools/bin/git-lfs" '+event+' "$@"\n')
    hook.chmod(0o755)

previous=json.loads((LIB/'发布整理记录.json').read_text()) if (LIB/'发布整理记录.json').exists() else {}
good_snapshots=[row for row in snapshots if row.get('status')=='downloaded']
record={**previous,'date':datetime.now(ZoneInfo('Asia/Hong_Kong')).date().isoformat(),'repository':'https://github.com/107843099/edu-robot',
        'scope':{'folder':'机器人开发参考库','files':top_files},
        'navigation_files_converted':sorted(set(previous.get('navigation_files_converted',[])+changes)),
        'source_snapshots':len(good_snapshots),'distinct_upstream_repositories':len({row['repo'] for row in good_snapshots}),
        'omitted_os_metadata_files':sum(len(row.get('publication_omitted_files',[])) for row in snapshots),
        'large_file_threshold_bytes':2*1024*1024,'large_files_selected':len(large),
        'large_files_logical_bytes':sum(f.stat().st_size for f in large),
        'redaction_record':'机器人开发参考库/上游源码脱敏记录.json',
        'source_snapshot_policy':'Preserve source and licenses; one recorded credential replacement. Nested ignore rules are bypassed only for explicitly enumerated source files.',
        'hardware_execution':False}
(LIB/'发布整理记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
files += [LIB/'发布整理记录.json',REPO/'README.md',REPO/'.gitignore',REPO/'.gitattributes']
unique=sorted(set(files))
pathspec=REPO/'.git/publish-paths'
pathspec.write_bytes(b'\0'.join(str(f.relative_to(REPO)).encode() for f in unique)+b'\0')
print(json.dumps({'files_enumerated':len(unique),'authored_navigation_files_changed':len(changes),
                  'large_files_selected':len(large),'large_files_logical_bytes':record['large_files_logical_bytes'],
                  'stage_pathspec':'.git/publish-paths'},ensure_ascii=False,indent=2))
