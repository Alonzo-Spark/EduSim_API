import json
import re

from .agentic_models import SimulationBlueprint

def _safe_js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)

def _inject_csp(html: str) -> str:
    csp_meta = (
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; '
        'img-src data:; font-src data:; connect-src \'none\'; media-src \'none\'; frame-src \'none\'; '
        'object-src \'none\'; base-uri \'none\'; form-action \'none\'">'
    )

    if re.search(r'http-equiv\s*=\s*["\']Content-Security-Policy["\']', html, flags=re.IGNORECASE):
        return html

    if "<head>" in html:
        return html.replace("<head>", f"<head>\n  {csp_meta}", 1)

    return html

def render_blueprint_to_html(blueprint: SimulationBlueprint) -> str:
    blueprint_json = json.dumps(blueprint.model_dump(), ensure_ascii=True)
    title = _safe_js_string(blueprint.title)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{blueprint.title}</title>
  <style>
    :root {{
      --bg: #071722;
      --panel: #0f2737;
      --accent: #31d0aa;
      --secondary: #ffcc66;
      --warn: #ff6f61;
      --text: #e8f1f6;
      --muted: #9db2c1;
      --border: #1c4259;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Inter", "Segoe UI", sans-serif;
      color: var(--text);
      background: radial-gradient(circle at 10% 15%, #103145, var(--bg));
      display: grid;
      grid-template-rows: auto 1fr auto;
    }}
    header {{ padding: 16px 24px; border-bottom: 1px solid var(--border); background: rgba(8, 23, 33, 0.9); backdrop-filter: blur(8px); }}
    h1 {{ margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.01em; color: var(--accent); }}
    main {{ display: grid; grid-template-columns: 300px 1fr; gap: 16px; padding: 16px; overflow: hidden; }}
    .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 16px; display: flex; flex-direction: column; gap: 16px; }}
    .panel h2 {{ margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
    .control-group {{ display: flex; flex-direction: column; gap: 12px; }}
    .control {{ display: flex; flex-direction: column; gap: 6px; }}
    .control-header {{ display: flex; justify-content: space-between; align-items: center; }}
    .control label {{ font-size: 13px; color: var(--text); }}
    .control output {{ font-size: 13px; font-family: monospace; color: var(--secondary); }}
    input[type=range] {{ width: 100%; accent-color: var(--accent); }}
    .actions {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    button {{
      border: 0;
      border-radius: 8px;
      padding: 10px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    button.primary {{ background: var(--accent); color: #021017; }}
    button.secondary {{ background: transparent; border: 1px solid var(--border); color: var(--text); }}
    button:hover {{ opacity: 0.9; transform: translateY(-1px); }}
    #simContainer {{ position: relative; width: 100%; height: 100%; background: #08131b; border-radius: 16px; border: 1px solid var(--border); overflow: hidden; }}
    #simCanvas {{ width: 100%; height: 100%; display: block; }}
    .overlay {{ position: absolute; top: 16px; left: 16px; pointer-events: none; }}
    .badge {{ background: rgba(49, 208, 170, 0.1); border: 1px solid var(--accent); color: var(--accent); padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }}
    .formula-card {{ margin-top: auto; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px; font-size: 13px; border-left: 2px solid var(--secondary); }}
    .formula-text {{ font-family: "Cambria Math", serif; font-size: 16px; color: var(--secondary); margin-top: 4px; }}
    footer {{ padding: 12px 24px; font-size: 11px; color: var(--muted); border-top: 1px solid var(--border); display: flex; justify-content: space-between; }}
    @media (max-width: 900px) {{
      main {{ grid-template-columns: 1fr; }}
      #simContainer {{ height: 400px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1 id="title"></h1>
  </header>

  <main>
    <section class="panel">
      <div class="control-group">
        <h2>Parameters</h2>
        <div id="controls"></div>
      </div>
      
      <div class="actions">
        <button id="toggleRun" class="primary">Pause Simulation</button>
        <button id="reset" class="secondary">Reset</button>
      </div>

      <div class="formula-card">
        <div>Active Model</div>
        <div class="formula-text" id="formulaText"></div>
      </div>
    </section>

    <section id="simContainer">
      <canvas id="simCanvas"></canvas>
      <div class="overlay">
        <span class="badge" id="runtimeBadge">Live Monitor</span>
        <div id="statusText" style="margin-top: 8px; font-size: 12px; color: var(--muted);"></div>
      </div>
    </section>
  </main>

  <footer>
    <span>Autonomous Agent Pipeline v2.0</span>
    <span id="fpsCounter">FPS: --</span>
  </footer>

  <script>
    const BLUEPRINT = {blueprint_json};
    const canvas = document.getElementById('simCanvas');
    const ctx = canvas.getContext('2d');
    const titleEl = document.getElementById('title');
    const controlsEl = document.getElementById('controls');
    const formulaEl = document.getElementById('formulaText');
    const statusEl = document.getElementById('statusText');
    const fpsEl = document.getElementById('fpsCounter');
    const toggleBtn = document.getElementById('toggleRun');

    titleEl.textContent = {title};
    formulaEl.textContent = BLUEPRINT.physics.formula || 'N/A';

    const STRATEGY = BLUEPRINT.metadata?.strategy || {{ instruction_mode: 'guided', visualization_complexity: 'medium', animation_speed_scale: 1.0 }};
    
    let running = true;
    let time = 0;
    let objects = JSON.parse(JSON.stringify(BLUEPRINT.objects));
    const initialObjects = JSON.parse(JSON.stringify(BLUEPRINT.objects));

    // Pedagogical Initialization
    if (STRATEGY.instruction_mode === 'guided') {{
        statusEl.innerHTML = `<strong>Guided Mode:</strong> Observe how the variables interact. <br/> <span style="font-size: 11px;">(Hint: Try changing gravity slowly)</span>`;
    }} else if (STRATEGY.instruction_mode === 'challenge') {{
        statusEl.innerHTML = `<strong>Challenge Mode:</strong> Adjust the parameters to reach the target!`;
    }}

    const runtime = {{
      startTime: Date.now(),
      interactions: [],
      errors: [],
      fpsHistory: [],
      loopCheck: {{ count: 0, lastTime: performance.now() }}
    }};

    function postRuntimeEvent(type, payload) {{
      try {{
        if (window.parent && window.parent !== window) {{
          window.parent.postMessage({{ 
            type, 
            payload, 
            simId: BLUEPRINT.id,
            timestamp: Date.now() 
          }}, '*');
        }}
      }} catch (err) {{}}
    }}

    function resize() {{
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    }}

    window.addEventListener('resize', resize);
    resize();

    function createControls() {{
      BLUEPRINT.controls.forEach(ctrl => {{
        const div = document.createElement('div');
        div.className = 'control';
        
        const header = document.createElement('div');
        header.className = 'control-header';
        
        const label = document.createElement('label');
        label.textContent = ctrl.label;
        
        const out = document.createElement('output');
        out.textContent = ctrl.default + (ctrl.unit || '');
        
        header.appendChild(label);
        header.appendChild(out);
        div.appendChild(header);

        if (ctrl.type === 'slider') {{
          const input = document.createElement('input');
          input.type = 'range';
          input.min = ctrl.min;
          input.max = ctrl.max;
          input.step = (ctrl.max - ctrl.min) / 100;
          input.value = ctrl.default;
          
          input.addEventListener('input', () => {{
            const val = parseFloat(input.value);
            out.textContent = val + (ctrl.unit || '');
            updatePhysicsParam(ctrl.name, val);
            
            // Track interaction
            runtime.interactions.push({{ name: ctrl.name, value: val, time: Date.now() - runtime.startTime }});
            if (runtime.interactions.length % 5 === 0) {{
              postRuntimeEvent('sim_interaction', {{ 
                name: ctrl.name, 
                value: val, 
                totalInteractions: runtime.interactions.length 
              }});
            }}
          }});
          div.appendChild(input);
        }}
        
        controlsEl.appendChild(div);
      }});
    }}

    function updatePhysicsParam(name, value) {{
      if (name === 'gravity') BLUEPRINT.physics.gravity = value;
      // Dynamic mapping logic
      objects.forEach(obj => {{
        if (obj.id.includes(name) || name.includes(obj.id)) {{
            // Mapping values to velocity or styles could go here
        }}
      }});
    }}

    function drawGrid() {{
      if (!BLUEPRINT.visuals.grid) return;
      ctx.strokeStyle = 'rgba(28, 66, 89, 0.3)';
      ctx.lineWidth = 1;
      const step = 50;
      for (let x = 0; x < canvas.width; x += step) {{
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }}
      for (let y = 0; y < canvas.height; y += step) {{
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }}
    }}

    function drawObject(obj) {{
      ctx.save();
      ctx.translate(obj.position.x, obj.position.y);
      
      const color = obj.style?.color || BLUEPRINT.visuals.theme.primary;
      const radius = obj.style?.radius || 10;

      if (obj.type === 'particle' || obj.type === 'ball') {{
        ctx.beginPath();
        ctx.arc(0, 0, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
        ctx.stroke();
      }} else if (obj.type === 'box' || obj.type === 'block') {{
        ctx.fillStyle = color;
        ctx.fillRect(-radius, -radius, radius * 2, radius * 2);
      }}

      if (BLUEPRINT.visuals.annotations.show_vectors) {{
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(obj.velocity.x * 2, obj.velocity.y * 2);
        ctx.strokeStyle = BLUEPRINT.visuals.theme.secondary || '#ffcc66';
        ctx.stroke();
      }}

      ctx.restore();
    }}

    function update(dt) {{
      if (!running) return;
      
      const g = BLUEPRINT.physics.gravity || 9.8;
      let offScreenCount = 0;
      
      objects.forEach(obj => {{
        obj.velocity.y += g * dt * 10;
        obj.position.x += obj.velocity.x * dt * 5;
        obj.position.y += obj.velocity.y * dt * 5;

        // Floor collision
        if (obj.position.y > canvas.height - (obj.style?.radius || 10)) {{
          obj.position.y = canvas.height - (obj.style?.radius || 10);
          obj.velocity.y *= -0.7;
        }}
        
        // Tracking stability
        if (obj.position.x < -200 || obj.position.x > canvas.width + 200 || obj.position.y < -200) {{
          offScreenCount++;
        }}
      }});

      if (offScreenCount === objects.length && objects.length > 0) {{
        postRuntimeEvent('sim_warning', {{ message: 'All entities off-screen', stability: 0.2 }});
      }}

      time += dt;
      statusEl.textContent = `Time: ${{time.toFixed(2)}}s | Entities: ${{objects.length}}`;
    }}

    let lastTime = 0;
    function loop(now) {{
      const baseDt = Math.min((now - lastTime) / 1000, 0.1);
      const dt = baseDt * (STRATEGY.animation_speed_scale || 1.0);
      lastTime = now;

      // Loop freeze detection
      runtime.loopCheck.count++;
      if (now - runtime.loopCheck.lastTime > 1000) {{
        const fps = runtime.loopCheck.count;
        fpsEl.textContent = `FPS: ${{fps}}`;
        runtime.fpsHistory.push(fps);
        
        if (fps < 20) {{
          postRuntimeEvent('sim_performance', {{ fps: fps, average: runtime.fpsHistory.slice(-10).reduce((a,b)=>a+b,0)/10 }});
        }}
        
        runtime.loopCheck.count = 0;
        runtime.loopCheck.lastTime = now;
      }}

      ctx.fillStyle = BLUEPRINT.visuals.theme.background || '#071722';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      drawGrid();
      update(dt);
      objects.forEach(drawObject);

      requestAnimationFrame(loop);
    }}

    window.addEventListener('error', (e) => {{
      postRuntimeEvent('sim_error', {{ message: e.message, stack: e.error?.stack }});
    }});

    toggleBtn.addEventListener('click', () => {{
      running = !running;
      toggleBtn.textContent = running ? 'Pause Simulation' : 'Resume Simulation';
      toggleBtn.className = running ? 'primary' : 'secondary';
      postRuntimeEvent('sim_interaction', {{ action: running ? 'resume' : 'pause' }});
    }});

    document.getElementById('reset').addEventListener('click', () => {{
      objects = JSON.parse(JSON.stringify(initialObjects));
      time = 0;
      postRuntimeEvent('sim_interaction', {{ action: 'reset' }});
    }});

    createControls();
    requestAnimationFrame(loop);
  </script>
</body>
</html>
"""

    return _inject_csp(html)