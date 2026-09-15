// Run from the project root with JavaScriptCore's jsc.
const component = new Function(readFile('scratchpad.js').replace('export default', 'return'))();
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
globalThis.window = {devicePixelRatio: 2};
globalThis.HTMLElement = class {};
globalThis.document = {activeElement: null};
let disconnected = false;
globalThis.ResizeObserver = class {
  observe() {}
  disconnect() { disconnected = true; }
};
const ctx = {};
for (const method of ['setTransform', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'arc', 'fill', 'clearRect']) {
  ctx[method] = () => {};
}
const captured = new Set();
const listeners = new Map();
const canvas = {
  addEventListener(type, handler, options) {
    assert(options.passive === false, 'Touch gesture cancellation must be non-passive');
    listeners.set(type, handler);
  },
  removeEventListener(type, handler) {
    assert(listeners.get(type) === handler, 'Remove the registered handler');
    listeners.delete(type);
  },
  clientWidth: 400, clientHeight: 300, clientLeft: 1, clientTop: 1,
  getContext: () => ctx,
  getBoundingClientRect: () => ({left: 0, top: 0}),
  setPointerCapture: id => captured.add(id),
  hasPointerCapture: id => captured.has(id),
  releasePointerCapture: id => captured.delete(id),
};
const pad = {$refs: {canvas}};
for (const [name, method] of Object.entries(component.methods)) pad[name] = method.bind(pad);
component.mounted.call(pad);
for (const type of ['touchstart', 'touchmove']) {
  let prevented = false;
  listeners.get(type)({cancelable: true, preventDefault() { prevented = true; }});
  assert(prevented, 'Touch gestures must not select or scroll the page');
}
assert(canvas.width === 800 && canvas.height === 600, 'High-resolution backing canvas');
const event = (type, id = 1, x = 101) => ({
  type, pointerId: id, isPrimary: true, button: 0, clientX: x, clientY: 76,
  preventDefault() {},
});
pad.startStroke(event('pointerdown'));
assert(pad.strokes.length === 1 && captured.has(1), 'Touch starts a captured stroke');
pad.startStroke(event('pointerdown', 2));
pad.moveStroke(event('pointermove', 2));
assert(pad.strokes.length === 1 && pad.strokes[0].length === 1, 'Second finger cannot corrupt stroke');
pad.moveStroke(event('pointermove', 1, 201));
pad.endStroke(event('pointerup', 1, 301));
assert(pad.strokes[0].length === 3 && !captured.has(1), 'Stroke completes and releases capture');
assert(pad.strokes[0][0][0] === 0.25, 'Coordinates account for canvas border');
canvas.clientWidth = 200;
canvas.clientHeight = 150;
pad.resize();
assert(pad.strokes[0][0][0] === 0.25, 'Resize preserves normalized notes');
pad.startStroke(event('pointerdown', 3));
pad.endStroke(event('pointercancel', 3));
assert(pad.pointer === null, 'Interrupted touches release drawing state');
pad.undo();
assert(pad.strokes.length === 1, 'Undo removes only the last stroke');
pad.clear();
assert(pad.strokes.length === 0, 'Clear removes notes');
component.beforeUnmount.call(pad);
assert(disconnected, 'Resize observer is cleaned up');
assert(listeners.size === 0, 'Touch listeners are cleaned up');
print('Scratchpad drawing, resize, cancellation, undo, clear, and cleanup checks passed.');
