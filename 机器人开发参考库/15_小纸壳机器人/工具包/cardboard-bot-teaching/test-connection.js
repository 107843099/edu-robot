// Runtime serial control for teaching firmware only. No flashing occurs here.
import { requestBoardPort, reportPort } from './device-status.js';
export class TestConnection {
  constructor(serial, version, onState) {
    this.serial = serial;
    this.version = version;
    this.onState = onState;
    this.session = null;
    this.busy = false;
  }

  emit(message, error = false) {
    const s = this.session;
    this.onState({ message, error, busy: this.busy, connected: !!s,
      step: s?.step, ready: !!s?.matched && (s?.robot || s?.oled) && !s?.closing,
      running: !!s?.running, starting: !!s?.starting, mode: s?.mode || '',
      panCurrent: s?.panCurrent, panTarget: s?.panTarget,
      tiltCurrent: s?.tiltCurrent, tiltTarget: s?.tiltTarget,
      stopped: !!s?.stopped, servoEnabled: !!s?.servoEnabled, config: s?.config || '', supportsDefaultCenter: !!s?.supportsDefaultCenter });
  }

  async send(s, command) {
    s.writes = s.writes.then(() => s.writer.write(new TextEncoder().encode(command + '\n')));
    return s.writes;
  }

  async connect(step) {
    if (this.busy || this.session) return;
    this.busy = true;
    this.emit('请选择 ESP32-C3 的测试串口。');
    let s;
    try {
      if (!this.serial) throw new Error('请使用 Chrome 或 Edge，并通过 localhost 或 HTTPS 打开。');
      const port = await requestBoardPort(this.serial);
      s = { port, step, robot: step === 'robot', writes: Promise.resolve(), matched: false, oled: false,
        running: false, starting: false, closing: false, timer: null, lastSeen: 0,
        mode: '', stopped: false, servoEnabled: false, config: '', supportsDefaultCenter: false };
      this.session = s;
      await port.open({ baudRate: 115200 });
      reportPort('connected', port);
      s.writer = port.writable.getWriter();
      s.reader = port.readable.getReader();
      s.identity = new Promise((resolve, reject) => { s.resolve = resolve; s.reject = reject; });
      // Attach a rejection observer immediately, before the first query write.
      s.identity.catch(() => {});
      s.readTask = this.read(s);
      const identityError = s.robot ? '没有读到完整系统固件，请先安装第 06 步固件，按 RST 后重连。' : '没有读到本步固件，请先刷入对应固件；也可按 RST 后重连。';
      s.deadline = setTimeout(() => s.reject(new Error(identityError)), 4000);
      s.query = setInterval(() => { this.send(s, '?').catch(() => {}); }, 600);
      await this.send(s, '?');
      await s.identity;
      clearTimeout(s.deadline);
      clearInterval(s.query);
      s.timer = setInterval(() => {
        if (s.closing) return;
        if (Date.now() - s.lastSeen > 2200) {
          void this.disconnect('设备失联。请检查连接；舵机固件会在心跳超时后停止。', true);
          return;
        }
        this.send(s, s.robot ? '?' : 'PING').catch(() => { void this.disconnect('串口发送失败，请断开外部电源并检查 USB。', true); });
      }, 500);
      await this.send(s, s.robot ? '?' : 'PING');
      this.busy = false;
      if (s.robot) {
        this.emit(s.oled ? '完整系统固件已识别，可以进入校准。' : '完整系统固件已识别，但 OLED 无应答；可校准舵机，请同时检查 OLED 供电和接线。', !s.oled);
      } else {
        this.emit(s.oled ? '固件身份匹配，OLED 有应答。请按本步说明观察实物。' : 'OLED 无应答。请检查供电、SDA/SCL，按 RST 后重连。', !s.oled);
      }
    } catch (error) {
      this.busy = false;
      if (s) await this.disconnect(error.message || '连接失败，请关闭安装窗口后重试。', true);
      else this.emit(error.name === 'NotFoundError' ? '已取消串口选择。' : error.message, true);
    }
  }

  async read(s) {
    let buffer = '';
    const decoder = new TextDecoder();
    try {
      while (!s.closing) {
        const { value, done } = await s.reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop().slice(-1024);
        for (const line of lines) this.handleLine(s, line.trim());
      }
    } catch (error) {
      s.reject?.(error);
    } finally {
      s.reader.releaseLock();
      s.reader = null;
      if (!s.closing) {
        s.reject?.(new Error('串口已断开，请重新连接。'));
        // Do not await disconnect here: it joins readTask during cleanup.
        void this.disconnect('串口已断开，请重新连接。', true);
      }
    }
  }

  handleLine(s, line) {
    if (s !== this.session || s.closing) return;
    if (line.startsWith('CB_ROBOT ')) {
      const fields = Object.fromEntries(line.slice(9).split(' ').map(part => part.split('=')));
      if (fields.version !== this.version) {
        s.matched = false;
        const message = '完整系统固件版本不匹配，请重新安装第 06 步。';
        s.reject?.(new Error(message));
        if (!this.busy) void this.disconnect(message, true);
        return;
      }
      if (!s.matched) reportPort('identified', s.port);
      s.matched = true;
      s.oled = fields.oled === '1';
      s.supportsDefaultCenter = fields.caps === 'default_center';
      s.mode = fields.mode || s.mode;
      s.lastSeen = Date.now();
      s.resolve?.();
      this.emit(s.oled ? '完整系统固件已识别，正在读取舵机状态。' : '完整系统已识别，但 OLED 无应答。', !s.oled);
    } else if (line.startsWith('mode=') && s.robot) {
      const fields = Object.fromEntries(line.split(' ').map(part => part.split('=')));
      const pan = (fields.pan || '/').split('/').map(Number);
      const tilt = (fields.tilt || '/').split('/').map(Number);
      s.mode = fields.mode || s.mode;
      s.config = fields.config || s.config;
      s.stopped = fields.stop === 'active';
      s.servoEnabled = fields.servos === 'enabled';
      if (Number.isFinite(pan[0])) s.panCurrent = pan[0];
      if (Number.isFinite(pan[1])) s.panTarget = pan[1];
      if (Number.isFinite(tilt[0])) s.tiltCurrent = tilt[0];
      if (Number.isFinite(tilt[1])) s.tiltTarget = tilt[1];
      s.lastSeen = Date.now();
      const modeNames = { NORMAL: '正常运行', CALIBRATION: '校准模式', SELF_TEST: '自检模式' };
      const angles = Number.isFinite(s.panCurrent) && Number.isFinite(s.tiltCurrent) ? '；水平 ' + s.panCurrent + '°→' + s.panTarget + '°，俯仰 ' + s.tiltCurrent + '°→' + s.tiltTarget + '°' : '';
      const drive = s.stopped ? '；急停已生效' : (s.servoEnabled ? '；舵机驱动已启用' : '；舵机驱动未启用');
      this.emit('完整系统已连接：' + (modeNames[s.mode] || s.mode) + angles + drive + '。');
    } else if (line.startsWith('CB_TEST ')) {
      const fields = Object.fromEntries(line.slice(8).split(' ').map(part => part.split('=')));
      if (fields.id !== s.step || fields.version !== this.version) {
        s.matched = false;
        const message = '固件不匹配，请断开并刷入当前步骤固件。';
        s.reject?.(new Error(message));
        if (!this.busy) void this.disconnect(message, true);
        return;
      }
      if (!s.matched) reportPort('identified', s.port);
      s.matched = true;
      s.oled = fields.oled === '1';
      s.running = fields.running === '1';
      if (s.running || Date.now() - (s.startAt || 0) > 1500) s.starting = false;
      s.lastSeen = Date.now();
      s.resolve?.();
      const messages = { ready: '已连接，等待本步操作。', running: '正在执行一轮小幅动作，请保持周围无遮挡。',
        complete: '本轮动作已完成，PWM 已关闭。请确认实物动作是否正常。', manual: '已停止，PWM 已关闭。',
        heartbeat: '心跳超时，固件已停止 PWM。重连不会自动启动。', oled: 'OLED 失联，固件已停止 PWM。' };
      this.emit(s.oled ? (messages[fields.result] || '已连接，请观察实物。') : 'OLED 无应答，请回第 01 步查线，恢复供电后按 RST。', !s.oled || fields.result === 'heartbeat');
    } else if (line.startsWith('SERVO_STARTED')) {
      s.running = true;
      s.starting = false;
      this.emit('正在执行一轮小幅动作。');
    } else if (line.startsWith('SERVO_STOP')) {
      s.running = false;
      s.starting = false;
      this.emit(line.includes('complete') ? '本轮完成，PWM 已关闭。请观察确认。' : 'PWM 已停止。');
    } else if (line.startsWith('SERVO_ERROR')) {
      s.starting = false;
      this.emit('未启动：请检查 OLED 和连接状态。', true);
    }
  }

  async robotCommand(command) {
    const s = this.session;
    const allowed = new Set(['1', '2', 'B', 'C', 'A', 'D', 'W', 'S', 'V', 'X', 'R']);
    if (!s?.robot || !s.matched || s.closing || !allowed.has(command)) return;
    if (command === 'B' && !s.supportsDefaultCenter) return;
    if (['B', 'C', 'A', 'D', 'W', 'S', 'V'].includes(command) && (s.mode !== 'CALIBRATION' || s.stopped)) return;
    if (command === '1' && s.stopped) return;
    const messages = { '1': '正在返回正常模式。', '2': '正在进入校准模式。', B: '正在让两个舵机平缓回到默认 90°；不会覆盖自定义中位。', C: '正在让两个舵机平缓回到自定义中位。', A: '水平向左微调 1°。', D: '水平向右微调 1°。', W: '俯仰向上微调 1°。', S: '俯仰向下微调 1°。', V: '正在把两个舵机当前位置保存为自定义中位。', X: '正在执行急停并关闭舵机 PWM。', R: '正在恢复舵机驱动；不会自动回中。' };
    this.emit(messages[command]);
    try {
      await this.send(s, command);
      await new Promise(resolve => setTimeout(resolve, 120));
      await this.send(s, '?');
    } catch (_) {
      await this.disconnect('校准命令发送失败，请立即切断外部 12V 并检查 USB。', true);
    }
  }

  async start() {
    const s = this.session;
    if (!s?.matched || !s.oled || !s.step.startsWith('servo_') || s.running || s.starting || s.closing) return;
    s.starting = true;
    s.startAt = Date.now();
    this.emit('正在请求开始测试。');
    try {
      await this.send(s, 'PING');
      await this.send(s, 'START ' + s.step);
    } catch (_) {
      await this.disconnect('启动请求失败，请断开外部电源后检查 USB。', true);
    }
  }

  async stop() {
    const s = this.session;
    if (!s?.matched || s.closing) return;
    try {
      await this.send(s, 'STOP');
      s.starting = false;
      this.emit('已发送停止命令，等待固件确认。');
    } catch (_) {
      await this.disconnect('停止命令发送失败，请立即断开舵机外部电源。', true);
    }
  }

  async disconnect(message = '测试串口已释放，可以刷写下一步。', error = false) {
    const s = this.session;
    if (!s) { this.busy = false; this.emit(message, error); return; }
    if (s.closing) return s.closeTask;
    s.closing = true;
    clearInterval(s.timer);
    clearInterval(s.query);
    clearTimeout(s.deadline);
    s.reject?.(new Error(message));
    this.emit(s.robot ? '正在释放串口；完整系统会继续按当前模式运行。' : '正在停止并释放串口。');
    s.closeTask = (async () => {
      let stopTimeout;
      try {
        if (s.matched && !s.robot && s.writer) await Promise.race([
          this.send(s, 'STOP'),
          new Promise((_, reject) => { stopTimeout = setTimeout(() => reject(new Error('STOP timeout')), 500); })
        ]);
      } catch (_) {
        try { await s.writer?.abort(); } catch (_) {}
      } finally { clearTimeout(stopTimeout); }
      try { await s.reader?.cancel(); } catch (_) {}
      await s.readTask;
      try { s.writer?.releaseLock(); } catch (_) {}
      try { await s.port.close(); } catch (_) { message = '串口释放失败，请拔插 USB 后刷新页面。'; error = true; }
      if (this.session === s) this.session = null;
      this.busy = false;
      reportPort(error ? 'error' : 'closed', s.port, error ? message : '');
      this.emit(message, error);
    })();
    return s.closeTask;
  }
}
