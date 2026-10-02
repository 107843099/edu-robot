import { TestConnection } from './test-connection.js';
import { mountDeviceStatus } from './device-status.js';

mountDeviceStatus();

const oled = [['OLED VCC', '电源模块 3.3V'], ['OLED GND', '公共 GND'], ['OLED SDA', 'GPIO0'], ['OLED SCL / SCK', 'GPIO1']];
const infrared = [['左红外 VCC', '电源模块 3.3V'], ['左红外 GND', '公共 GND'], ['左红外 OUT', 'GPIO4'], ['右红外 VCC', '电源模块 3.3V'], ['右红外 GND', '公共 GND'], ['右红外 OUT', 'GPIO3']];
const servo = (name, pin) => [[name + ' 红线', '电源模块 5V'], [name + ' 棕/黑线', '公共 GND'], [name + ' 黄/橙信号线', pin]];
const touch = [['TTP223 VCC', '电源模块 3.3V'], ['TTP223 GND', '公共 GND'], ['TTP223 OUT', 'GPIO10']];
const common = [['ESP32 USB', '电脑数据 USB 线'], ['ESP32 GND', '电源模块 GND']];

const steps = [
  {
    id: 'display', nav: '屏幕', title: '屏幕测试', manifest: 'manifest-display.json',
    need: 'ESP32-C3 ＋ OLED', wires: [...common, ...oled],
    parts: [['board', 'ESP32-C3'], ['oled', 'OLED 0.96"']],
    test: '恢复 OLED 的 3.3V 电源，按一下 RST，等待屏幕开始循环。',
    actions: ['依次出现 HELLO、边框、棋盘格和反色画面。', '完整观察一轮，画面稳定，没有缺行或闪烁。'],
    pass: '四种画面都完整、稳定。',
    problems: ['黑屏：检查 OLED 的 VCC、GND，再按一次 RST。', '仍黑屏：核对 SDA→GPIO0、SCL→GPIO1。', '花屏：确认使用的是 128×64 SSD1306 OLED。']
  },
  {
    id: 'infrared', nav: '红外', title: '双红外测试', manifest: 'manifest-infrared.json',
    need: '保留 OLED，增加左右红外', wires: [...common, ...oled, ...infrared],
    parts: [['board', 'ESP32-C3'], ['oled', 'OLED'], ['ir', '左红外 LM393'], ['ir', '右红外 LM393']],
    test: '恢复 OLED 和红外模块的 3.3V 电源，按一下 RST。',
    actions: ['遮挡左侧时 LEFT 变为 ON；遮挡右侧时 RIGHT 变为 ON。', '同时遮挡时两侧都为 ON；全部移开时都为 OFF。'],
    pass: '左、右、同时遮挡和全部移开都对应。',
    problems: ['一直 ON：移开近处物体，慢慢调节灵敏度旋钮。', '左右相反：核对左 OUT→GPIO4、右 OUT→GPIO3。', '一直 OFF：先检查 3.3V 和公共 GND。']
  },
  {
    id: 'servo_pan', nav: '水平舵机', title: '水平舵机测试', manifest: 'manifest-servo-pan.json',
    need: '保留 OLED，只接水平舵机', wires: [...common, ...oled, ...servo('水平舵机', 'GPIO5')],
    parts: [['board', 'ESP32-C3'], ['oled', 'OLED'], ['servo', 'SG90 水平舵机'], ['power', '多路电源模块']],
    test: '取下舵盘和负载，恢复 OLED 3.3V 与舵机 5V，按一下 RST。',
    actions: ['连接后点击“开始测试”，舵机只做一轮小幅动作。', '动作顺序为 90°→85°→95°→90°，完成后停止。'],
    pass: '动作平稳，没有持续嗡鸣、卡住、复位或发热。',
    problems: ['不动：核对外部 5V、公共 GND 和 GPIO5。', '无法开始：先确认 OLED 正常，再重新连接。', '嗡鸣、卡住或发热：立即切断外部电源。']
  },
  {
    id: 'servo_tilt', nav: '俯仰舵机', title: '俯仰舵机测试', manifest: 'manifest-servo-tilt.json',
    need: '保留 OLED，只接俯仰舵机', wires: [...common, ...oled, ...servo('俯仰舵机', 'GPIO6')],
    parts: [['board', 'ESP32-C3'], ['oled', 'OLED'], ['servo', 'SG90 俯仰舵机'], ['power', '多路电源模块']],
    test: '取下舵盘和负载，恢复 OLED 3.3V 与舵机 5V，按一下 RST。',
    actions: ['连接后点击“开始测试”，舵机只做一轮小幅动作。', '动作顺序为 90°→85°→95°→90°，完成后停止。'],
    pass: '动作平稳，没有持续嗡鸣、卡住、复位或发热。',
    problems: ['不动：本步信号接 GPIO6。', '提示程序不匹配：重新安装第 04 步程序。', '抖动、复位或发热：立即切断外部电源。']
  },
  {
    id: 'touch', nav: '触摸', title: '触摸模块测试', manifest: 'manifest-touch.json',
    need: '保留 OLED，只接 TTP223', wires: [...common, ...oled, ...touch],
    parts: [['board', 'ESP32-C3'], ['oled', 'OLED'], ['touch', 'TTP223 触摸模块']],
    test: '恢复 OLED 和触摸模块的 3.3V 电源，按一下 RST。',
    actions: ['按住感应区时显示 TOUCHED，松开后显示 OPEN。', '连续触摸 5 次，COUNT 每次只增加 1。'],
    pass: '五次触摸和松开都正常，计数每次加一。',
    problems: ['无变化：检查 OUT→GPIO10、3.3V 和 GND。', '松手不恢复：确认模块不是自锁模式。', '隔纸板不灵敏：先直接触摸裸模块测试。']
  },
  {
    id: 'robot', nav: '完整系统', title: '完整系统', manifest: 'manifest.json',
    need: '全部模块', wires: [...common, ...oled, ...infrared, ...servo('水平舵机', 'GPIO5'), ...servo('俯仰舵机', 'GPIO6'), ...touch],
    parts: [['board', 'ESP32-C3'], ['oled', 'OLED'], ['ir', '左右红外'], ['servo', '两个 SG90'], ['touch', 'TTP223'], ['power', '多路电源模块']],
    test: '确认舵机中位和机械活动空间，再恢复模块电源并按一下 RST。',
    actions: ['左右跟随合计测试 10 次，方向正确，动作自然。', '摸头 5 次并连续运行 2 分钟，没有撞限位、复位或发热。'],
    pass: '完整系统按上述项目观察通过。',
    problems: ['组装后异常：先断电检查接线、公共 GND 和机械干涉。', '方向或中位不对：停止动作，使用下方校准。', '重启、嗡鸣或发热：立即切断外部电源。']
  }
];

const phases = [
  ['wiring', '接线'],
  ['install', '安装程序'],
  ['test', '通电测试'],
  ['result', '确认结果']
];

const pinColors = {
  GPIO0: '#0057ff',
  GPIO1: '#00b83f',
  GPIO3: '#0057ff',
  GPIO4: '#ffd000',
  GPIO5: '#00b83f',
  GPIO6: '#ffd000',
  GPIO10: '#0057ff'
};

function wireColor(from, to) {
  const text = from + ' ' + to;
  if (/GND|棕\/黑/.test(text)) return '#000000';
  if (/USB|VCC|3\.3V|5V|红线/.test(text)) return '#ff0000';
  const pin = Object.keys(pinColors).find(name => text.includes(name));
  return pinColors[pin] || '#0057ff';
}

function wiringSvg(wires, title) {
  const h = 35 + wires.length * 25;
  return `<svg viewBox="0 0 540 ${h}" role="img" aria-label="${title}接线图"><title>${title}接线图</title>
    <text x="14" y="18">模块引脚</text><text x="350" y="18">连接到</text>
    ${wires.map(([from, to], index) => {
      const y = 39 + index * 25;
      const color = wireColor(from, to);
      return `<text x="14" y="${y}" dominant-baseline="middle">${from}</text>
        <path d="M 220 ${y} H 334" stroke="${color}" stroke-width="4"/>
        <circle cx="220" cy="${y}" r="4" fill="${color}"/>
        <circle cx="334" cy="${y}" r="4" fill="${color}"/>
        <text x="350" y="${y}" dominant-baseline="middle">${to}</text>`;
    }).join('')}
  </svg>`;
}

function partCards(parts) {
  return `<div class="parts-row">${parts.map(([kind, label]) =>
    `<div class="part-card"><div class="part-shape ${kind}" aria-hidden="true"></div><strong>${label}</strong></div>`
  ).join('')}</div>`;
}

function boardMini(bootPressed, rstPressed) {
  return `<div class="board-mini" aria-hidden="true">
    <img src="./assets/board/esp32-c3-supermini.png" alt="">
    ${bootPressed ? '<span class="key-highlight boot"></span>' : ''}
    ${rstPressed ? '<span class="key-highlight rst"></span>' : ''}
    ${bootPressed ? '<span class="finger boot"></span>' : ''}
    ${rstPressed ? '<span class="finger rst"></span>' : ''}
  </div>`;
}

function bootSequence() {
  const sequence = [
    ['① 按住 BOOT', true, false],
    ['② 按下 RST', true, true],
    ['③ 松开 RST', true, false],
    ['④ 松开 BOOT', false, false]
  ];
  return `<div class="boot-sequence">${sequence.map(([label, boot, rst]) =>
    `<div class="boot-step"><strong>${label}</strong>${boardMini(boot, rst)}</div>`
  ).join('')}</div>`;
}

function resultVisual(id) {
  if (id === 'display') {
    return `<div class="result-visual">
      <div class="result-item">${oledTestFrame(0)}文字</div>
      <div class="result-item">${oledTestFrame(1)}边框</div>
      <div class="result-item">${oledTestFrame(2)}棋盘格</div>
      <div class="result-item">${oledTestFrame(3)}反色</div>
    </div>`;
  }
  if (id === 'infrared') {
    return `<div class="result-visual">
      <div class="result-item"><strong>遮挡左侧</strong><br>LEFT：ON</div>
      <div class="result-item"><strong>遮挡右侧</strong><br>RIGHT：ON</div>
      <div class="result-item"><strong>同时遮挡</strong><br>两侧：ON</div>
      <div class="result-item"><strong>全部移开</strong><br>两侧：OFF</div>
    </div>`;
  }
  if (id.startsWith('servo_')) {
    return `<div class="result-visual"><div class="result-item"><strong>小幅转动一轮</strong><br>90° → 85° → 95° → 90°</div><div class="result-item"><strong>完成后停止</strong><br>无持续嗡鸣或发热</div></div>`;
  }
  if (id === 'touch') {
    return `<div class="result-visual"><div class="result-item"><strong>按住</strong><br>TOUCHED</div><div class="result-item"><strong>松开</strong><br>OPEN</div><div class="result-item"><strong>触摸 5 次</strong><br>COUNT：+5</div></div>`;
  }
  return `<div class="result-visual"><div class="result-item"><strong>左右跟随</strong><br>方向正确</div><div class="result-item"><strong>摸头 5 次</strong><br>表情正常</div><div class="result-item"><strong>运行 2 分钟</strong><br>无异常</div></div>`;
}

function oledTestFrame(frame) {
  const inverted = frame === 3;
  const foregroundClass = inverted ? 'oled-off' : 'oled-on';
  const title = `OLED TEST ${frame + 1}/4`;
  let content = '';

  if (frame === 0) {
    content = `<text class="oled-text oled-text-large ${foregroundClass}" x="12" y="39">HELLO</text>
      <text class="oled-text oled-text-small ${foregroundClass}" x="12" y="58">screen is alive</text>`;
  } else if (frame === 1) {
    content = `<rect class="oled-stroke ${foregroundClass}" x="8" y="18" width="112" height="38"></rect>
      <rect class="oled-stroke ${foregroundClass}" x="16" y="26" width="96" height="22"></rect>
      <text class="oled-text oled-text-small ${foregroundClass}" x="36" y="39">BORDER</text>`;
  } else if (frame === 2) {
    const squares = [];
    for (let y = 18; y < 58; y += 10) {
      for (let x = 8; x < 120; x += 10) {
        if ((Math.floor(x / 10) + Math.floor(y / 10)) % 2 === 0) {
          squares.push(`<rect class="${foregroundClass}" x="${x}" y="${y}" width="8" height="8"></rect>`);
        }
      }
    }
    content = squares.join('');
  } else {
    content = `<text class="oled-text oled-text-large ${foregroundClass}" x="22" y="41">INVERT</text>`;
  }

  return `<svg class="oled-preview${inverted ? ' is-inverted' : ''}" viewBox="0 0 128 64" role="img" aria-label="${title} actual display preview">
    <rect class="oled-background" width="128" height="64"></rect>
    <text class="oled-text oled-text-small ${foregroundClass}" x="0" y="7">${title}</text>
    <line class="oled-stroke ${foregroundClass}" x1="0" y1="10" x2="127" y2="10"></line>
    ${content}
  </svg>`;
}

function robotCalibration() {
  return `<div class="calibration-controls">
    <div class="info-label">装配前校准</div>
    <div class="calibration-flow"><span>1 进入校准</span><span>2 回到默认 90°</span><span>3 断电装舵盘</span><span>4 按需微调保存</span></div>
    <p class="calibration-state" data-calibration-state>连接完整系统后可校准。</p>
    <div class="calibration-group"><strong>开始</strong><div class="calibration-grid">
      <button type="button" class="secondary-action" data-robot-command="2" disabled>进入校准</button>
      <button type="button" class="secondary-action" data-robot-command="B" disabled>恢复默认中位</button>
      <button type="button" class="secondary-action" data-robot-command="C" disabled>回到自定义中位</button>
    </div></div>
    <p class="note">首次装配先断电取下舵盘和头部负载，再通电恢复默认 90°；停稳后断电，朝正装回舵盘。此按钮不覆盖自定义中位；按钮不可用时请安装本页完整固件。</p>
    <div class="calibration-group"><strong>每次微调 1°</strong><div class="calibration-grid">
      <button type="button" class="secondary-action" data-robot-command="A" disabled>水平向左</button>
      <button type="button" class="secondary-action" data-robot-command="D" disabled>水平向右</button>
      <button type="button" class="secondary-action" data-robot-command="W" disabled>俯仰向上</button>
      <button type="button" class="secondary-action" data-robot-command="S" disabled>俯仰向下</button>
    </div></div>
    <div class="calibration-group"><strong>完成</strong><div class="calibration-grid">
      <button type="button" class="secondary-action save-action" data-robot-command="V" disabled>保存自定义中位</button>
      <button type="button" class="secondary-action" data-robot-command="1" disabled>返回正常运行</button>
    </div></div>
    <div class="calibration-group"><strong>安全控制</strong><div class="calibration-grid">
      <button type="button" class="secondary-action emergency-action" data-robot-command="X" disabled>立即急停</button>
      <button type="button" class="secondary-action" data-robot-command="R" disabled>恢复舵机驱动</button>
    </div></div>
    <details class="troubleshooting"><summary>校准安全说明</summary><ul><li>回中和微调会让舵机动作，先确认机构活动空间。</li><li>嗡鸣、卡住或发热时立即切断外部 12V。</li><li>断开网页连接不会代替急停。</li></ul></details>
  </div>`;
}

let active = 'display';
let controller;
let serialState = {};
let version = '';
const root = document.querySelector('#steps');
const panels = new Map();
const nav = document.createElement('nav');
nav.className = 'step-nav';
nav.setAttribute('aria-label', '选择测试模块');
root.before(nav);

function setPhase(id, phase) {
  const panel = panels.get(id);
  if (!panel) return;
  const locked = serialState.connected || serialState.busy;
  if (locked && (phase === 'wiring' || phase === 'install')) return;
  panel.phase = phase;
  const currentIndex = phases.findIndex(([key]) => key === phase);
  panel.phaseTabs.forEach((button, index) => {
    button.classList.toggle('current', index === currentIndex);
    button.classList.toggle('done', index < currentIndex);
    button.setAttribute('aria-current', index === currentIndex ? 'step' : 'false');
  });
  panel.phasePanels.forEach(section => { section.hidden = section.dataset.phasePanel !== phase; });
  panel.workflowState.textContent = '当前：' + phases[currentIndex][1];
}

function select(id) {
  if (serialState.connected || serialState.busy) return;
  active = id;
  for (const [key, panel] of panels) panel.card.hidden = key !== id;
  nav.querySelectorAll('button').forEach(button => button.setAttribute('aria-current', button.dataset.step === id ? 'step' : 'false'));
  setPhase(id, panels.get(id)?.phase || 'wiring');
}

function updateControls(state = {}) {
  serialState = state;
  const locked = state.connected || state.busy;
  for (const [id, panel] of panels) {
    panel.install.disabled = !!locked || !version;
    panel.connect.disabled = !!locked || !version;
    panel.disconnect.disabled = !state.connected || state.step !== id;
    panel.start.disabled = !state.ready || state.step !== id || state.running || state.starting;
    panel.stop.disabled = !state.connected || state.step !== id;
    panel.phaseTabs.forEach(button => {
      button.disabled = !!locked && ['wiring', 'install'].includes(button.dataset.phase);
    });
    if (state.step === id || (!locked && id === active)) {
      panel.status.textContent = state.message || '';
      panel.status.classList.toggle('error', !!state.error);
    }
    if (state.connected && state.step === id) {
      panel.workflowState.textContent = state.ready ? '开发板已连接' : '正在识别程序';
    }
    if (panel.calibrationState) {
      const robotReady = !!state.connected && state.step === id && !!state.ready;
      const modeNames = { NORMAL: '正常运行', CALIBRATION: '校准模式', SELF_TEST: '自检模式' };
      const angles = Number.isFinite(state.panCurrent) && Number.isFinite(state.tiltCurrent)
        ? `水平 ${state.panCurrent}°→${state.panTarget}°；俯仰 ${state.tiltCurrent}°→${state.tiltTarget}°`
        : '角度等待读取';
      const drive = state.stopped ? '急停已生效' : (state.servoEnabled ? '舵机已启用' : '舵机未启用');
      panel.calibrationState.textContent = robotReady
        ? `${modeNames[state.mode] || state.mode || '读取中'}；${angles}；${drive}。`
        : '连接完整系统后可校准。';
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

for (const [index, step] of steps.entries()) {
  const no = String(index + 1).padStart(2, '0');
  const choice = document.createElement('button');
  choice.type = 'button';
  choice.dataset.step = step.id;
  choice.innerHTML = `<span>${no}</span>${step.nav}`;
  choice.addEventListener('click', () => select(step.id));
  nav.append(choice);

  const card = document.createElement('article');
  card.className = 'step-card';
  card.id = 'step-' + step.id;
  const isServo = step.id.startsWith('servo_');
  const isRobot = step.id === 'robot';
  const nextStep = steps[index + 1];
  card.innerHTML = `
    <div class="workflow-head">
      <div class="workflow-title"><span class="number">${no}</span><div><h2>${step.title}</h2><p>${step.need}</p></div></div>
      <span class="workflow-state">当前：接线</span>
    </div>
    <div class="phase-nav" role="navigation" aria-label="${step.title}操作步骤">
      ${phases.map(([key, label], phaseIndex) => `<button type="button" class="phase-tab" data-phase="${key}"><span class="phase-no">${phaseIndex + 1}</span><span>${label}</span></button>`).join('')}
    </div>

    <section class="phase-panel" data-phase-panel="wiring">
      <h3 class="phase-heading">接好本步元件</h3>
      <div class="safety-strip"><span class="safety-icon">⚠</span><span>改线前，断开电脑 USB 和全部外部电源。</span></div>
      ${partCards(step.parts)}
      <div class="wiring-card">${wiringSvg(step.wires, step.title)}</div>
      <div class="phase-actions"><span></span><button type="button" class="primary-action" data-go-phase="install">我已接好线，下一步 →</button></div>
    </section>

    <section class="phase-panel" data-phase-panel="install" hidden>
      <h3 class="phase-heading">让开发板进入下载模式</h3>
      <div class="safety-strip"><span class="safety-icon">⚠</span><span>关闭外部电源，只保留电脑 USB 连接。</span></div>
      ${bootSequence()}
      <div class="phase-actions">
        <button type="button" class="text-action" data-go-phase="wiring">‹ 返回接线</button>
        <div>
          <esp-web-install-button manifest="./${step.manifest}">
            <button slot="activate" class="install-action" type="button" disabled>安装${step.title}程序 →</button>
            <span slot="unsupported" class="slot-message">请使用最新版 Chrome 或 Edge。</span>
            <span slot="not-allowed" class="slot-message">请运行离线启动脚本打开本页。</span>
          </esp-web-install-button>
          <p class="install-helper">在弹窗中选择开发板</p>
          <button type="button" class="text-action" data-go-phase="test">安装完成，下一步 →</button>
        </div>
      </div>
      <details class="troubleshooting"><summary>找不到设备？</summary><ul><li>确认使用可以传数据的 USB 线。</li><li>重新按上面的 BOOT / RST 顺序操作。</li><li>等待开发板重新出现后再点击安装。</li></ul></details>
    </section>

    <section class="phase-panel" data-phase-panel="test" hidden>
      <h3 class="phase-heading">通电并测试</h3>
      <div class="test-intro"><p>${step.test}</p></div>
      <div class="test-controls">
        <div class="action-row"><button type="button" class="secondary-action" data-connect disabled>${isRobot ? '连接完整系统' : '连接开发板'}</button><button type="button" class="secondary-action" data-disconnect disabled>断开连接</button></div>
        <p class="status" role="status"></p>
        <div class="action-row" ${isServo ? '' : 'hidden'}><button type="button" class="secondary-action" data-start disabled>开始小幅转动</button><button type="button" class="secondary-action stop-action" data-stop disabled>立即停止</button></div>
        ${isRobot ? robotCalibration() : ''}
      </div>
      <div class="phase-actions"><button type="button" class="text-action" data-go-phase="install">‹ 返回安装</button><button type="button" class="primary-action" data-go-phase="result">查看正常现象 →</button></div>
    </section>

    <section class="phase-panel" data-phase-panel="result" hidden>
      <h3 class="phase-heading">对照检查结果</h3>
      ${resultVisual(step.id)}
      <ol class="result-list">${step.actions.map(action => `<li>${action}</li>`).join('')}</ol>
      <label class="observed"><input type="checkbox"> <span>${step.pass}</span></label>
      <details class="troubleshooting"><summary>没有出现这些现象？</summary><ul>${step.problems.map(problem => `<li>${problem}</li>`).join('')}</ul></details>
      <div class="phase-actions"><button type="button" class="text-action" data-go-phase="test">‹ 返回测试</button>
        ${nextStep ? `<button type="button" class="primary-action" data-next-step="${nextStep.id}">现象正常，进入下一模块 →</button>` : '<button type="button" class="primary-action" data-finish>完成本次测试</button>'}
      </div>
    </section>`;

  root.append(card);
  const panel = {
    card,
    phase: 'wiring',
    phaseTabs: [...card.querySelectorAll('[data-phase]')],
    phasePanels: [...card.querySelectorAll('[data-phase-panel]')],
    workflowState: card.querySelector('.workflow-state'),
    install: card.querySelector('.install-action'),
    connect: card.querySelector('[data-connect]'),
    disconnect: card.querySelector('[data-disconnect]'),
    start: card.querySelector('[data-start]'),
    stop: card.querySelector('[data-stop]'),
    status: card.querySelector('.status'),
    calibrationState: card.querySelector('[data-calibration-state]'),
    robotButtons: [...card.querySelectorAll('[data-robot-command]')]
  };
  panels.set(step.id, panel);
  panel.phaseTabs.forEach(button => button.addEventListener('click', () => setPhase(step.id, button.dataset.phase)));
  card.querySelectorAll('[data-go-phase]').forEach(button => button.addEventListener('click', () => setPhase(step.id, button.dataset.goPhase)));
  card.querySelector('[data-next-step]')?.addEventListener('click', event => {
    select(event.currentTarget.dataset.nextStep);
    document.querySelector('.step-nav')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  card.querySelector('[data-finish]')?.addEventListener('click', () => {
    panel.workflowState.textContent = '本次测试已完成';
    document.querySelector('.step-nav')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  panel.connect.addEventListener('click', () => controller?.connect(step.id));
  panel.disconnect.addEventListener('click', () => controller?.disconnect());
  panel.start.addEventListener('click', () => controller?.start());
  panel.stop.addEventListener('click', () => controller?.stop());
  panel.robotButtons.forEach(button => button.addEventListener('click', () => controller?.robotCommand(button.dataset.robotCommand)));
  setPhase(step.id, 'wiring');
}

select(active);

try {
  const response = await fetch('./release.json');
  if (!response.ok) throw new Error('安装资源没有加载，请重新打开完整安装包。');
  const release = await response.json();
  version = release.version;
  document.querySelector('.version').textContent = 'V' + version;
  controller = new TestConnection(navigator.serial, version, updateControls);
  updateControls({ message: '' });
} catch (error) {
  updateControls({ message: error.message, error: true });
}

document.addEventListener('visibilitychange', () => {
  if (document.hidden && controller?.session) void controller.disconnect('页面已离开，测试已停止。');
});
window.addEventListener('pagehide', () => { void controller?.disconnect(); });
