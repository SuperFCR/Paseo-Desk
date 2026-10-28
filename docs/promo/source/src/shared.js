// 公共动画工具：注入到每个场景脚本的 IIFE 里，所有动作放在场景时间轴的绝对时刻上。
// 首次出现用 fromTo（出场前保持隐藏）；同一元素后续动作用 later()，避免覆盖初始状态。
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const list = (t) => (typeof t === "string" ? $$(t) : Array.isArray(t) ? t.flatMap((x) => (typeof x === "string" ? $$(x) : [x])) : [t]);

// 把元素里的文字拆成逐字 span，保留内部高亮 span
function split(el) {
  const out = [];
  const walk = (node) => {
    [...node.childNodes].forEach((n) => {
      if (n.nodeType === 3) {
        const frag = document.createDocumentFragment();
        for (const c of n.textContent) {
          const s = document.createElement("span");
          s.className = "ch";
          s.textContent = c;
          frag.appendChild(s);
          if (!/\s/.test(c)) out.push(s);
        }
        n.replaceWith(frag);
      } else if (n.nodeType === 1 && n.tagName.toLowerCase() !== "svg") {
        walk(n);
      }
    });
  };
  walk(el);
  return out;
}

function later(tl, t, from, to, at) {
  return tl.fromTo(list(t), from, { ...to, immediateRender: false }, at);
}
function blurIn(tl, t, at, o = {}) {
  return tl.fromTo(list(t), { opacity: 0, filter: `blur(${o.blur ?? 10}px)` },
    { opacity: 1, filter: "blur(0px)", duration: o.dur ?? 0.5, ease: "power2.out", stagger: o.stagger ?? 0 }, at);
}
function rise(tl, t, at, o = {}) {
  return tl.fromTo(list(t), { opacity: 0, y: o.y ?? 34, filter: "blur(5px)" },
    { opacity: 1, y: 0, filter: "blur(0px)", duration: o.dur ?? 0.9, ease: "expo.out", stagger: o.stagger ?? 0.1 }, at);
}
function slideIn(tl, t, at, o = {}) {
  return tl.fromTo(list(t), { opacity: 0, x: o.x ?? -40 },
    { opacity: 1, x: 0, duration: o.dur ?? 0.8, ease: "expo.out", stagger: o.stagger ?? 0.1 }, at);
}
function pop(tl, t, at, o = {}) {
  return tl.fromTo(list(t), { opacity: 0, scale: o.from ?? 0.7, y: o.y ?? 0 },
    { opacity: 1, scale: 1, y: 0, duration: o.dur ?? 0.7, ease: o.ease ?? "back.out(1.7)", stagger: o.stagger ?? 0 }, at);
}
function charsRise(tl, el, at, o = {}) {
  return tl.fromTo(split($(el)), { opacity: 0, y: o.y ?? 44, filter: "blur(8px)" },
    { opacity: 1, y: 0, filter: "blur(0px)", duration: o.dur ?? 0.6, ease: "expo.out", stagger: o.stagger ?? 0.05 }, at);
}
// 打字：逐字出现，cps 为每秒字数；返回结束时刻
function typeOn(tl, el, at, cps = 22) {
  const cs = split($(el));
  tl.fromTo(cs, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: 1 / cps, ease: "none" }, at);
  return at + cs.length / cps;
}
// 描线：SVG path / rect 从起点画到终点
function draw(tl, t, at, o = {}) {
  list(t).forEach((p, i) => {
    const L = p.getTotalLength();
    p.style.strokeDasharray = `${L} ${L}`;
    tl.fromTo(p, { strokeDashoffset: L, opacity: 1 },
      { strokeDashoffset: 0, duration: o.dur ?? 0.8, ease: o.ease ?? "power2.inOut" }, at + i * (o.stagger ?? 0));
  });
}
// 光点沿折线移动：pts 为 [[x,y],...]，按段长分配时间
function travel(tl, el, pts, at, dur) {
  const seg = pts.slice(1).map((p, i) => Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]));
  const L = seg.reduce((a, b) => a + b, 0);
  tl.fromTo(el, { x: pts[0][0], y: pts[0][1], opacity: 0 }, { opacity: 1, duration: 0.15, ease: "none" }, at);
  let t = at;
  seg.forEach((s, i) => {
    const d = (dur * s) / L;
    later(tl, el, { x: pts[i][0], y: pts[i][1] }, { x: pts[i + 1][0], y: pts[i + 1][1], duration: d, ease: "none" }, t);
    t += d;
  });
  later(tl, el, { opacity: 1 }, { opacity: 0, duration: 0.2, ease: "none" }, t);
  return t;
}
function bar(tl, t, at, o = {}) {
  return tl.fromTo(list(t), { scaleX: 0, transformOrigin: "0% 50%" },
    { scaleX: 1, duration: o.dur ?? 0.7, ease: o.ease ?? "expo.out" }, at);
}
function dim(tl, t, at, o = {}) {
  return later(tl, t, { opacity: 1 }, { opacity: o.to ?? 0.3, duration: o.dur ?? 0.5, ease: "power2.out" }, at);
}
function out(tl, t, at, o = {}) {
  return later(tl, t, { opacity: 1, filter: "blur(0px)" },
    { opacity: 0, filter: `blur(${o.blur ?? 8}px)`, duration: o.dur ?? 0.45, ease: "power2.in", stagger: o.stagger ?? 0 }, at);
}
// 场景首尾：整体淡入淡出 + 极慢推镜
function frame(tl, sel, D, o = {}) {
  tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: o.in ?? 0.5, ease: "power1.out" }, 0);
  tl.fromTo(sel, { scale: 1 }, { scale: o.zoom ?? 1.025, duration: D, ease: "none", immediateRender: false }, 0);
  later(tl, sel, { opacity: 1 }, { opacity: 0, duration: o.out ?? 0.5, ease: "power1.in" }, D - (o.out ?? 0.5));
}
