export default {
  template: `
    <section aria-label="Scratchpad" @keydown.stop @keyup.stop
             @selectstart.prevent @dragstart.prevent @contextmenu.prevent
             style="width:100%; max-width:900px; min-width:0;
                    -webkit-user-select:none; user-select:none; -webkit-touch-callout:none">
      <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px">
        <h2 style="font-size:20px; font-weight:600; margin:0; flex:1">Scratchpad</h2>
        <button type="button" @click="undo" style="padding:6px 12px; border:1px solid #94a3b8; border-radius:6px">Undo</button>
        <button type="button" @click="clear" style="padding:6px 12px; border:1px solid #94a3b8; border-radius:6px">Clear notes</button>
      </div>
      <p style="font-size:14px; margin:0 0 8px">Draw with your finger, stylus, or mouse. Notes stay until cleared or the page reloads.</p>
      <canvas ref="canvas" aria-label="Drawing area for handwritten working"
              draggable="false"
              @pointerdown="startStroke" @pointermove="moveStroke"
              @pointerup="endStroke" @pointercancel="endStroke"
              @lostpointercapture="endStroke" @contextmenu.prevent
              style="display:block; width:100%; aspect-ratio:4/3; background:white;
                     border:1px solid #94a3b8; border-radius:8px; touch-action:none;
                     -webkit-user-select:none; user-select:none;
                     -webkit-touch-callout:none; cursor:crosshair"></canvas>
    </section>`,
  mounted() {
    this.strokes = [];
    this.pointer = null;
    this.context = this.$refs.canvas.getContext('2d');
    // Explicitly non-passive so mobile browsers allow us to cancel long-press gestures.
    this.preventTouchGesture = event => {
      if (event.cancelable) event.preventDefault();
    };
    for (const type of ['touchstart', 'touchmove']) {
      this.$refs.canvas.addEventListener(type, this.preventTouchGesture, {passive: false});
    }
    this.observer = new ResizeObserver(() => this.resize());
    this.observer.observe(this.$refs.canvas);
    this.resize();
  },
  beforeUnmount() {
    this.observer.disconnect();
    for (const type of ['touchstart', 'touchmove']) {
      this.$refs.canvas.removeEventListener(type, this.preventTouchGesture);
    }
  },
  methods: {
    resize() {
      const canvas = this.$refs.canvas;
      this.width = canvas.clientWidth;
      this.height = canvas.clientHeight;
      if (!this.width || !this.height) return;
      const scale = window.devicePixelRatio || 1;
      canvas.width = Math.round(this.width * scale);
      canvas.height = Math.round(this.height * scale);
      this.context.setTransform(scale, 0, 0, scale, 0, 0);
      this.context.strokeStyle = '#172554';
      this.context.fillStyle = '#172554';
      this.context.lineWidth = 3;
      this.context.lineCap = 'round';
      this.context.lineJoin = 'round';
      this.redraw();
    },
    point(event) {
      const canvas = this.$refs.canvas;
      const rect = canvas.getBoundingClientRect();
      // Store normalized coordinates so rotating/resizing keeps the notes.
      return [(event.clientX - rect.left - canvas.clientLeft) / this.width,
              (event.clientY - rect.top - canvas.clientTop) / this.height];
    },
    segment(from, to) {
      const ctx = this.context;
      ctx.beginPath();
      ctx.moveTo(from[0] * this.width, from[1] * this.height);
      ctx.lineTo(to[0] * this.width, to[1] * this.height);
      ctx.stroke();
    },
    dot(point) {
      this.context.beginPath();
      this.context.arc(point[0] * this.width, point[1] * this.height, 1.5, 0, Math.PI * 2);
      this.context.fill();
    },
    startStroke(event) {
      if (this.pointer !== null || !event.isPrimary || event.button !== 0) return;
      event.preventDefault();
      // Dismiss the answer keyboard on touch devices while taking notes.
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      this.pointer = event.pointerId;
      this.$refs.canvas.setPointerCapture(event.pointerId);
      const point = this.point(event);
      this.strokes.push([point]);
      this.dot(point);
    },
    moveStroke(event) {
      if (event.pointerId !== this.pointer) return;
      event.preventDefault();
      const stroke = this.strokes[this.strokes.length - 1];
      const point = this.point(event);
      this.segment(stroke[stroke.length - 1], point);
      stroke.push(point);
    },
    endStroke(event) {
      if (event.pointerId !== this.pointer) return;
      if (event.type === 'pointerup') this.moveStroke(event);
      this.pointer = null;
      if (this.$refs.canvas.hasPointerCapture(event.pointerId)) {
        this.$refs.canvas.releasePointerCapture(event.pointerId);
      }
    },
    redraw() {
      this.context.clearRect(0, 0, this.width, this.height);
      for (const stroke of this.strokes) {
        this.dot(stroke[0]);
        for (let i = 1; i < stroke.length; i++) this.segment(stroke[i - 1], stroke[i]);
      }
    },
    undo() {
      if (this.pointer !== null) return;
      this.strokes.pop();
      this.redraw();
    },
    clear() {
      if (this.pointer !== null) return;
      this.strokes = [];
      this.redraw();
    },
  },
};
