import { TestConnection } from './test-connection.js';
import { mountDeviceStatus } from './device-status.js';

mountDeviceStatus();

const oled = [['OLED VCC', '电源模块 3.3V'], ['OLED GND', '公共 GND'], ['OLED SDA', 'GPIO0'], ['OLED SCL / SCK', 'GPIO1']];
const infrared = [['左红外 VCC', '电源模块 3.3V'], ['左红外 GND', '公共 GND'], ['左红外 OUT', 'GPIO4'], ['右红外 VCC', '电源模块 3.3V'], ['右红外 GND', '公共 GND'], ['右红外 OUT', 'GPIO3']];
const servo = (name, pin) => [[name + ' 红线', '电源模块 5V'], [name + ' 棕/黑线', '公共 GND'], [name + ' 黄/橙信号线', pin]];
const touch = [['TTP223 VCC', '电源模块 3.3V'], ['TTP223 GND', '公共 GND'], ['TTP223 OUT', 'GPIO10']];
const common = [['ESP32 USB', '电脑数据 USB 线'], ['ESP32 GND', '电源模块 GND']];
const steps = [
  { id: 'display', title: '屏幕测试', manifest: 'manifest-display.json', need: 'ESP32-C3＋OLED。红外、舵机、触摸全部断开。', wires: [...common, ...oled],
    actions: ['通电后循环显示 HELLO（文字）、BORDER（边框）、棋盘格、INVERT（反色）。', '观察至少一轮：四个画面完整、稳定、没有缺行或闪烁。'],
    pass: '我已看到四种画面完整、稳定。', problems: ['黑屏：确认 OLED 的 VCC 和 GND，恢复外部电源后按 RST。', '仍黑屏：检查 SDA→GPIO0、SCL→GPIO1，不能接反。', '有通信不代表画面正确；花屏时核对是否为本套 128×64 SSD1306 OLED。'] },
  { id: 'infrared', title: '双红外测试', manifest: 'manifest-infrared.json', need: '保留 OLED，接左、右红外。两个舵机与触摸模块断开。', wires: [...common, ...oled, ...infrared],
    actions: ['先移开物体：LEFT（左）和 RIGHT（右）都应为 OFF。', '依次遮挡左、右：对应侧变 ON；再同时遮挡，两侧都 ON；移开都 OFF。'],
    pass: '左、右、同时遮挡、全部移开，四种状态都对应。', problems: ['一直 ON：移开近处物体，逐步调节红外模块灵敏度旋钮。', '左右相反：核对左 OUT→GPIO4、右 OUT→GPIO3。', '一直 OFF：先检查 3.3V 和共地，再靠近模块测试；它不能测量距离。'] },
  { id: 'servo_pan', title: '水平舵机测试', manifest: 'manifest-servo-pan.json', need: '保留 OLED，只接水平舵机。不装舵盘或纸板负载，其他模块断开。', wires: [...common, ...oled, ...servo('水平舵机', 'GPIO5')],
    actions: ['恢复外部电源，按 RST，OLED 显示 READY 后连接测试。', '点击“开始测试”：90°→85°→95°→90°，只执行一轮，结束显示 DONE，PWM 关闭。'],
    pass: '观察到一轮小幅动作，无持续嗡鸣、卡住、异常复位或发热。', problems: ['不动：核对独立 5V、公共 GND、信号 GPIO5。', '无法开始：先确认 OLED 正常，关闭安装窗口后重新连接测试。', '卡住、嗡鸣或发热：立即断开外部电源，检查是否装了舵盘或有负载。'] },
  { id: 'servo_tilt', title: '俯仰舵机测试', manifest: 'manifest-servo-tilt.json', need: '保留 OLED，只接俯仰舵机。水平舵机断开，不装舵盘或负载。', wires: [...common, ...oled, ...servo('俯仰舵机', 'GPIO6')],
    actions: ['恢复外部电源，按 RST，OLED 显示 READY 后连接测试。', '点击“开始测试”：90°→85°→95°→90° 一轮，结束显示 DONE。'],
    pass: '观察到一轮小幅动作，无持续嗡鸣、卡住、异常复位或发热。', problems: ['不动：本步信号接 GPIO6，不能仍接 GPIO5。', '提示固件不匹配：断开测试，刷第 04 步，再重连。', '抖动、重启或发热：立即断开外部电源，检查 5V 供电和共地。'] },
  { id: 'touch', title: '触摸模块测试', manifest: 'manifest-touch.json', need: '保留 OLED，只接 TTP223。两个舵机与红外断开。', wires: [...common, ...oled, ...touch],
    actions: ['触摸金属感应区，显示 TOUCHED；松开后显示 OPEN。', '连续触摸、松开 5 次：COUNT 每次触摸只加 1，按住不应反复增加。'],
    pass: '五次触摸与松开均正常，计数每次加一。', problems: ['无变化：检查 OUT→GPIO10、3.3V 和 GND。', '松手不恢复：核对 TTP223 是否为点动模式，不是自锁模式。', '隔纸板不灵敏：先直接触摸裸模块，装配后的灵敏度另行验证。'] },
  { id: 'robot', title: '完整系统', manifest: 'manifest.json', need: '全部模块。安装舵盘前先用完整固件校准回中；整机测试时确认结构无干涉。', wires: [...common, ...oled, ...infrared, ...servo('水平舵机', 'GPIO5'), ...servo('俯仰舵机', 'GPIO6'), ...touch],
    actions: ['装配前先刷完整固件，按下方“装配前校准”说明回中，再安装舵盘与结构。若已装好，先确认中位与运动空间正确。', '完成左右跟随流程合计 10 次；观察默认、搜索、摸头三种表情。', '摸头 5 次，连续运行 2 分钟；确认跟随时自然抬头，无错误方向、撞限位、异常复位或发热。完整固件上电会启用动作。'],
    pass: '完整系统按上述项目观察通过。', problems: ['单模块正常、组装后异常：先断电检查接线松动、公共 GND 和机械干涉。', '舵机方向或中位不对：停止，返回完整固件校准流程。', '动作时重启、嗡鸣或发热：立即切断外部电源，检查供电与卡住位置。'] }
];

let active = 'display';
let controller;
let serialState = {};
let version = '';
const root = document.querySelector('#steps');
const panels = new Map();


const nav = document.createElement('nav');
nav.className = 'step-nav';
nav.setAttribute('aria-label', '按顺序选择教学步骤');
root.before(nav);

const POWER_WIRE_COLOR = "#ff0000";
const GROUND_WIRE_COLOR = "#000000";
const SIGNAL_WIRE_COLORS = ["#0057ff", "#00b83f", "#ffd000"];

function wiringSvg(wires, title) {
  const h = 42 + wires.length * 27;
  let signalIndex = 0;
  return `<svg viewBox="0 0 540 ${h}" role="img" aria-label="${title}逐线连接示意"><title>${title}接线示意</title>
    <text x="16" y="20">模块引脚 / 线色</text><text x="345" y="20">接到这里</text>` +
    wires.map(([from, to], i) => {
      const y = 42 + i * 27;
      const isGroundWire = /GND/.test(from + " " + to);
      const isPowerWire = /USB|VCC|3\.3V|5V/.test(from + " " + to);
      const color = isGroundWire ? GROUND_WIRE_COLOR : isPowerWire ? POWER_WIRE_COLOR : SIGNAL_WIRE_COLORS[signalIndex++ % SIGNAL_WIRE_COLORS.length];
      return `<text x="16" y="${y}" dominant-baseline="middle">${from}</text><path d="M 217 ${y} H 330" stroke="${color}" stroke-width="2"/><circle cx="217" cy="${y}" r="3" fill="${color}"/><circle cx="330" cy="${y}" r="3" fill="${color}"/><text x="345" y="${y}" dominant-baseline="middle">${to}</text>`;
    }).join('') + '</svg>';
}

function updateControls(state) {
  serialState = state;
  const locked = state.connected || state.busy;
  for (const [id, panel] of panels) {
    panel.install.disabled = !!locked || !version;
    panel.connect.disabled = !!locked || !version;
    panel.disconnect.disabled = !state.connected || state.step !== id;
    panel.start.disabled = !state.ready || state.step !== id || state.running || state.starting;
    panel.stop.disabled = !state.connected || state.step !== id;
    if (state.step === id || (!locked && id === active)) {
      panel.status.textContent = state.message;
      panel.status.classList.toggle('error', !!state.error);
    }
    if (panel.calibrationState) {
      const robotReady = !!state.connected && state.step === id && !!state.ready;
      const modeNames = { NORMAL: '正常运行', CALIBRATION: '校准模式', SELF_TEST: '自检模式' };
      const angles = Number.isFinite(state.panCurrent) && Number.isFinite(state.tiltCurrent)
        ? `水平 ${state.panCurrent}°→${state.panTarget}°；俯仰 ${state.tiltCurrent}°→${state.tiltTarget}°`
        : '角度等待读取';
      const drive = state.stopped ? '急停已生效，PWM 已关闭' : (state.servoEnabled ? '舵机驱动已启用' : '舵机驱动未启用');
      panel.calibrationState.textContent = robotReady
        ? `模式：${modeNames[state.mode] || state.mode || '读取中'}；${angles}；${drive}。`
        : '尚未连接并识别第 06 步完整系统固件。';
      for (const button of panel.robotButtons) {
        const command = button.dataset.robotCommand;
        if (command === 'X') button.disabled = !robotReady || state.stopped;
        else if (command === 'R') button.disabled = !robotReady || !state.stopped;
        else if (command === '2') button.disabled = !robotReady || state.mode === 'CALIBRATION';
        else if (command === '1') button.disabled = !robotReady || state.mode === 'NORMAL' || state.stopped;
        else if (command === 'B') button.disabled = !robotReady || !state.supportsDefaultCenter || state.mode !== 'CALIBRATION' || state.stopped;
        else button.disabled = !robotReady || state.mode !== 'CALIBRATION' || state.stopped;
      }
    }
  }
  nav.querySelectorAll('button').forEach(button => { button.disabled = !!locked; });
}

function select(id) {
  if (serialState.connected || serialState.busy) return;
  active = id;
  for (const [key, panel] of panels) panel.card.hidden = key !== id;
  nav.querySelectorAll('button').forEach(button => button.setAttribute('aria-current', button.dataset.step === id ? 'step' : 'false'));
}

for (const [index, step] of steps.entries()) {
  const no = String(index + 1).padStart(2, '0');
  const choice = document.createElement('button');
  choice.type = 'button';
  choice.dataset.step = step.id;
  choice.innerHTML = `<span>${no}</span>${step.title}`;
  choice.addEventListener('click', () => select(step.id));
  nav.append(choice);
  const card = document.createElement('article');
  card.className = 'step-card';
  card.id = 'step-' + step.id;
  const isServo = step.id.startsWith('servo_');
  const isRobot = step.id === 'robot';
  const robotCalibration = isRobot ? `<div class="calibration-controls">
    <div class="info-label">装配前校准 · 完整固件</div>
    <ol><li>首次装配先断电取下舵盘和纸板负载，再上电连接完整系统。</li><li>点击“进入校准”→“恢复默认中位”，到 90°并停稳后断电，朝正装回舵盘。</li><li>重新上电后按需微调，每次 1°；点击“保存自定义中位”会同时保存水平和俯仰。</li></ol>
    <p class="calibration-state" data-calibration-state>尚未连接完整系统固件。</p>
    <div class="calibration-grid">
      <button type="button" class="secondary-action" data-robot-command="2" disabled>进入校准</button>
      <button type="button" class="secondary-action" data-robot-command="B" disabled>恢复默认中位</button>
      <button type="button" class="secondary-action" data-robot-command="C" disabled>回到自定义中位</button>
      <button type="button" class="secondary-action" data-robot-command="A" disabled>水平向左 −1°</button>
      <button type="button" class="secondary-action" data-robot-command="D" disabled>水平向右 +1°</button>
      <button type="button" class="secondary-action" data-robot-command="W" disabled>俯仰向上 +1°</button>
      <button type="button" class="secondary-action" data-robot-command="S" disabled>俯仰向下 −1°</button>
      <button type="button" class="secondary-action save-action" data-robot-command="V" disabled>保存自定义中位</button>
      <button type="button" class="secondary-action" data-robot-command="1" disabled>返回正常模式</button>
      <button type="button" class="secondary-action emergency-action" data-robot-command="X" disabled>立即急停</button>
      <button type="button" class="secondary-action" data-robot-command="R" disabled>恢复舵机驱动</button>
    </div>
    <p class="note"><strong>安全：</strong>默认回中不覆盖自定义中位，但回中和微调都会让舵机动作。持续嗡鸣、撞限位、卡住、复位或发热时，立即切断外部 12V；“恢复舵机驱动”不会自动回中。断开连接只释放串口，不会替你急停。</p>
  </div>` : '';
  card.innerHTML = `<div class="card-title"><span class="number">${no}</span><div><h2>${step.title}</h2><p>${step.need}</p></div></div>
    <div class="card-grid"><div>
      <div class="info-block"><div class="info-label">怎么接线 · 断开全部电源后操作</div>${wiringSvg(step.wires, step.title)}
        <p>ESP32 只用 USB 供电。模块标注和线色以实物为准；外部电源不可接到 ESP32 电源脚。首次使用电源模块先空载测量 3.3V 与 5V 输出。</p>
      </div>
      <div class="info-block"><div class="info-label">怎样判断通过</div><ol>${step.actions.map(a => `<li>${a}</li>`).join('')}</ol>
        <label class="observed"><input type="checkbox"> ${step.pass}</label><p class="note">此勾选仅表示你的现场观察，本页不会自动判断硬件通过；刷新后清除。</p>
      </div>
    </div><div>
      <div class="info-block"><div class="info-label">简化版 ESP32-C3 · 安装前手动进入下载模式</div><p>只接 ESP32 USB，按住 BOOT → 按下 RESET（RST）→ 松开 RESET → 松开 BOOT。等待 USB 设备重新出现，再点击安装并选择当前端口；端口号可能变化。</p><p>写入过程中不要按 BOOT / RESET 或拔 USB。显示安装成功后关闭安装窗口，恢复本步模块电源并按一次 RESET，然后连接测试。下载模式下不能进行功能测试。</p></div>
      <div class="info-block"><div class="info-label">先刷固件，再恢复模块电源</div><ol><li>关闭外部电源，只接电脑 USB，点击下方安装按钮。</li><li>完成后关闭安装窗口，恢复外部电源并按一次 RST，让屏幕重新初始化。</li><li>${isServo ? '确认无舵盘、无负载，再连接测试并点击开始。' : isRobot ? '按左侧说明观察；第 06 步连接完整系统后可使用校准按钮。' : '按左侧说明观察；连接测试可核对通信。'}</li></ol></div>
      <esp-web-install-button manifest="./${step.manifest}"><button slot="activate" class="install-action" type="button" disabled>安装 ${no} · ${step.title}</button><span slot="unsupported" class="slot-message">请使用最新版 Chrome 或 Edge。</span><span slot="not-allowed" class="slot-message">请通过 HTTPS 或 localhost 打开，不要直接双击 HTML。</span></esp-web-install-button>
      <div class="test-controls">
        <div class="action-row"><button type="button" class="secondary-action" data-connect disabled>${isRobot ? '连接完整系统' : '连接测试'}</button><button type="button" class="secondary-action" data-disconnect disabled>${isRobot ? '断开连接' : '断开测试'}</button></div>
        <p class="status" role="status"></p>
        <div class="action-row" ${isServo ? '' : 'hidden'}><button type="button" class="secondary-action" data-start disabled>开始测试</button><button type="button" class="secondary-action stop-action" data-stop disabled>立即停止</button></div>
        ${robotCalibration}
      </div>
      ${isServo ? '<p class="note">首次回到 90° 的动作取决于舵机原位置，所以必须空载。网页断线后固件最多约 2 秒停止 PWM；异常时直接切断外部电源。测试不能代替装配回中。</p>' : ''}
      <div class="info-block troubleshooting"><div class="info-label">不正常怎么办</div><ul>${step.problems.map(p => `<li>${p}</li>`).join('')}</ul></div>
    </div></div>`;
  root.append(card);
  const panel = { card, install: card.querySelector('.install-action'), connect: card.querySelector('[data-connect]'),
    disconnect: card.querySelector('[data-disconnect]'), start: card.querySelector('[data-start]'), stop: card.querySelector('[data-stop]'), status: card.querySelector('.status'),
    calibrationState: card.querySelector('[data-calibration-state]'), robotButtons: [...card.querySelectorAll('[data-robot-command]')] };
  panels.set(step.id, panel);
  panel.connect.addEventListener('click', () => controller?.connect(step.id));
  panel.disconnect.addEventListener('click', () => controller?.disconnect());
  panel.start.addEventListener('click', () => controller?.start());
  panel.stop.addEventListener('click', () => controller?.stop());
  panel.robotButtons.forEach(button => button.addEventListener('click', () => controller?.robotCommand(button.dataset.robotCommand)));
}
select(active);
try {
  const response = await fetch('./release.json');
  if (!response.ok) throw new Error('发布清单加载失败，请重新解压完整安装包。');
  const release = await response.json();
  version = release.version;
  document.querySelector('.version').textContent = '分步教学 · V' + version;
  controller = new TestConnection(navigator.serial, version, updateControls);
  updateControls({ message: '' });
} catch (error) { updateControls({ message: error.message, error: true }); }
document.addEventListener('visibilitychange', () => {
  if (document.hidden && controller?.session) void controller.disconnect('页面已离开前台，测试已停止并断开。');
});
window.addEventListener('pagehide', () => { void controller?.disconnect(); });
