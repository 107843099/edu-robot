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
primary=['dorianborian/sesame-robot','RussellCooper-DJZ/manbo-robot-dog','ace-trump-tech/MindPaw','stack-chan/stack-chan','thinking0things/AlbertMicro','ViolinLee/NodeHexa','rookidroid/hexapod','78/xiaozhi-esp32','txp666/ottodiy-docs','M-D-777/EMO-Dot','peng-zhihui/ElectronBot','maker-community/VerdureLab','LuwuDynamics/xgoduck_hardware','KingKongRobotics/jumper','jamro/tiny-engineer','cactus-compute/needle']
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
md=[p for p in ROOT.glob('*.md')]+[p for f in folders for p in f.glob('*.md')]+list(ROOT.parent.glob('*.md'))+[p for f in folders for p in (f/'分析证据').glob('*.md')]
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
hf_verified=0
new_host_checks=[]
needle=ROOT/'17_Needle端侧模型'
if needle.is_dir():
 resources=json.loads((needle/'运行资源下载记录.json').read_text())
 for resource in resources:
  for row in resource['files']:
   p=ROOT.parent/row['saved_path']
   if not p.is_file() or p.stat().st_size!=row['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:errors.append('HF resource hash mismatch '+row['saved_path'])
   else:hf_verified+=1
 audit=json.loads((needle/'分析证据/源码与模型格式核查.json').read_text())
 for row in audit['source_snapshots']:
  if row['mismatches'] or not row['archive_sha256_verified']:errors.append('addition source mismatch '+row['repo'])
 for folder in ['16_TinyEngineer桌面编程机器人','17_Needle端侧模型']:
  report=json.loads((ROOT/folder/'分析证据/主机验证记录.json').read_text())
  if folder.startswith('16') and any(row.get('exit_code')!=0 for row in report['rows']):errors.append('Tiny host check failed')
  new_host_checks.append({'folder':folder,'scope':report['scope'],'physical_robot_test':False})
 smoke=json.loads((needle/'分析证据/离线指令试验.json').read_text())
 if len(smoke['rows'])!=10 or smoke['robot_connected'] or smoke['callables_bound']:errors.append('unexpected Needle smoke scope')
# Local robot attachments are separate from fixed GitHub source snapshots.
local_bundle_audits=[]
def stream_sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
for folder in ['02_曼波小狗','18_桌面小坦克','19_每逢佳节瘦三斤固件生态']:
 p=ROOT/folder/'本地资料来源与校验.json'
 if not p.is_file():errors.append('missing local manifest '+folder);continue
 manifest=json.loads(p.read_text());verified=0;private=0
 for row in manifest['original_files']+manifest['extracted_files']:
  if row.get('saved_path') is None:
   private+=1
   if not (ROOT.parent/row['public_notice']).is_file():errors.append('missing private original notice '+folder)
   continue
  f=ROOT.parent/row['saved_path']
  if not f.is_file() or f.stat().st_size!=row['bytes'] or stream_sha256(f)!=row['sha256']:errors.append('local bundle hash mismatch '+row['saved_path'])
  else:verified+=1
 for entry in manifest.get('archive_only_entries',[]):
  import zipfile
  with zipfile.ZipFile(ROOT.parent/entry['archive']) as archive:
   candidates=[]
   for z in archive.infolist():
    name=z.filename
    if not z.flag_bits&0x800:
     try:name=name.encode('cp437').decode('gb18030')
     except (UnicodeError,LookupError):pass
    if name==entry['archive_entry']:candidates.append(z)
   if len(candidates)!=1 or candidates[0].file_size!=entry['bytes'] or f"{candidates[0].CRC:08x}"!=entry['crc32']:errors.append('archive-only record mismatch '+entry['archive_entry'])
 local_bundle_audits.append({'folder':folder,'original_files_received':len(manifest['original_files']),'public_original_files':len(manifest['original_files'])-private,'public_extracted_files':len(manifest['extracted_files']),'public_files_sha256_verified':verified,'archive_only_entries':len(manifest.get('archive_only_entries',[])),'private_only_originals':private,'physical_test':False})
for folder,file in [('18_桌面小坦克','控制算法主机复核.json'),('19_每逢佳节瘦三斤固件生态','音乐索引离线复核.json')]:
 evidence=json.loads((ROOT/folder/'分析证据'/file).read_text())
 if evidence.get('hardware_test') or not all(x.startswith('PASS') for x in evidence['checks']):errors.append('local host evidence failure '+folder)

result={'project_folders':len(folders),'original_repositories_present':14,'requested_main_repositories_present':len(primary),'downloaded_snapshots':len(good),'distinct_repositories':len({r['repo'] for r in good}),'source_files':source_count,'authored_markdown_docs':len(md),'local_links_checked':links,'lfs_files_hash_verified':lfsok,'local_attachment_audits':local_audits,'hf_resource_files_hash_verified':hf_verified,'new_project_host_checks':new_host_checks,'known_unavailable_entries':[r['repo'] for r in m if r.get('status')!='downloaded'],'errors':errors,'local_robot_bundle_audits':local_bundle_audits,'verification_scope':'File and source-version checks, HF inference resource hashes, local attachment static analysis, fake-serial probes, selected Tiny host checks and Needle SDK/offline inference evidence. Selected tank C controller compiled for host with mock motors and music indexing checked with synthetic files. Local public originals and extracted files hash-verified, archive-only installer checked by ZIP metadata. No full firmware compilation, model training or physical robot tests'}
(ROOT/'资料库校验记录.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
