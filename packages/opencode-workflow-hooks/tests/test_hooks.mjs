import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'
import { test } from 'node:test'
import plugin from '../src/index.ts'

const named = 'event config dispose chat.message chat.params chat.headers permission.ask command.execute.before tool.execute.before tool.execute.after tool.definition shell.env experimental.chat.messages.transform experimental.chat.system.transform experimental.session.compacting experimental.compaction.autocontinue experimental.text.complete experimental.provider.small_model'.split(' ')
const bus = 'command.executed file.edited file.watcher.updated installation.updated lsp.client.diagnostics lsp.updated message.part.removed message.part.updated message.removed message.updated permission.asked permission.replied server.connected session.created session.compacted session.deleted session.diff session.error session.idle session.status session.updated todo.updated shell.env tool.execute.before tool.execute.after tui.prompt.append tui.command.execute tui.toast.show'.split(' ')

const drainPy = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', 'tools', 'hooklog', 'drain.py')
const drain = () => execFileSync('python3', [drainPy, '--once'], { env: { ...process.env, WORKFLOW_QUALITY_URL: '' } })

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
    drain()
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
    process.env.WORKFLOW_HOOKLOG_SPOOL = path.join(tmp, 'spool-file') // unwritable spool cannot throw or rewrite status
    await writeFile(path.join(tmp, 'spool-file'), 'x')
    await hooks['permission.ask'](input, output)
    assert.equal(output.status, 'ask')
  } finally {
    delete process.env.WORKFLOW_HOOKLOG_SPOOL
    await rm(tmp, { recursive: true, force: true })
  }
})
