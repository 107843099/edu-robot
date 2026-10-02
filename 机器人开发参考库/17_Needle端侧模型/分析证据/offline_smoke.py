from pathlib import Path
import os,sys,json,time,platform,ctypes
import argparse
args_parser=argparse.ArgumentParser(description='Offline Needle research smoke test: no robot or callable execution')
args_parser.add_argument('--library',required=True,help='Path to a matching Needle3 3.1.0 dynamic library extracted from the platform wheel')
args=args_parser.parse_args()
root=Path(__file__).resolve().parents[3]; project=root/'机器人开发参考库/17_Needle端侧模型'; assets=project/'运行资源/Cactus-Compute__needle3'
os.environ.update(NEEDLE_TELEMETRY='0',DO_NOT_TRACK='1',CI='1',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',NEEDLE3_LIB_PATH=str(Path(args.library).resolve()))
sys.path.insert(0,str(project/'仓库/cactus-compute__needle'))
from needle import Needle
schema=[{'name':'show_expression','description':'Show an expression on the robot face','parameters':{'type':'object','properties':{'expression':{'type':'string','enum':['happy','sad','thinking']}},'required':['expression']}},{'name':'nod','description':'Nod the robot head a specified number of times','parameters':{'type':'object','properties':{'count':{'type':'integer','minimum':1,'maximum':3}},'required':['count']}}]
queries=[('expression_en','Show a happy face.'),('nod_en','Nod twice.'),('refuse_en','Tell me the capital of France.'),('negation_en','Do not nod.'),('expression_zh','请显示开心的表情。'),('nod_zh','点头两次。')]
queries += [('nod_digits_en','Nod 2 times.'),('negation_en_512','Do not nod.'),('expression_zh_512','请显示开心的表情。'),('nod_zh_512','点头两次。')]
start=time.monotonic(); agent=Needle(tools=schema,weights=assets/'needle3.cact',stateless=True,auto_date=False,system='locale: en-US; device: desktop-robot'); load=time.monotonic()-start
rows=[]
try:
 for label,query in queries:
  t=time.monotonic()
  try: result=agent.complete(query,max_new_tokens=512 if label.endswith('_512') else 128); row=dict(label=label,query=query,result=result)
  except Exception as e: row=dict(label=label,query=query,error=f'{type(e).__name__}: {e}')
  row['max_new_tokens']=512 if label.endswith('_512') else 128; row['elapsed_seconds']=round(time.monotonic()-t,3); rows.append(row); print(json.dumps(row,ensure_ascii=False),flush=True)
finally: agent.close()
report=dict(date='2026-10-03',sdk_commit='8881c1ceada54814465fa5edddc6599f32383985',model_revision='c7c415a3d1b3d929014bc6e866d51ebb971f7089',engine='3.1.0 macosx_11_0_x86_64 wheel',host=dict(system=platform.system(),machine=platform.machine(),python=platform.python_version()),telemetry_disabled=True,explicit_local_weights_and_engine=True,robot_connected=False,callables_bound=False,method='complete only; no run; each independent query reset',system_prompt='locale: en-US; device: desktop-robot',prompt_method='system facts per upstream llms.txt; initial instruction-style run archived separately',load_seconds=round(load,3),tool_schemas=schema,rows=rows,scope='Ten synthetic smoke queries with three 512-token follow-ups, not an accuracy or latency benchmark; no ASR, training, device or network integration')
(project/'分析证据').mkdir(exist_ok=True)
(project/'分析证据/离线指令试验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
