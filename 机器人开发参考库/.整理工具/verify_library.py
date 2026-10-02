from pathlib import Path
import json,re,os,hashlib
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'仓库下载清单.json').read_text());good=[r for r in m if r.get('status')=='downloaded'];errors=[]
source_count=0
for r in good:
 p=ROOT/r['relative_path']
 if not p.is_dir():errors.append('missing snapshot '+str(p));continue
 omitted=set(r.get('publication_omitted_files',[]))
 if any(Path(name).name!='.DS_Store' for name in omitted):errors.append('unexpected publication omission '+r['repo'])
 count=sum(1 for base,_,fs in os.walk(p) for name in fs if str((Path(base)/name).relative_to(p)) not in omitted);source_count+=count
 expected=r['file_count']-len(omitted)
 if count!=expected:errors.append(f"file count mismatch {r['repo']} {count} != {expected}")
 if not re.fullmatch('[a-f0-9]{40}',r['commit']):errors.append('invalid commit '+r['repo'])
 if not re.fullmatch('[a-f0-9]{64}',r['archive_sha256']):errors.append('invalid zip hash '+r['repo'])
primary=['dorianborian/sesame-robot','RussellCooper-DJZ/manbo-robot-dog','ace-trump-tech/MindPaw','stack-chan/stack-chan','thinking0things/AlbertMicro','ViolinLee/NodeHexa','rookidroid/hexapod','78/xiaozhi-esp32','txp666/ottodiy-docs','M-D-777/EMO-Dot','peng-zhihui/ElectronBot','maker-community/VerdureLab','LuwuDynamics/xgoduck_hardware','KingKongRobotics/jumper']
for repo in primary:
 if repo not in {r['repo'] for r in good}:errors.append('missing original '+repo)
folders=[p for p in ROOT.iterdir() if p.is_dir() and re.match(r'^\d\d_',p.name)]
for p in folders:
 for name in ['README.md','配套生态与代码导读.md','仓库阅读记录.md','来源与版本.json']:
  if not (p/name).is_file():errors.append('missing project document '+str(p/name))
 for name in ['README.md','配套生态与代码导读.md']:
  if (p/name).exists():
   body=re.sub(r'\]\(<[^>]+>\)',']',(p/name).read_text())
   if len(body)<500:errors.append('too brief '+str(p/name))
md=[p for p in ROOT.glob('*.md')]+[p for f in folders for p in f.glob('*.md')]+list(ROOT.parent.glob('*.md'))
links=0
for p in md:
 text=p.read_text()
 for target in re.findall(r'\]\(<([^>]+)>\)',text):
  if not urlsplit(target).scheme and not target.startswith('#'):
   links+=1
   link_path=Path(unquote(urlsplit(target).path))
   resolved=link_path if link_path.is_absolute() else p.parent/link_path
   if not resolved.exists():errors.append('broken local link '+str(p)+': '+target)
lf=json.loads((ROOT/'14_Jumper螃蟹机器人'/'LFS下载记录.json').read_text());design=next(r for r in good if r['repo']=='KingKongRobotics/jumper-design');lfsok=0
for row in lf:
 p=ROOT/design['relative_path']/row['path']
 if row['status']!='materialized' or not p.is_file():errors.append('missing LFS '+row['path']);continue
 if p.stat().st_size!=row['expected_size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=row['oid_sha256']:errors.append('LFS hash mismatch '+row['path'])
 else:lfsok+=1
local_audits=[]
paper=ROOT/'15_小纸壳机器人'
if paper.is_dir():
 for name in ['第一版制作与验收清单.md','物料接线与机构拆解.md','逆向分析与自研迁移方案.md']:
  if not (paper/name).is_file():errors.append('missing cardboard document '+name)
 static=json.loads((paper/'逆向证据/静态核查结果.json').read_text())
 probes=json.loads((paper/'逆向证据/串口模拟核查结果.json').read_text())
 if static['errors']:errors.append('cardboard static audit has errors')
 if not all(r['assertion'] for r in probes['rows']):errors.append('cardboard isolated probe failed')
 local_audits.append({'folder':paper.name,'source_files_verified':static['source_files_verified'],'archive_files_verified':static['archive_files_verified'],'release_files_verified':static['release_files_verified'],'isolated_serial_probes':probes['checks'],'physical_tests':False})
result={'project_folders':len(folders),'original_repositories_present':len(primary),'downloaded_snapshots':len(good),'distinct_repositories':len({r['repo'] for r in good}),'source_files':source_count,'authored_markdown_docs':len(md),'local_links_checked':links,'lfs_files_hash_verified':lfsok,'local_attachment_audits':local_audits,'known_unavailable_entries':[r['repo'] for r in m if r.get('status')!='downloaded'],'errors':errors,'verification_scope':'File and source-version checks; local attachment static analysis and isolated fake-serial probes. No firmware compilation, model training or physical robot tests'}
(ROOT/'资料库校验记录.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
