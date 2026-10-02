// Execute only the isolated TestConnection class with fake ports and writers.
// No DOM startup, navigator.serial, USB, network, installer or firmware execution.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source=fs.readFileSync(path.join(root,'工具包/cardboard-bot-teaching/test-connection.js'),'utf8')
  .replace(/^import .*?;\s*$/m,'').replace('export class TestConnection','class TestConnection');
const scope={reportPort(){},TextEncoder,TextDecoder,setTimeout,clearTimeout,setInterval,clearInterval,Date,
  requestBoardPort(){throw new Error('Real ports forbidden in audit');}};
vm.createContext(scope);
const TestConnection=vm.runInContext(source+'\nTestConnection;',scope);
const rows=[];
function session(step){return {step,robot:step==='robot',matched:false,closing:false,stopped:false,
  mode:'CALIBRATION',writes:Promise.resolve(),resolve(){},reject(){},port:{async close(){}},
  writer:{async write(){},releaseLock(){}},readTask:Promise.resolve()};}
function probe(name,assertion,evidence){rows.push({name,assertion,evidence});if(!assertion)throw new Error(name);}
{
 const c=new TestConnection(null,'0.3',()=>{});const s=session('display');c.session=s;
 c.handleLine(s,'CB_ROBOT version=0.3 oled=1 mode=NORMAL caps=default_center');
 probe('完整系统身份可被屏幕步骤错误接受',s.matched===true && s.robot===false,{matched:s.matched,robot:s.robot,step:s.step});
}
{
 const c=new TestConnection(null,'0.3',()=>{});const s=session('servo_pan');c.session=s;
 c.handleLine(s,'CB_TEST id=servo_tilt version=0.3 oled=1 running=0 result=ready');
 probe('教学步骤错误ID会被拒绝',s.matched===false,{matched:s.matched});
}
for(const step of ['display','robot']){
 const c=new TestConnection(null,'0.3',()=>{});const s=session(step);s.matched=true;c.session=s;const sent=[];
 c.send=async(_,cmd)=>{sent.push(cmd);};await c.disconnect();
 probe(step==='robot'?'完整系统断开不发送停止':'教学断开发送STOP',step==='robot'?sent.length===0:sent.includes('STOP'),{sent});
}
{
 const c=new TestConnection(null,'0.3',()=>{});const s=session('robot');s.matched=true;s.stopped=true;c.session=s;const sent=[];
 c.send=async(_,cmd)=>{sent.push(cmd);};await c.robotCommand('A');
 probe('急停状态微调被网页阻止',sent.length===0,{sent});
 s.stopped=false;s.supportsDefaultCenter=false;await c.robotCommand('B');
 probe('缺少能力标记时默认回中被网页阻止',sent.length===0,{sent});
 c.handleLine(s,'mode=CALIBRATION config=NVS state=IDLE stop=clear servos=enabled pan=90/92 tilt=91/91 irL=0 irR=0 touch=0');
 probe('两轴当前及目标角度可解析',s.panCurrent===90&&s.panTarget===92&&s.tiltCurrent===91,{panCurrent:s.panCurrent,panTarget:s.panTarget,tiltCurrent:s.tiltCurrent});
}
const report={date:'2026-10-02',isolated_component_execution:true,real_serial_access:false,installer_started:false,
 firmware_executed:false,checks:rows.length,rows};
fs.mkdirSync(path.join(root,'逆向证据'),{recursive:true});
fs.writeFileSync(path.join(root,'逆向证据/串口模拟核查结果.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
