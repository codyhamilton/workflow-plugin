import assert from 'node:assert/strict'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { createServer } from 'node:http'
import { createHash } from 'node:crypto'
import os from 'node:os'
import path from 'node:path'
import { test } from 'node:test'
import plugin from '../src/index.ts'

const named = 'event config dispose chat.message chat.params chat.headers permission.ask command.execute.before tool.execute.before tool.execute.after tool.definition shell.env experimental.chat.messages.transform experimental.chat.system.transform experimental.session.compacting experimental.compaction.autocontinue experimental.text.complete experimental.provider.small_model'.split(' ')
const bus = 'command.executed file.edited file.watcher.updated installation.updated lsp.client.diagnostics lsp.updated message.part.removed message.part.updated message.removed message.updated permission.asked permission.replied server.connected session.created session.compacted session.deleted session.diff session.error session.idle session.status session.updated todo.updated shell.env tool.execute.before tool.execute.after tui.prompt.append tui.command.execute tui.toast.show'.split(' ')

test('18 callbacks and 28 bus types preserve payloads, outputs, sessions and boundaries', async () => {
  const tmp = await mkdtemp(path.join(os.tmpdir(), 'workflow-hooks-'))
  process.env.WORKFLOW_HOOKLOG_DIR = tmp
  process.env.WORKFLOW_HOOKLOG = 'on'
  process.env.WORKFLOW_OPENCODE_SIGNALS = '0' // capture is independent of soft signals
  try {
    const hooks = await plugin({ directory: '/tmp/project' })
    assert.deepEqual(Object.keys(hooks).sort(), named.sort())
    const input = { sessionID: 's', tool: 'read', callID: 't', args: { path: 'a' } }
    const output = { status: 'ask', args: { path: 'a' }, parts: [{ type: 'text', text: 'prompt' }],
                     text: 'answer', output: 'result', title: 'read a', headers: { Authorization: 'short-secret' },
                     env: { TOKEN: 'short-secret' }, enabled: true }
    for (const name of named.filter(n => !['event', 'dispose'].includes(n))) {
      const before = JSON.stringify({ input, output })
      await hooks[name](input, output)
      assert.equal(JSON.stringify({ input, output }), before, name)
    }
    for (const type of bus) {
      const event = { type, properties: { info: { id: 's', directory: '/tmp/project' } } }
      await hooks.event({ event })
    }
    // Real message/part envelopes put sessionID below properties, alongside unrelated IDs.
    await hooks.event({ event: { type: 'message.part.updated', properties: { part: { id: 'part', sessionID: 's', type: 'step-finish' } } } })
    const cyclic = { sessionID: 's' }
    cyclic.properties = cyclic
    await hooks['chat.params'](cyclic, output)
    const idle = hooks.event({ event: { type: 'session.idle', properties: { sessionID: 's' } } })
    await hooks.dispose() // host bus dispatch can still be in flight during teardown
    await idle
    const rows = (await readFile(path.join(tmp, 'opencode/s.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse)
    assert.deepEqual(new Set(rows.filter(r => r.source === 'hook').map(r => r.hook_event)), new Set(named.filter(n => !['event', 'dispose'].includes(n))))
    assert.deepEqual(new Set(rows.filter(r => r.source === 'bus').map(r => r.hook_event)), new Set(bus))
    assert(rows.filter(r => r.source === 'bus').every(r => r.kind === 'event'))
    assert.equal(rows.filter(r => r.kind === 'tool_call').length, 1)
    assert.equal(rows.find(r => r.kind === 'tool_pre').input.path, 'a')
    assert.deepEqual(rows.find(r => r.kind === 'batch_end').tool_use_ids, ['t'])
    assert.equal(rows.at(-1).hook_event, 'Stop')
    assert.equal(rows.find(r => r.hook_event === 'chat.headers').data.output.headers.Authorization, '[REDACTED]')
    const unknown = (await readFile(path.join(tmp, 'opencode/unknown.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse)
    assert.equal(unknown.at(-1).hook_event, 'dispose')
    process.env.WORKFLOW_HOOKLOG_CLI = path.join(tmp, 'missing.py')
    await hooks['permission.ask'](input, output) // unavailable logger cannot throw or rewrite status
    assert.equal(output.status, 'ask')
  } finally {
    delete process.env.WORKFLOW_HOOKLOG_CLI
    await rm(tmp, { recursive: true, force: true })
  }
})

test('artifact backstop follows tool logging, deduplicates, and preserves tool outputs', async () => {
  const tmp = await mkdtemp(path.join(os.tmpdir(), 'workflow-artifact-hooks-'))
  const saved = { ...process.env }
  const requests = []
  const artifacts = new Map()
  const outcomes = []
  const server = createServer(async (req, res) => {
    let raw = ''
    for await (const chunk of req) raw += chunk
    requests.push([req.method, req.url])
    let response = {}
    if (req.method === 'POST' && ['/v1/designs', '/v1/briefs'].includes(req.url)) {
      const body = JSON.parse(raw)
      const sha = createHash('sha256').update(body.text).digest('hex').slice(0, 16)
      const id = artifacts.get(body.path)?.id || artifacts.size + 1
      const kind = req.url === '/v1/designs' ? 'design' : 'brief'
      const artifact = { id, kind, project: body.project, path: body.path, sha, text: body.text,
                         conversation: body.conversation_id, submission_bound: true }
      artifacts.set(body.path, artifact)
      response = { id, frontmatter: `---\n${kind}_id: ${id}\n---\n` }
    } else if (req.url.startsWith('/v1/sessions/')) {
      const conversation = decodeURIComponent(req.url.split('/').at(-1))
      response = { artifacts: [...artifacts.values()].filter(a => a.conversation === conversation) }
    } else if (/\/v1\/(designs|briefs)\/\d+\/body/.test(req.url)) {
      response = [...artifacts.values()].find(a => a.id === Number(req.url.split('/')[3]))
    } else if (req.url === '/v1/hook-events') {
      outcomes.push(...JSON.parse(raw).rows)
      response = { inserted: 1 }
    }
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(response))
  })
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  process.env.WORKFLOW_QUALITY_URL = `http://127.0.0.1:${server.address().port}`
  process.env.WORKFLOW_HOOKLOG_DIR = path.join(tmp, 'spool')
  process.env.WORKFLOW_OPENCODE_SIGNALS = '0'
  process.env.WORKFLOW_HOOKLOG = 'on'
  delete process.env.WORKFLOW_HOOKLOG_CLI
  delete process.env.WORKFLOW_ARTIFACT_SUBMIT_CLI
  try {
    await mkdir(path.join(tmp, 'docs/plans/example/briefs'), { recursive: true })
    const hooks = await plugin({ directory: tmp })
    for (const [tool, filePath, endpoint] of [
      ['write', 'docs/plans/example/DESIGN.md', '/v1/designs'],
      ['edit', 'docs/plans/example/briefs/01.md', '/v1/briefs'],
    ]) {
      await writeFile(path.join(tmp, filePath), '# Fixture\n')
      const input = { sessionID: 'artifact-session', tool, callID: tool, args: { filePath } }
      const output = { title: 'written', output: 'unchanged tool result' }
      const original = JSON.stringify({ input, output })
      await hooks['tool.execute.after'](input, output)
      await hooks['tool.execute.after'](input, output)
      assert.equal(JSON.stringify({ input, output }), original)
      assert.equal(requests.filter(([method, url]) => method === 'POST' && url === endpoint).length, 1)
    }
    assert.equal(requests[0][1], '/v1/hook-events') // hooklog precedes submission
    assert.equal(outcomes.filter(row => row.tool_name === 'artifact_submit').length, 4)
    assert(outcomes.filter(row => row.tool_name === 'artifact_submit').every(row => row.ok))
    const postCount = requests.filter(([method, url]) => method === 'POST' && ['/v1/designs', '/v1/briefs'].includes(url)).length
    await hooks.event({ event: { type: 'file.edited', properties: { sessionID: 'other-session', file: 'docs/plans/example/DESIGN.md' } } })
    await hooks['tool.execute.after']({ sessionID: 'other-session', tool: 'read', callID: 'read', args: { filePath: 'docs/plans/example/DESIGN.md' } }, { output: '# Fixture' })
    assert.equal(requests.filter(([method, url]) => method === 'POST' && ['/v1/designs', '/v1/briefs'].includes(url)).length, postCount)
    process.env.WORKFLOW_ARTIFACT_SUBMIT_CLI = path.join(tmp, 'missing.py')
    const output = { title: 'written', output: 'preserved through helper failure' }
    await hooks['tool.execute.after']({ sessionID: 'failure-session', tool: 'write', callID: 'failure', args: { filePath: 'docs/plans/example/DESIGN.md' } }, output)
    assert.equal(output.output, 'preserved through helper failure')
    assert.equal(await readFile(path.join(tmp, 'docs/plans/example/DESIGN.md'), 'utf8'), '# Fixture\n')
    await hooks.dispose()
  } finally {
    await new Promise(resolve => server.close(resolve))
    for (const key of Object.keys(process.env)) if (!(key in saved)) delete process.env[key]
    Object.assign(process.env, saved)
    await rm(tmp, { recursive: true, force: true })
  }
})
