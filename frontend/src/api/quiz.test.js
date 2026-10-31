import { describe, expect, it } from 'vitest'

import { generateQuiz } from '@/api/quiz'
import { fakeServer } from '@/test/helpers'

describe('generateQuiz', () => {
  it('waits up to 25 s, since the server writes the questions and then checks every answer', async () => {
    const server = fakeServer(200, { quiz_id: 'q1' })
    await generateQuiz('css basics')
    const config = server.mock.calls[0][0]
    expect(config.url).toBe('/quiz/generate/css%20basics')
    expect(config.timeout).toBe(25_000)
  })
})
