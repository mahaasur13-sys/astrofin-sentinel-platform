/* Orbital particle canvas — ROMA-style */
(() => {
  const c = document.getElementById('particle-canvas');
  if (!c) return;
  const ctx = c.getContext('2d');
  let W, H, particles = [];
  
  const COLORS = ['#06d6d6', '#a855f7', '#62e6ff', '#9d8cff', '#14b8a6'];
  
  function resize() {
    W = c.width = window.innerWidth;
    H = c.height = window.innerHeight;
    particles = Array.from({length: 55}, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: .6 + Math.random() * 2.2,
      vx: (Math.random() - .5) * .25,
      vy: (Math.random() - .5) * .2,
      a: .15 + Math.random() * .4,
      c: COLORS[Math.floor(Math.random() * COLORS.length)]
    }));
  }
  
  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < -20) p.x = W + 20;
      if (p.x > W + 20) p.x = -20;
      if (p.y < -20) p.y = H + 20;
      if (p.y > H + 20) p.y = -20;
      
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.c;
      ctx.globalAlpha = p.a;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = p.c;
      ctx.globalAlpha = p.a * .2;
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }
  
  window.addEventListener('resize', resize);
  resize();
  draw();
})();
