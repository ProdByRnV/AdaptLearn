import { describe, expect, it } from 'vitest'

import { difficultyLabel, domainLabel, groupByDifficulty, impliedPrerequisites, listNames } from '@/lib/topics'
import { topicGraph } from '@/test/fixtures'

const { nodes } = topicGraph()
const byId = new Map(nodes.map((t) => [t.id, t]))

describe('impliedPrerequisites', () => {
  it('includes every prerequisite further back, mapped to the topic that needs it', () => {
    const implied = impliedPrerequisites(byId, ['react_hooks'])
    expect([...implied.keys()].sort()).toEqual(['html_basics', 'javascript_fundamentals', 'props_state', 'react_fundamentals'])
    expect(implied.get('html_basics')).toEqual(['react_hooks'])
  })

  it('lists every selected topic that needs a shared prerequisite', () => {
    const implied = impliedPrerequisites(byId, ['react_hooks', 'react_router'])
    expect(implied.get('react_fundamentals')).toEqual(['react_hooks', 'react_router'])
    expect(implied.has('react_router')).toBe(false)
  })

  it('leaves out selected and excluded topics', () => {
    const implied = impliedPrerequisites(byId, ['flexbox', 'css_basics'], new Set(['html_basics']))
    expect(implied.size).toBe(0)
  })

  it('a root topic implies nothing, an empty selection implies nothing', () => {
    expect(impliedPrerequisites(byId, ['html_basics']).size).toBe(0)
    expect(impliedPrerequisites(byId, []).size).toBe(0)
  })

  it('survives a cycle or an unknown id without looping', () => {
    const cyclic = new Map([
      ['a', { prerequisites: ['b'] }],
      ['b', { prerequisites: ['a', 'missing'] }],
    ])
    expect([...impliedPrerequisites(cyclic, ['a']).keys()].sort()).toEqual(['b', 'missing'])
  })
})

describe('display helpers', () => {
  it('groups by difficulty, lowest first, keeping order', () => {
    const groups = groupByDifficulty([nodes[6], nodes[0], nodes[3], nodes[1]])
    expect(groups.map((g) => g.level)).toEqual([1, 2, 3])
    expect(groups[0].topics.map((t) => t.id)).toEqual(['css_basics', 'html_basics'])
  })

  it.each([
    [1, 'Beginner'],
    [2, 'Intermediate'],
    [3, 'Advanced'],
    [4, 'Expert'],
    [7, 'Level 7'],
  ])('difficulty %i is %s', (level, label) => {
    expect(difficultyLabel(level)).toBe(label)
  })

  it('names domains', () => {
    expect(domainLabel('web-development')).toBe('Web Development')
    expect(domainLabel('data-science')).toBe('Data Science')
  })

  it.each([
    [[], ''],
    [['A'], 'A'],
    [['A', 'B'], 'A and B'],
    [['A', 'B', 'C'], 'A, B and 1 more'],
    [['A', 'B', 'C', 'D'], 'A, B and 2 more'],
  ])('listNames %j', (names, text) => {
    expect(listNames(names)).toBe(text)
  })
})
