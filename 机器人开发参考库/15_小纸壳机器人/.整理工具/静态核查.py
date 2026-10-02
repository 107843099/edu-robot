"""Read-only package audit. Never opens serial ports or runs firmware/startup scripts."""
from pathlib import Path
import hashlib, json, re, struct, zipfile, sys

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / '工具包/cardboard-bot-teaching'
OUT = ROOT / '逆向证据'
OUT.mkdir(exist_ok=True)
errors = []
def sha(data): return hashlib.sha256(data).hexdigest()
def save(name, value): (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2))

sources = json.loads((ROOT/'来源与版本.json').read_text())
for row in sources:
    for key in ['original_path', 'saved_path']:
        source_path = Path(row[key])
        if not source_path.is_absolute(): source_path = ROOT.parents[1] / source_path
        data = source_path.read_bytes()
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            errors.append('source mismatch: ' + key + ' ' + row['name'])
archive = next(Path(r['saved_path']) for r in sources if r['name'].endswith('.zip'))
if not archive.is_absolute(): archive = ROOT.parents[1] / archive
with zipfile.ZipFile(archive) as z:
    if z.testzip(): errors.append('ZIP CRC failure')
    members = [i for i in z.infolist() if not i.is_dir()]
    for entry in members:
        if sha(z.read(entry)) != sha((ROOT/'工具包'/entry.filename).read_bytes()):
            errors.append('extraction mismatch: ' + entry.filename)

release = json.loads((PKG/'release.json').read_text())
checked = []
images = []
strings = []
for step in release['steps']:
    manifest = json.loads((PKG/step['manifest']).read_text())
    parts = manifest['builds'][0]['parts']
    if [(r['path'],r['offset']) for r in parts] != [(r['path'],r['offset']) for r in step['parts']]:
        errors.append('manifest mismatch: '+step['id'])
    for part in step['parts']:
        data = (PKG/part['path']).read_bytes()
        ok = len(data)==part['bytes'] and sha(data)==part['sha256']
        checked.append({'path':part['path'],'offset':hex(part['offset']), 'bytes':len(data), 'sha256':sha(data),'matches_release':ok})
        if not ok: errors.append('release mismatch: '+part['path'])
    data = (PKG/step['parts'][-1]['path']).read_bytes()
    offset = 24; segments = []; checksum = 0xef
    for _ in range(data[1]):
        address, size = struct.unpack_from('<II', data, offset)
        begin = offset+8
        for byte in data[begin:begin+size]: checksum ^= byte
        segments.append({'file_offset':begin, 'size':size,'load_address':hex(address)})
        offset = begin+size
    checksum_at = offset | 15
    checksum_ok = data[checksum_at] == checksum
    digest_ok = data[checksum_at+1:checksum_at+33] == hashlib.sha256(data[:checksum_at+1]).digest()
    if not checksum_ok or not digest_ok: errors.append('image integrity mismatch: '+step['id'])
    images.append({'step':step['id'],'magic':hex(data[0]),'chip_id':struct.unpack_from('<H',data,12)[0],
                   'flash_size_mb':2**(data[3]>>4), 'entry_point':hex(struct.unpack_from('<I',data,4)[0]),
                   'segments':segments,'checksum_ok':checksum_ok,'appended_sha256_ok':digest_ok})
    for match in re.finditer(rb'[\x20-\x7e]{3,}',data[:0x2000]):
        strings.append({'step':step['id'],'file_offset':hex(match.start()),'text':match.group().decode()})
save('固件镜像与校验.json', {'release_files':checked,'application_images':images})
save('应用字符串定位.json',strings)

data = (PKG/'firmware/teaching/06-robot/partitions.bin').read_bytes()
partitions = []
for offset in range(0,len(data),32):
    if data[offset:offset+2]!=b'\xaa\x50': break
    _,typ,sub,start,size,label,flags=struct.unpack_from('<HBBII16sI',data,offset)
    partitions.append({'name':label.rstrip(b'\0').decode(),'type':typ,'subtype':sub,
                       'offset':hex(start),'size':hex(size),'end_exclusive':hex(start+size),'flags':flags})
save('分区表还原.json',partitions)

vendor = next((PKG/'vendor/esp-web-tools').glob('install-dialog-*.js'))
content = vendor.read_text()
snippets=[]
for pattern in ['_renderDashboardNoImprov()', 'this._manifest.new_install_prompt_erase?this._state="ASK_ERASE":this._startInstall(!0)',
                '_startInstall(e){', 'this._installErase', 'eraseFlash()', 'eraseAll:!1']:
    for match in re.finditer(re.escape(pattern),content):
        snippets.append({'file':str(vendor.relative_to(PKG)),'pattern':pattern,'character_offset':match.start(),
                         'line':content.count('\n',0,match.start())+1,'context':content[max(0,match.start()-180):match.end()+240]})
save('安装器擦除路径摘录.json',snippets)

binary = (PKG/'firmware/teaching/06-robot/firmware.bin').read_bytes()
defaults = list(struct.unpack_from('<6i',binary,0x120))
save('校准默认数据.json',{'file':'firmware/teaching/06-robot/firmware.bin','offset':'0x120',
                         'order':['pan_center','pan_min','pan_max','tilt_center','tilt_min','tilt_max'],
                         'values':defaults,'interpretation':'Data cross-checked with the copy and validation routines; not physical travel limits.'})

# Optional instruction decoding dependency, kept outside the original package.
if len(sys.argv)>1: sys.path.insert(0,sys.argv[1])
try:
    from capstone import Cs, CS_ARCH_RISCV, CS_MODE_RISCV32, CS_MODE_RISCVC
except ImportError:
    decoded=False
else:
    decoded=True; disassembler=Cs(CS_ARCH_RISCV,CS_MODE_RISCV32|CS_MODE_RISCVC)
    tasks = [('06-robot',[(0x20072,0x201ea),(0x201ea,0x20512),(0x20512,0x20e00),(0x210c0,0x21260)]),
             ('03-servo-pan',[(0x10300,0x10450)])]
    for folder,ranges in tasks:
        data=(PKG/f'firmware/teaching/{folder}/firmware.bin').read_bytes()
        offset=24; segments=[]
        for _ in range(data[1]):
            address,size=struct.unpack_from('<II',data,offset);segments.append((offset+8,size,address));offset+=8+size
        lines=['# RISC-V 32 + compressed instructions. File offset and mapped virtual address are separate.']
        for begin,end in ranges:
            seg=next(s for s in segments if s[0]<=begin<s[0]+s[1])
            virtual=seg[2]+begin-seg[0]
            lines.append(f'\n# File range {begin:#x}..{end:#x}, mapped start {virtual:#x}')
            for ins in disassembler.disasm(data[begin:end],virtual):
                file_offset=begin+ins.address-virtual
                lines.append(f'{file_offset:08x}  {ins.address:08x}  {ins.bytes.hex():12}  {ins.mnemonic:12} {ins.op_str}')
        (OUT/f'{folder}_关键指令.txt').write_text('\n'.join(lines)+'\n')

report={'date':'2026-10-02','source_files_verified':len(sources),'archive_files_verified':len(members),
        'release_files_verified':len(checked),'manifests_verified':len(images),'application_images_verified':len(images),
        'embedded_c_cpp_source_files':len([p for p in PKG.rglob('*') if p.suffix in ['.ino','.cpp','.h','.c']]),
        'instruction_decoding_performed':decoded,'errors':errors,
        'scope':'File checks, image decoding, string and selected RISC-V instruction analysis only. No serial I/O, flashing, firmware execution or physical tests.'}
save('静态核查结果.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
