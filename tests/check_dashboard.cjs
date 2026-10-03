// No installed Node packages required. PyYAML is used to read the YAML examples.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const cp = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const files = process.argv[2] ? JSON.parse(fs.readFileSync(process.argv[2], 'utf8')) : JSON.parse(cp.execFileSync(process.env.PYTHON || 'python3', ['-c', 'import pathlib,yaml,json; print(json.dumps({p.name:yaml.safe_load(p.read_text()) for p in pathlib.Path(".").glob("dashboard*.yaml")}))'], {cwd:root, encoding:'utf8'}));
let templates=0;
function visit(v, fn) { if(Array.isArray(v)) v.forEach(x=>visit(x,fn)); else if(v&&typeof v==='object'){fn(v); Object.values(v).forEach(x=>visit(x,fn));} }
for (const [file, view] of Object.entries(files)) {
  visit(view, c => {
    if(c.type==='custom:map-card') {
      assert.equal(c.entities[0].history_show_lines,false);
      assert.equal(c.entities[0].history_show_dots,false);
      assert.equal(c.x,undefined); assert.equal(c.y,undefined);
    }
    if(c.type==='custom:mushroom-template-card'&&c.entity?.startsWith('lawn_mower.'))assert.match(c.card_mod.style,/height: 112px/);
    if(c.primary==='Mowing history')assert.equal(c.tap_action.browser_mod.data.content.cards.length,3);
    const code=c.custom_fields?.content;
    if(typeof code !== 'string' || !code.trim().startsWith('[[['))return;
    const render=new Function('entity','states','hass',code.trim().slice(3,-3));
    const hass={config:{time_zone:'UTC'}};
    const empty=render(undefined,{},hass);
    assert.doesNotMatch(empty,/undefined|NaN/);
    const session={lawn:'Lawn 1',mower:'Mower',end:new Date().toISOString(),duration_min:30,outcome:'completed',progress_end:100,source:'app'};
    const states={'sensor.mowing_session_log':{attributes:{sessions:[session]}},'sensor.mowing_session_log_2':{attributes:{sessions:[{...session,lawn:'lawn 1',mower:'Mower 2'}]}}};
    const html=render(states['sensor.mowing_session_log'],states,hass);
    assert.doesNotMatch(html,/undefined|NaN/);
    if(code.includes('const lawns')) assert.match(html,/<td>2<\/td><td>2<\/td>/);
    else assert.ok(html.includes('Mower 2'));
    states['sensor.mowing_session_log'].attributes.sessions=[{...session,lawn:'<script>alert(1)</script>',mower:'<img src=x>',error_code:'<img src=x>'}];
    const escaped=render(states['sensor.mowing_session_log'],states,hass);
    assert.ok(!escaped.includes('<script>')&&!escaped.includes('<img src=x>'));
    templates++;
  });
}
assert.equal(templates,6);
console.log(`Validated ${templates} dashboard templates: two-mower history, grouping, escaping, empty states, map settings and status heights.`);
