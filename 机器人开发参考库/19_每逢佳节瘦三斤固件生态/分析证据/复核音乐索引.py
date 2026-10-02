"""Run selected unchanged MusicManager code against synthetic temporary files. No server/network/robot."""
from pathlib import Path
import ast,os,struct,hashlib,tempfile,json
from typing import List,Dict,Optional
ROOT=Path(__file__).resolve().parents[1];source=next(ROOT.glob('本地资料/**/music_server/server.py'));raw=source.read_bytes()
tree=ast.parse(raw.decode('utf-8-sig'));selected=[n for n in tree.body if (isinstance(n,ast.ClassDef) and n.name=='MusicManager') or (isinstance(n,ast.FunctionDef) and n.name=='iter_faststart')]
ns={'os':os,'Path':Path,'struct':struct,'hashlib':hashlib,'List':List,'Dict':Dict,'Optional':Optional,'__file__':str(source)}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),ns);checks=[]
with tempfile.TemporaryDirectory(prefix='music-index-') as td:
 p=Path(td);(p/'Composer').mkdir()
 for name in ['Composer - Song.mp3','Title-Artist.flac','other.aac','sample.wav','sample.m4a','ignored.ogg','Composer/Fallback.mp3']:(p/name).write_bytes(b'SYNTHETIC NOT AUDIO')
 (p/'Composer - Song.lrc').write_text('[00:01.00] synthetic test line',encoding='utf-8');mgr=ns['MusicManager'](str(p))
 assert len(mgr.songs)==6;checks.append('PASS five formats scanned; OGG excluded')
 s=mgr.search('Song')['data'][0];assert (s['title'],s['artist'])==('Song','Composer');checks.append('PASS spaced separator artist-first')
 s2=mgr.search('Title')['data'][0];assert (s2['title'],s2['artist'])==('Title','Artist');checks.append('PASS unspaced separator title-first')
 assert mgr.search('composer')['total']==2;checks.append('PASS case normalization and directory artist fallback')
 assert len(mgr.list_all(2,2)['data'])==2;checks.append('PASS pagination')
 assert mgr.get_lyrics(s['id']).startswith('[00:01.00]');assert mgr.get_song('missing') is None;checks.append('PASS UTF-8 LRC and missing song')
 old=s['id'];(p/'Composer - Song.mp3').write_bytes(b'CHANGED SYNTHETIC');mgr.rescan();assert mgr.search('Song')['data'][0]['id']==old;checks.append('PASS IDs depend on relative path rather than content')
 def box(typ,data):return struct.pack('>I4s',8+len(data),typ)+data
 ftyp=box(b'ftyp',b'xxxx');mdat=box(b'mdat',b'not audio');moov=box(b'moov',b'fake metadata');movie=p/'synthetic.m4a';movie.write_bytes(ftyp+mdat+moov)
 order=mgr.get_faststart_order(str(movie));assert b''.join(ns['iter_faststart'](str(movie),order))==ftyp+moov+mdat;checks.append('PASS synthetic MP4 box reorder without transcoding')
 movie.write_bytes(ftyp+moov+mdat);assert mgr.get_faststart_order(str(movie)) is None;checks.append('PASS already faststart uses original order')
 report={'date':'2026-10-03','scope':'AST extraction of original MusicManager and iter_faststart only; synthetic filenames, fake audio bytes, LRC and MP4 boxes. No FastAPI server, network download, genuine audio decode or firmware client.','source_sha256':hashlib.sha256(raw).hexdigest(),'checks':checks,'check_count':len(checks),'hardware_test':False,'network_used':False}
 (ROOT/'分析证据/音乐索引离线复核.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
