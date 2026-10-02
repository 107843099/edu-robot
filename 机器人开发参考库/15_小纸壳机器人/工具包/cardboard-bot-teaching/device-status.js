// Shared by the installer and teaching tests; never opens a port itself.
export const BOARD_FILTERS = [{ usbVendorId: 0x303a, usbProductId: 0x1001 }];

export function isBoardPort(port) {
  const info = port.getInfo();
  return BOARD_FILTERS.some(filter => info.usbVendorId === filter.usbVendorId && info.usbProductId === filter.usbProductId);
}

export function reportPort(state, port, message = '') {
  document.dispatchEvent(new CustomEvent('cb-port-state', { detail: { state, port, message } }));
}

export async function requestBoardPort(serial = navigator.serial) {
  try {
    const port = await serial.requestPort({ filters: BOARD_FILTERS });
    reportPort('selected', port);
    return port;
  } catch (error) {
    reportPort('error', null, error.name === 'NotFoundError'
      ? '没有选择开发板。'
      : '连接失败：' + error.message);
    throw error;
  }
}

export function mountDeviceStatus(serial = navigator.serial) {
  const label = document.querySelector('#device-status');
  if (!label) return;
  let currentPort = null;
  let active = false;
  let revision = 0;
  const show = (message, error = false) => {
    label.textContent = message;
    label.classList.toggle('error', error);
  };
  const refresh = async () => {
    const request = ++revision;
    if (active) return;
    try {
      const ports = (await serial.getPorts()).filter(isBoardPort).filter(port => port.connected !== false);
      if (request !== revision || active) return;
      show(ports.length > 1 ? '发现多块开发板，请只保留要安装的一块。'
        : ports.length === 1 ? '已发现开发板，可以开始安装。'
        : '等待连接；安装时请选择开发板。');
    } catch (_) { show('无法读取设备，请使用 Chrome 或 Edge。', true); }
  };
  document.addEventListener('cb-port-state', ({ detail }) => {
    ++revision;
    const { state, port, message } = detail;
    currentPort = port;
    active = state === 'connected' || state === 'identified';
    const labels = {
      selected: '已选择开发板，正在连接。',
      connected: '已连接，正在识别程序。',
      identified: '开发板已连接。',
      closed: '已断开连接。',
      error: '连接失败，请查看当前步骤的帮助。'
    };
    show(message || labels[state], state === 'error');
  });
  if (!serial || !window.isSecureContext || location.protocol === 'file:') {
    show('请运行离线启动脚本，用 Chrome 或 Edge 打开。', true);
    return;
  }
  serial.addEventListener('connect', () => { if (!active) void refresh(); });
  serial.addEventListener('disconnect', event => {
    const port = event.port || event.target;
    if (port === currentPort) {
      ++revision;
      active = false;
      currentPort = null;
      show('开发板已断开，重新出现后请再次选择。', true);
    } else if (!active) void refresh();
  });
  void refresh();
}
