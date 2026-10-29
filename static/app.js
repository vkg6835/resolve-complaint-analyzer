/* Local, dependency-free UI. All complaint and model text is HTML-escaped. */
'use strict';

const paths = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  inbox: '<path d="M4 4h16v16H4zM4 13h4l2 3h4l2-3h4"/>',
  scan: '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5M7 8h10M7 12h10M7 16h6"/>',
  book: '<path d="M12 6v15M3 4c4-1 6 0 9 2 3-2 5-3 9-2v15c-4-1-6 0-9 2-3-2-5-3-9-2V4Z"/>',
  flask: '<path d="M9 3h6m-5 0v6l-6 10a1.3 1.3 0 0 0 1 2h14a1.3 1.3 0 0 0 1-2L14 9V3M7 15h10"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  back: '<path d="M19 12H5m6-6-6 6 6 6"/>',
  down: '<path d="m7 10 5 5 5-5"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
  chat: '<path d="M4 4h16v13H9l-5 4V4Z"/><path d="M8 9h8M8 13h5"/>',
  phone: '<path d="m6 3 4 5-3 3c2 3 3 4 6 6l3-3 5 4c-1 4-3 4-5 3C8 18 6 16 3 8 2 6 2 4 6 3Z"/>',
  web: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  square: '<rect x="4" y="4" width="16" height="16" rx="3"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
  alert: '<path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3h.01"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  spark: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2c0-5 16-5 16 0v2"/>',
  chart: '<path d="M4 3v18h17M8 16l4-5 4 2 5-7"/>',
  bank: '<path d="m3 8 9-5 9 5H3Zm2 3v7m5-7v7m4-7v7m5-7v7M3 21h18"/>',
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.info}</svg>`;
const h = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
const pct = value => (Number(value) * 100).toFixed(1) + '%';
const num = value => Number(value).toLocaleString('en-IN');
const tag = (value, extra = '') => `<span class="tag ${h(extra || String(value).toLowerCase().replaceAll(' ', '-'))}">${h(value)}</span>`;
const date = value => new Date(value).toLocaleDateString('en-IN', {day: '2-digit', month: 'short', timeZone: 'Asia/Kolkata'});
const state = {health: null, overview: null, methodology: null, knowledge: null, record: null, caseTab: 'analysis', pending: new Set(), routeVersion: 0};
const content = document.getElementById('content');

async function api(url, options = {}) {
  const response = await fetch(url, {...options, headers: {'Content-Type': 'application/json', ...options.headers}});
  const body = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(body.detail) ? body.detail.map(item => item.msg).join('; ') : body.detail;
    throw new Error(detail || 'The request could not be completed.');
  }
  return body;
}

let toastTimer;
function toast(message, error = false) {
  const element = document.getElementById('toast');
  element.textContent = message;
  element.className = 'toast show' + (error ? ' error' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => element.classList.remove('show'), error ? 8500 : 4200);
}

function setNav(page) {
  document.querySelectorAll('[data-nav]').forEach(link => link.classList.toggle('active', link.dataset.nav === page));
  const labels = {overview: 'Overview', complaints: 'Complaints', analyze: 'Analyze complaint', knowledge: 'Evidence library', methodology: 'Methodology'};
  document.getElementById('breadcrumb').textContent = labels[page] || 'Complaint analysis';
}

function complaintTable(records, compact = false) {
  if (!records.length) return `<div class="empty-state">${icon('search')}No complaints match these filters.</div>`;
  return `<div class="table-wrap"><table><thead><tr><th>Complaint</th><th>Category</th><th>Priority</th><th>Status</th>${compact ? '' : '<th>Channel</th>'}<th>Received</th><th aria-label="Open case"></th></tr></thead><tbody>${records.map(row => `
    <tr class="case-row" data-case="${h(row.id)}" tabindex="0" role="button" aria-label="Open ${h(row.title)}">
      <td><div class="case-title">${h(row.title)}</div><div class="case-id">${h(row.id)}</div></td>
      <td>${h(row.category)}</td><td>${tag(row.priority)}</td><td>${tag(row.status)}</td>
      ${compact ? '' : `<td><span class="channel">${icon(row.channel.toLowerCase())}${h(row.channel)}</span></td>`}
      <td>${date(row.created_at)}</td><td>${icon('arrow')}</td>
    </tr>`).join('')}</tbody></table></div>`;
}

function donut(priorities, total) {
  const colors = ['#bc7371', '#ff936c', '#b2bea3', '#658872'];
  const radius = 51, circumference = 2 * Math.PI * radius;
  let offset = 0;
  const arcs = priorities.map((row, index) => {
    const length = total ? row.count / total * circumference : 0;
    const part = `<circle cx="65" cy="65" r="${radius}" fill="none" stroke="${colors[index]}" stroke-width="13" stroke-dasharray="${Math.max(0, length - (length ? 2.7 : 0))} ${circumference}" stroke-dashoffset="${-offset}"/>`;
    offset += length;
    return part;
  }).join('');
  return `<div class="priority-layout"><div class="donut-wrap"><svg viewBox="0 0 130 130" aria-label="Complaint priority distribution"><circle cx="65" cy="65" r="51" fill="none" stroke="#f3f5ef" stroke-width="13"/>${arcs}</svg><div class="donut-center"><strong>${total}</strong><span>complaints</span></div></div><div class="legend">${priorities.map((row, i) => `<div class="legend-row"><span class="color-dot" style="background:${colors[i]}"></span>${h(row.name)}<strong>${row.count}</strong></div>`).join('')}</div></div>`;
}

function overviewPage(data, methodology) {
  const selected = methodology.experiments.find(item => item.selected);
  const featured = data.featured;
  const max = Math.max(1, ...data.categories.map(row => row.count));
  return `
    <section class="hero"><div><div class="hero-label"><span class="line"></span>BANKING · CUSTOMER COMPLAINT ANALYZER</div><h1>Find what went wrong.</h1><p>Understand the reported problem, investigate possible causes, and give every complaint a clearer next step.</p></div><div class="hero-aside"><span class="hero-badge">${icon('bank')}</span><div><strong>Evidence before conclusions</strong><span>Local analysis. Clear reasoning. Human review.</span></div></div></section>
    <section class="metrics" aria-label="Workspace metrics">
      <div class="metric"><div class="metric-top"><span>Total complaints</span>${icon('inbox')}</div><div class="metric-value">${data.total}</div><div class="metric-note">${data.demo_count} fictional demo cases · ${data.active} active</div></div>
      <div class="metric attention"><div class="metric-top"><span>Need attention</span>${icon('alert')}</div><div class="metric-value">${data.attention}</div><div class="metric-note">${data.urgent} urgent · active high-priority cases</div></div>
      <div class="metric"><div class="metric-top"><span>Supported complaint types</span>${icon('scan')}</div><div class="metric-value">${data.intents}</div><div class="metric-note">Selected banking intents · English</div></div>
      <div class="metric test"><div class="metric-top"><span>Held-out intent macro-F1</span>${icon('target')}</div><div class="metric-value">${(selected.test.macro_f1 * 100).toFixed(1)}<small>%</small></div><div class="metric-note"><span class="tiny-dot"></span>${data.test_count} test queries · 12-category subset</div></div>
    </section>
    <section class="overview-grid">
      <div class="panel"><div class="panel-head"><div><h2>Most common reported problems</h2><p>Patterns in the complaint inbox</p></div><span class="subtle-badge">ALL CASES</span></div><div class="panel-body">${data.categories.map(row => `<div class="bar-row"><span class="bar-name">${h(row.name)}</span><div class="bar-track"><div class="bar-fill" style="width:${row.count/max*100}%"></div></div><span class="bar-count">${row.count}</span></div>`).join('')}<div class="chart-note">Counts describe this demo inbox, not the benchmark dataset.</div></div></div>
      <div class="panel"><div class="panel-head"><div><h2>Priority at a glance</h2><p>Where a reviewer should start</p></div>${icon('chart')}</div><div class="panel-body">${donut(data.priorities, data.total)}<div class="chart-note">Priority follows investigation rules, with security cases escalated first.</div></div></div>
    </section>
    ${featured ? `<section class="spotlight"><div class="spotlight-left"><div class="spotlight-tag">${icon('spark')}CASE SPOTLIGHT · ${h(featured.id)}</div><h3>${h(featured.title)}</h3><blockquote>${h(featured.facts[0]?.quote || featured.text)}</blockquote><div class="spotlight-bottom">${tag(featured.priority)}<span class="tag outline">Fictional demo complaint</span></div></div><div class="spotlight-right"><div class="eyebrow">A POSSIBLE FAILURE MECHANISM</div><h3>${h(featured.hypothesis)}</h3><div class="spotlight-check">${icon('search')}<span>${h(featured.questions[0])}</span></div><div class="spotlight-bottom"><span class="tag outline">Verification required</span><a href="#case/${h(featured.id)}" class="text-link">Open full analysis ${icon('arrow')}</a></div></div></section>` : ''}
    <section class="panel"><div class="panel-head"><div><h2>Recent complaints</h2><p>Reported problems with evidence and an investigation plan</p></div><a href="#complaints" class="text-link">View all complaints ${icon('arrow')}</a></div>${complaintTable(data.recent, true)}<div class="table-bottom"><span>Common identifiers are masked before a complaint is stored.</span><a href="#analyze" class="text-link">Analyze a new complaint ${icon('plus')}</a></div></section>`;
}

function complaintsPage(records) {
  const categories = state.methodology.labels.map(row => row.title).sort();
  return `<div class="page-heading"><div><div class="eyebrow">THE COMPLAINT INBOX</div><h1>Every case, in one place.</h1><p>Filter the inbox, review the evidence, and track the next step.</p></div><div class="heading-actions"><a class="button" href="/api/export">${icon('download')}Export CSV</a><a class="button dark" href="#analyze">${icon('plus')}New analysis</a></div></div>
    <section class="panel"><div class="filters"><div class="input-wrap">${icon('search')}<input id="search-complaints" aria-label="Search complaints" placeholder="Search complaints, IDs or keywords..."></div><select id="filter-priority" aria-label="Filter priority"><option value="">All priorities</option>${['Urgent','High','Medium','Low'].map(x => `<option>${x}</option>`).join('')}</select><select id="filter-status" aria-label="Filter status"><option value="">All statuses</option>${['Open','Under review','Resolved'].map(x => `<option>${x}</option>`).join('')}</select><select id="filter-category" aria-label="Filter category"><option value="">All categories</option>${categories.map(x => `<option>${h(x)}</option>`).join('')}<option>Needs manual review</option></select></div><div id="complaint-table">${complaintTable(records.items)}</div><div class="table-bottom"><span id="list-count">${records.count} complaints</span><span>Demo cases are fictional and labeled in each case.</span></div></section>`;
}

const samples = [
  {name:'Duplicate charge', title:'One purchase, two settled charges', text:'I paid Rs 2400 at a supermarket once, but my bank statement shows two charges. Both entries are marked completed and the merchant receipt shows only one payment. I contacted support three times and each agent told me to wait. I am frustrated because nobody has given me a case update.'},
  {name:'Missing transfer', title:'Recipient has not received the transfer', text:'I transferred Rs 12000 to my landlord four days ago. The money has left my account but the recipient says nothing has arrived. The app says the transfer is complete. I contacted support twice and was sent to different agents.'},
  {name:'Unrecognized payment', title:'A card payment I did not authorize', text:'I found an unrecognized card payment for Rs 8600 on my bank statement. I did not authorize the transaction and my card is still with me. I am worried about more charges.'},
  {name:'Missing details', title:'An unclear complaint', text:'The service is terrible and I am upset. Something went wrong yesterday and I want someone to fix it.'},
];

function analyzePage() {
  return `<div class="page-heading"><div><div class="eyebrow">START AN INVESTIGATION</div><h1>What happened?</h1><p>Paste a banking complaint. Get a reported problem, supporting evidence, and a plan to check the cause.</p></div><span class="tag outline">English · 12 banking complaint types</span></div>
    <div class="analyze-grid"><section class="panel form-panel"><div class="panel-head"><h2>Complaint details</h2><span class="subtle-badge">LOCAL PROCESSING</span></div><div class="panel-body"><form id="analyze-form"><div class="field-row"><div><label class="field-label" for="complaint-title">Case title <span style="font-weight:400;color:#99a28e">(optional)</span></label><input id="complaint-title" name="title" maxlength="120" placeholder="A short title for this complaint"></div><div><label class="field-label" for="complaint-channel">Channel</label><select id="complaint-channel" name="channel"><option>Web</option><option>Email</option><option>Chat</option><option>Phone</option></select></div></div><label class="field-label">Try a fictional example</label><div class="sample-buttons">${samples.map((sample, index) => `<button type="button" class="sample-button" data-sample="${index}">${h(sample.name)}</button>`).join('')}</div><label class="field-label" for="complaint-text">Customer complaint</label><textarea id="complaint-text" class="complaint-text" name="text" minlength="20" maxlength="4000" required placeholder="Describe what happened, what the customer expected, and any support contact or transaction status..." aria-describedby="complaint-help"></textarea><div class="textarea-meta" id="complaint-help"><span>At least 20 characters. Include details that can be checked.</span><span id="character-count">0 / 4,000</span></div><div class="privacy-note">${icon('shield')}<span>Analysis stays on this laptop. Common emails, card numbers and long numeric identifiers are masked before storage. Use a fictional example or remove sensitive details before pasting.</span></div><label class="checkbox-line"><input type="checkbox" id="use-llm" ${state.health?.llm?.available ? 'checked' : ''}>Add a deeper local LLM explanation after triage</label><button class="button accent wide" type="submit" id="analyze-button">${icon('scan')}Analyze complaint ${icon('arrow')}</button><div class="form-error" id="form-error" role="alert"></div></form></div></section>
    <aside class="process-guide"><div class="eyebrow">BEHIND THE ANALYSIS</div><h2>A complaint is the starting point.</h2><p>The goal is to separate what the customer reports from what the organization still needs to verify.</p><div class="process-step"><span class="step-number">1</span><div><strong>Understand the reported problem</strong><p>A trained intent classifier proposes a complaint category and flags uncertainty.</p></div></div><div class="process-step"><span class="step-number">2</span><div><strong>Bring the evidence together</strong><p>Exact complaint quotes, relevant investigation playbooks, and similar training queries.</p></div></div><div class="process-step"><span class="step-number">3</span><div><strong>Test the possible cause</strong><p>Identify a working hypothesis and the records needed to confirm or reject it.</p></div></div><div class="process-step"><span class="step-number">4</span><div><strong>Fix the case and the process</strong><p>Suggest an investigation owner and a preventive action for review.</p></div></div><div class="guide-foot">A plausible cause still needs evidence. The system keeps that distinction visible.</div></aside></div>`;
}

function policyCard(policy, showSimilarity = false) {
  return `<article class="evidence-card"><div class="similar-meta"><span class="policy-id">${h(policy.id)}</span><span class="tag outline">Demo playbook · v${h(policy.version)}</span></div><h3>${h(policy.title)}</h3><p>${h(policy.text)}</p><div class="evidence-meta"><span>${showSimilarity ? h(policy.retrieval_reason) : h(policy.group)}</span><span>${showSimilarity ? 'Lexical cosine ' + Number(policy.similarity).toFixed(2) : 'Authored example'}</span></div></article>`;
}

function llmCard(record) {
  const value = record.llm;
  if (!value) return '';
  return `<section class="panel llm-output"><div class="panel-head"><h2>${icon('spark')} Local LLM explanation</h2><span class="tag green">${h(value.model)}</span></div><div class="panel-body"><h3>${h(value.summary)}</h3><span class="tag outline">Possible cause · unverified</span><p>${h(value.possible_cause)}</p>${value.why_this_hypothesis ? `<p><strong>Why this needs checking:</strong> ${h(value.why_this_hypothesis)}</p>` : ''}${value.fact_quotes.map((quote, i) => `<div class="fact-row"><span class="fact-ref">Q${i+1}</span><p>“${h(quote)}”</p></div>`).join('')}<div class="feature-tags">${value.policy_ids.map(id => `<span class="policy-id">${h(id)}</span>`).join('')}</div><ul class="checklist">${value.verification_questions.map(q => `<li>${icon('square')}<span>${h(q)}</span></li>`).join('')}</ul><div class="source-line"><span>Exact quotes and citation IDs checked. Causality needs review.</span><span>${value.seconds}s · saved explanation</span></div>${value.input_truncated ? '<p class="score-note">The local explanation used the first 2,000 characters of the complaint.</p>' : ''}</div></section>`;
}

function casePage(record) {
  const busy = state.pending.has(record.id);
  const main = state.caseTab === 'analysis' ? `
    <div class="case-grid"><div class="case-main"><section class="panel"><div class="panel-head"><h2>The customer's account</h2><span class="subtle-badge">CUSTOMER-REPORTED</span></div><div class="panel-body"><p class="quote-text">${h(record.text)}</p><div class="source-line"><span>${h(record.source)}</span><span>${h(record.channel)} · ${date(record.created_at)}</span></div></div></section>
    <section class="panel hypothesis-panel"><div class="panel-head"><h2>${record.needs_review ? 'More information needed' : 'Where it may have failed'}</h2>${tag('Verification required','warning')}</div><div class="panel-body"><h3 class="hypothesis-title">${h(record.hypothesis)}</h3><div class="hypothesis-note">${icon('info')}<span>This is a working hypothesis. Complaint text and similar wording cannot establish the operational cause.</span></div><div class="cause-path"><div class="cause-node"><small>REPORTED PROBLEM</small><p>${h(record.category)}</p></div>${icon('arrow')}<div class="cause-node"><small>NEXT CHECK</small><p>${h(record.questions[0])}</p></div></div>${record.service_gap ? `<div class="service-gap"><strong>There may also be a service-process issue</strong><p>${h(record.service_gap.hypothesis)}. ${h(record.service_gap.check)}</p><div class="feature-tags">${record.service_gap.evidence_ids.map(id => `<span class="fact-ref">${h(id)}</span>`).join('')}<span class="policy-id">KB-13</span></div></div>` : ''}</div></section>
    ${llmCard(record)}
    <section class="panel"><div class="panel-head"><h2>What the complaint actually says</h2><span class="subtle-badge">EXACT SOURCE QUOTES</span></div><div class="panel-body">${record.facts.map(fact => `<div class="fact-row"><span class="fact-ref">${h(fact.id)}</span><p>“${h(fact.quote)}”</p></div>`).join('')}</div></section>
    <section class="panel"><div class="panel-head"><h2>Verify before deciding</h2>${icon('search')}</div><div class="panel-body"><ul class="checklist">${record.questions.map(q => `<li>${icon('square')}<span>${h(q)}</span></li>`).join('')}</ul></div></section>
    <section class="panel"><div class="panel-head"><h2>Resolve the case. Improve the process.</h2>${icon('target')}</div><div class="panel-body">${record.actions.map(action => `<div class="action-item">${tag(action.kind,'outline')}<p>${h(action.title)}</p><div class="action-owner">${icon('user')}${h(action.owner)}</div></div>`).join('')}</div></section></div>
    <aside class="case-side"><section class="panel"><div class="panel-head"><h2>Case overview</h2></div><div class="panel-body"><div class="metadata-row"><span>Priority</span>${tag(record.priority)}</div><div class="metadata-row"><span>Reported problem</span><strong>${h(record.category)}</strong></div><div class="metadata-row"><span>Suggested owner</span><strong>${h(record.owner)}</strong></div><div class="metadata-row"><span>Customer tone</span><strong>${h(record.tone)} <span style="font-size:8px;font-weight:400">(heuristic)</span></strong></div><div class="metadata-row"><span>Analysis time</span><strong>${record.baseline_seconds}s baseline</strong></div><label class="field-label" for="case-status" style="margin-top:17px">Review status</label><select class="status-select" id="case-status">${['Open','Under review','Resolved'].map(status => `<option ${record.status === status ? 'selected' : ''}>${status}</option>`).join('')}</select></div></section>
    <section class="panel"><div class="panel-head"><h2>Intent model</h2>${icon('scan')}</div><div class="panel-body"><div class="metadata-row"><span>Top model score</span><strong>${pct(record.confidence)}</strong></div><div class="model-score-bar"><div style="width:${record.confidence*100}%"></div></div><p class="score-note">A softmax score for the reported problem. It is not a calibrated probability or root-cause confidence.</p>${record.needs_review ? '<div class="privacy-note">More detail is needed before accepting a complaint category.</div>' : ''}<div class="feature-tags">${record.feature_evidence.slice(0,5).map(term => `<span class="feature-tag">${h(term.term)}</span>`).join('')}</div><p class="score-note">Top positive word features for the proposed category.</p></div></section>
    <div class="local-llm"><h3>${icon('spark')}Deeper local explanation</h3><p>${record.llm ? 'This case has a saved model-generated explanation with checked quotations and playbook references.' : 'Ask the local model to explain the retrieved evidence. First use can take a minute or longer.'}</p><button class="button wide" id="deep-analysis" ${busy || record.llm || record.needs_review ? 'disabled' : ''}>${busy ? '<span class="spinner"></span>Analyzing locally...' : record.llm ? icon('check') + 'Explanation ready' : icon('spark') + 'Generate explanation'}</button>${busy ? '<div class="llm-wait"><span class="spinner"></span><span>The completed triage is available while the local model works.</span></div>' : ''}</div></aside></div>` : state.caseTab === 'evidence' ? `
    <div class="library-notice">${icon('info')}Playbooks are authored investigation examples. Similar queries are not resolved cases or proof of a cause.</div><div class="page-heading" style="margin-top:29px;margin-bottom:18px"><div><h1 style="font-size:20px">Retrieved investigation playbooks</h1><p>Intent-linked guidance plus lexical evidence retrieval</p></div></div><div class="evidence-grid">${record.policies.map(policy => policyCard(policy,true)).join('')}</div><div class="page-heading" style="margin-top:30px;margin-bottom:18px"><div><h1 style="font-size:20px">Similar customer queries</h1><p>${h(record.retrieval_method)} · training split only</p></div></div>${record.similar_cases.map(row => `<article class="similar-card"><div class="similar-meta"><strong>${h(row.title)}</strong><span class="tag outline">Cosine ${Number(row.similarity).toFixed(2)}</span></div><p>“${h(row.text)}”</p><div class="source-line"><span>${h(row.id)} · ${h(row.source)}</span><span>Intent label, no verified resolution</span></div></article>`).join('')}` : `
    <section class="panel"><div class="panel-head"><h2>A draft the reviewer can edit</h2><span class="tag outline">Human review required</span></div><div class="panel-body"><div class="reply-box" id="draft-reply">${h(record.reply)}</div><div class="reply-footer"><p>Review the bank's actual policy and transaction status before using this draft. No deadline or refund outcome is promised.</p><button class="button" id="copy-reply">${icon('copy')}Copy draft</button></div></div></section>`;
  return `<a href="#complaints" class="back-link">${icon('back')}Back to complaints</a><div class="page-heading case-heading"><div><div class="eyebrow">COMPLAINT ANALYSIS</div><h1>${h(record.title)}</h1><div class="case-subtitle"><span class="case-id">${h(record.id)}</span>${tag(record.category,'outline')}${tag(record.priority)}${record.needs_review ? tag('Needs review','warning') : ''}</div></div><div class="heading-actions"><a href="/api/complaints/${h(record.id)}/report" class="button">${icon('download')}Download report</a></div></div><div class="case-tabs" role="tablist">${[['analysis','Analysis'],['evidence','Evidence'],['reply','Draft reply']].map(([key,label]) => `<button role="tab" aria-selected="${state.caseTab===key}" class="${state.caseTab===key?'active':''}" data-case-tab="${key}">${label}</button>`).join('')}</div>${main}`;
}

function knowledgePage(data) {
  return `<div class="page-heading"><div><div class="eyebrow">THE EVIDENCE LIBRARY</div><h1>A place to start checking.</h1><p>Investigation playbooks connect the reported problem to the records a reviewer needs.</p></div><span class="tag outline">${data.items.length} authored playbooks</span></div><div class="library-notice">${icon('info')}${h(data.notice)}</div><div class="input-wrap" style="margin-bottom:23px;max-width:430px">${icon('search')}<input id="search-knowledge" aria-label="Search playbooks" placeholder="Search a problem, mechanism or evidence source..."></div><div class="evidence-grid" id="knowledge-grid">${data.items.map(row => policyCard(row)).join('')}</div>`;
}

function confusionGrid(matrix, labels) {
  const codes = ['DC','UP','DP','CW','PC','PT','FT','RT','IT','RF','AT','LC'];
  const max = Math.max(1, ...matrix.flat());
  return `<div class="confusion-container"><div class="confusion-grid"><div class="matrix-cell label"></div>${codes.map(code => `<div class="matrix-cell label">${code}</div>`).join('')}${matrix.map((row,i) => `<div class="matrix-cell label">${codes[i]}</div>${row.map((value,j) => `<div class="matrix-cell" title="Actual: ${h(labels[i].title)}; predicted: ${h(labels[j].title)}; ${value} queries" style="background:rgba(123,157,99,${value ? .08+.65*value/max : .025});color:${value > max/2 ? '#fff' : '#829e6e'}">${value || '·'}</div>`).join('')}`).join('')}</div></div><div class="matrix-legend">${labels.map((row,i) => `<span><b>${codes[i]}</b>${h(row.title)}</span>`).join('')}</div>`;
}

function methodologyPage(data) {
  const winner = data.experiments.find(row => row.selected);
  const counts = data.provenance.counts;
  const retrieval = data.retrieval;
  return `<div class="page-heading"><div><div class="eyebrow">METHODS, DATA AND EVIDENCE</div><h1>A demo you can explain.</h1><p>Reproducible experiments built around the course's emphasis on fundamentals and honest evaluation.</p></div><div class="heading-actions"><a class="button" href="/api/experiments">${icon('download')}Results CSV</a><a class="button" href="/docs" target="_blank" rel="noopener">${icon('flask')}API docs</a></div></div>
    <section class="method-metrics"><div class="method-metric"><strong>${num(counts.train)}</strong><span>Training queries · vocabulary and model fit</span></div><div class="method-metric"><strong>${num(counts.dev)}</strong><span>Validation queries · feature selection</span></div><div class="method-metric"><strong>${num(counts.test)}</strong><span>Official held-out test queries</span></div></section>
    <div class="method-layout"><section class="panel"><div class="panel-head"><div><h2>Controlled feature comparison</h2><p>Same splits, softmax classifier, optimizer and stopping rule</p></div><span class="subtle-badge">MACRO-F1</span></div><div class="table-wrap"><table class="method-table"><thead><tr><th>Features</th><th>Dimensions</th><th>Validation</th><th>Test</th></tr></thead><tbody>${data.experiments.map(row => `<tr class="${row.selected?'selected':''}"><td>${h(row.name)}${row.selected ? '<br><span class="tag green">Selected on validation</span>' : ''}</td><td>${num(row.features)}</td><td>${pct(row.dev.macro_f1)}</td><td><strong>${pct(row.test.macro_f1)}</strong></td></tr>`).join('')}</tbody></table></div><div class="method-note">Own TF-IDF, softmax regression, Adam and macro-F1. NumPy performs array operations; SciPy stores sparse vectors. Test labels are excluded from feature and checkpoint selection.</div></section>
    <section class="panel"><div class="panel-head"><h2>The analysis pipeline</h2>${icon('scan')}</div><div class="panel-body pipeline">${[['Normalize and mask','NFKC, word tokenization, common-identifier masking'],['Classify the reported problem','From-scratch TF-IDF and multiclass logistic regression'],['Retrieve relevant context','Investigation playbooks and training-query neighbors'],['Explain a working hypothesis','Local LLM with checked quotes and citation IDs'],['Verify and assign next steps','Human review of records, ownership and prevention']].map(([title,text],i) => `<div class="pipeline-item"><span class="step-number">${i+1}</span><div><strong>${title}</strong><p>${text}</p></div></div>`).join('')}</div></section></div>
    <div class="method-sections"><section class="panel"><div class="panel-head"><div><h2>Held-out confusion matrix</h2><p>Rows are actual labels; columns are predicted labels. Hover for each pair.</p></div><span class="tag green">${pct(winner.test.accuracy)} accuracy</span></div><div class="panel-body">${confusionGrid(winner.test.confusion_matrix,data.labels)}</div></section>
    ${retrieval ? `<section class="panel"><div class="panel-head"><div><h2>Does semantic retrieval find the right kind of complaint?</h2><p>${num(retrieval.index_count)} training queries in the index · ${retrieval.dimensions}-dimensional sentence vectors</p></div><span class="tag outline">${h(retrieval.embedding_model)}</span></div><div class="panel-body"><div class="retrieval-comparison">${[['TF-IDF cosine retrieval',retrieval.tfidf],['MiniLM semantic retrieval',retrieval.minilm]].map(([name,result]) => `<div class="retrieval-result"><h3>${name}</h3><strong>${pct(result.intent_hit_at_3)}</strong><p>Intent hit@3 on ${result.count} held-out queries</p><p>Nearest-query intent accuracy: ${pct(result.nearest_intent_accuracy)}</p></div>`).join('')}</div><p class="score-note" style="margin-top:15px">${h(retrieval.interpretation)} ${h(retrieval.query_split)}.</p><div class="panel-head" style="padding:19px 0 0"><div><h2>Recurring themes in sentence-vector clusters</h2><p>Own spherical K-means · k = 6 · seed ${retrieval.seed}</p></div></div><div class="clusters">${retrieval.clusters.map(cluster => `<div class="cluster-card"><h3>Cluster ${cluster.id}<span>${cluster.size} queries</span></h3><p>${cluster.terms.map(h).join(' · ')}</p></div>`).join('')}</div></div></section>` : ''}
    <section class="panel"><div class="panel-head"><h2>What these results establish</h2>${icon('info')}</div><div class="panel-body"><ul class="notes-list"><li>BANKING77 by Casanueva et al. (2020), licensed CC BY 4.0. This prototype selects 12 complaint-related intents from the original 77. It does not report a full BANKING77 benchmark score.</li><li>The official test split is preserved. A stratified 15% validation split is taken from the cleaned official training pool. Seed: ${data.seed}. Exact training duplicates removed: ${data.provenance.removed_train_duplicates}. Exact train/test overlap removed: ${data.provenance.removed_train_test_exact_overlap}.</li><li>${h(data.root_cause_evaluation)} Operational hypotheses need bank records and human review.</li><li>${h(data.llm_evaluation)} Quote and citation checks establish source fidelity, not factual or causal correctness.</li><li>The 24 starting inbox cases and ${state.knowledge?.items?.length || 13} playbooks are authored demonstration examples. Priority and tone use explicit heuristics. Common-identifier masking is incomplete by design and is not a privacy guarantee.</li></ul><div class="source-line"><span>Data revision: ${h(data.provenance.revision.slice(0,12))} · model selected on validation macro-F1</span><a class="text-link" href="${h(data.provenance.url)}" target="_blank" rel="noopener">Dataset and license ${icon('arrow')}</a></div></div></section></div>`;
}

async function route() {
  const version = ++state.routeVersion;
  const hash = location.hash.slice(1) || 'overview';
  const page = hash.startsWith('case/') ? 'case' : hash;
  setNav(page === 'case' ? 'complaints' : page);
  content.innerHTML = '<div class="page-loading"><span class="spinner"></span>Loading...</div>';
  window.scrollTo(0,0);
  try {
    if (!state.methodology) state.methodology = await api('/api/methodology');
    let html;
    if (page === 'overview') {
      state.overview = await api('/api/overview');
      document.getElementById('nav-count').textContent = state.overview.total;
      html = overviewPage(state.overview,state.methodology);
    } else if (page === 'complaints') html = complaintsPage(await api('/api/complaints'));
    else if (page === 'analyze') html = analyzePage();
    else if (page === 'case') {
      state.record = await api('/api/complaints/' + encodeURIComponent(hash.split('/')[1]));
      state.caseTab = 'analysis';
      html = casePage(state.record);
    } else if (page === 'knowledge') {
      state.knowledge = await api('/api/knowledge');
      html = knowledgePage(state.knowledge);
    } else if (page === 'methodology') html = methodologyPage(state.methodology);
    else { location.hash = 'overview'; return; }
    if (version === state.routeVersion) content.innerHTML = html;
  } catch (error) {
    if (version === state.routeVersion) content.innerHTML = `<div class="empty-state">${icon('alert')}<p>${h(error.message)}</p><a class="button" href="#overview">Return to overview</a></div>`;
  }
}

async function deepAnalyze(recordId) {
  if (state.pending.has(recordId)) return;
  state.pending.add(recordId);
  if (state.record?.id === recordId && location.hash === '#case/'+recordId) content.innerHTML = casePage(state.record);
  try {
    const result = await api('/api/complaints/'+encodeURIComponent(recordId)+'/deep-analysis',{method:'POST'});
    if (state.record?.id === recordId) state.record = result;
    toast('Local explanation saved. Source quotations and citations checked.');
  } catch (error) {
    toast(error.message,true);
  } finally {
    state.pending.delete(recordId);
    if (state.record?.id === recordId && location.hash === '#case/'+recordId) content.innerHTML = casePage(state.record);
  }
}

document.addEventListener('click', async event => {
  const sample = event.target.closest('[data-sample]');
  if (sample) {
    const value = samples[Number(sample.dataset.sample)];
    document.getElementById('complaint-title').value = value.title;
    document.getElementById('complaint-text').value = value.text;
    document.getElementById('character-count').textContent = value.text.length + ' / 4,000';
    document.getElementById('complaint-text').focus();
    return;
  }
  const caseRow = event.target.closest('[data-case]');
  if (caseRow) { location.hash = 'case/' + caseRow.dataset.case; return; }
  const tab = event.target.closest('[data-case-tab]');
  if (tab && state.record) { state.caseTab = tab.dataset.caseTab; content.innerHTML = casePage(state.record); return; }
  if (event.target.closest('#deep-analysis') && state.record) { deepAnalyze(state.record.id); return; }
  if (event.target.closest('#copy-reply') && state.record) {
    try { await navigator.clipboard.writeText(state.record.reply); toast('Draft copied for review.'); }
    catch { toast('Select the draft text and copy it manually.',true); }
  }
});

document.addEventListener('keydown', event => {
  if (event.target.matches('[data-case]') && ['Enter',' '].includes(event.key)) {
    event.preventDefault(); location.hash = 'case/' + event.target.dataset.case;
  }
});

document.addEventListener('submit', async event => {
  if (event.target.id !== 'analyze-form') return;
  event.preventDefault();
  const button = document.getElementById('analyze-button');
  if (button.disabled) return;
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Classifying and retrieving evidence...';
  document.getElementById('form-error').textContent = '';
  const useLLM = document.getElementById('use-llm').checked;
  try {
    const form = new FormData(event.target);
    const record = await api('/api/analyze',{method:'POST',body:JSON.stringify(Object.fromEntries(form))});
    document.getElementById('nav-count').textContent = Number(document.getElementById('nav-count').textContent)+1;
    location.hash = 'case/' + record.id;
    if (Object.keys(record.redactions).length) toast('Common identifiers were masked before this case was stored.');
    if (useLLM && !record.needs_review) {
      state.pending.add(record.id);
      // The route loads the saved baseline immediately; generation runs in
      // parallel and updates that case only if it is still being viewed.
      try {
        const result = await api('/api/complaints/'+record.id+'/deep-analysis',{method:'POST'});
        if (state.record?.id === record.id) state.record = result;
        toast('Local explanation saved. Source quotations and citations checked.');
      } catch (error) { toast(error.message,true); }
      finally {
        state.pending.delete(record.id);
        if (state.record?.id === record.id && location.hash === '#case/'+record.id) content.innerHTML = casePage(state.record);
      }
    }
  } catch (error) {
    const field = document.getElementById('form-error');
    if (field) field.textContent = error.message;
    if (document.contains(button)) { button.disabled = false; button.innerHTML = icon('scan') + 'Analyze complaint ' + icon('arrow'); }
    else toast(error.message,true);
  }
});

let searchTimer, filterVersion = 0;
async function filterComplaints() {
  if (location.hash !== '#complaints' || !document.getElementById('search-complaints')) return;
  const version = ++filterVersion;
  const params = new URLSearchParams({query:document.getElementById('search-complaints').value,
    priority:document.getElementById('filter-priority').value,
    status:document.getElementById('filter-status').value,
    category:document.getElementById('filter-category').value});
  try {
    const result = await api('/api/complaints?' + params);
    if (version === filterVersion && location.hash === '#complaints') {
      document.getElementById('complaint-table').innerHTML = complaintTable(result.items);
      document.getElementById('list-count').textContent = result.count + ' complaints';
    }
  } catch (error) { toast(error.message,true); }
}

document.addEventListener('input', event => {
  if (event.target.id === 'complaint-text') document.getElementById('character-count').textContent = event.target.value.length + ' / 4,000';
  if (event.target.id === 'search-complaints') { clearTimeout(searchTimer); searchTimer = setTimeout(filterComplaints,180); }
  if (event.target.id === 'search-knowledge') {
    const query = event.target.value.toLowerCase();
    const items = state.knowledge.items.filter(row => (row.title + ' ' + row.text + ' ' + row.id).toLowerCase().includes(query));
    document.getElementById('knowledge-grid').innerHTML = items.length ? items.map(row => policyCard(row)).join('') : '<div class="empty-state">No matching investigation playbooks.</div>';
  }
});

document.addEventListener('change', async event => {
  if (event.target.id.startsWith('filter-')) filterComplaints();
  if (event.target.id === 'case-status' && state.record) {
    const id = state.record.id;
    try {
      const result = await api('/api/complaints/'+id,{method:'PATCH',body:JSON.stringify({status:event.target.value})});
      if (state.record?.id === id) state.record = result;
      toast('Review status saved.');
    } catch (error) { toast(error.message,true); }
  }
});

async function initialize() {
  document.querySelectorAll('[data-icon]').forEach(element => element.innerHTML = icon(element.dataset.icon));
  try {
    state.health = await api('/api/health');
    const status = document.getElementById('model-status');
    status.innerHTML = '<span class="status-dot"></span>' + (state.health.llm.available ? 'Local LLM available' : 'Local NLP ready');
    status.title = state.health.llm.available ? state.health.llm.model + ' via Ollama' : 'Baseline works without Ollama';
  } catch { /* The route reports a connection error with a useful message. */ }
  await route();
}
window.addEventListener('hashchange',route);
initialize();
