/* Exercise the actual view functions with local project data, without a browser. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync} = require('node:child_process');

const root = path.resolve(__dirname, '..');
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const data = JSON.parse(execFileSync(python, ['-c', `
import json
from app import main, storage
from app.engine import Analyzer
main.analyzer = Analyzer()
print(json.dumps({'overview':main.overview(), 'methodology':main.methodology(),
                 'knowledge':main.knowledge(), 'complaints':main.complaints(query='',priority='',status='',category=''),
                 'record':storage.get_record('CMP-0001')}))
`], {cwd: root, encoding: 'utf8', maxBuffer: 5 * 1024 * 1024}));

const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {innerHTML:'', textContent:'', className:'', classList:{toggle(){},remove(){}}, dataset:{}});
  return elements.get(id);
}
const sandbox = vm.createContext({
  document: {getElementById:element, querySelectorAll:()=>[], addEventListener(){}, contains:()=>false},
  window: {scrollTo(){}, addEventListener(){}},
  location: {hash:'#overview'}, navigator:{clipboard:{writeText:async()=>{}}},
  setTimeout:()=>0, clearTimeout(){}, URLSearchParams, console,
  fetch:async url => {
    const responses = {'/api/health':{llm:{available:true,model:'fixture-local'}},
      '/api/overview':data.overview, '/api/methodology':data.methodology,
      '/api/knowledge':data.knowledge, '/api/complaints':data.complaints,
      '/api/complaints/CMP-0001':data.record};
    assert.ok(Object.hasOwn(responses,url), 'Unexpected request in template test: '+url);
    return {ok:true,json:async()=>structuredClone(responses[url])};
  },
});

async function main() {
  const source = fs.readFileSync(path.join(root,'static','app.js'),'utf8')
    .replace(/\ninitialize\(\);\s*$/, '\nglobalThis.ready = initialize();');
  vm.runInContext(source,sandbox,{filename:'app.js'});
  await sandbox.ready;
  assert.match(element('content').innerHTML,/Find what went wrong/);
  for (const [page,expected] of [
    ['complaints','Every case, in one place'], ['analyze','What happened'],
    ['knowledge','A place to start checking'], ['methodology','A demo you can explain'],
    ['case/CMP-0001',"The customer's account"],
  ]) {
    sandbox.location.hash='#'+page;
    await vm.runInContext('route()',sandbox);
    assert.ok(element('content').innerHTML.includes(expected), 'View did not render: '+page);
    assert.ok(!element('content').innerHTML.includes('undefined'), 'Undefined content in '+page);
  }
  const evidence = vm.runInContext("state.caseTab='evidence';casePage(state.record)",sandbox);
  assert.match(evidence,/KB-01/);
  assert.match(evidence,/Similar customer queries/);
  const reply = vm.runInContext("state.caseTab='reply';casePage(state.record)",sandbox);
  assert.match(reply,/A draft the reviewer can edit/);
  assert.equal(vm.runInContext("h('<script>alert(1)</script>')",sandbox), '&lt;script&gt;alert(1)&lt;/script&gt;');
  assert.equal(vm.runInContext("h('a\"b')",sandbox), 'a&quot;b');
  console.log('Frontend smoke checks passed: 8 views and HTML escaping. This is not a visual browser test.');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
