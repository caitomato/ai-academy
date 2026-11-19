import { expect, it } from 'vitest';
import { emptyState, migrateState } from './progress';
it('aliases renamed courses without losing old notes or completion evidence', () => {
  const state = emptyState();
  state.completed = ['06-old'];
  state.notes = { '06-old': '我的原笔记' };
  state.scores = { '06-old': 85 };
  state.attempts = [{ id: 'attempt', questionId: 'q-old', answer: ['x'], correct: false, date: '2026-11-19' }];
  const migrated = migrateState(state, { lessonIds: { '06-old': '06-10' }, questionIds: { 'q-old': '06-10-p1' } });
  expect(migrated.completed).toEqual(['06-old', '06-10']);
  expect(migrated.notes['06-10']).toBe('我的原笔记');
  expect(migrated.notes['06-old']).toBe('我的原笔记');
  expect(migrated.attempts[0].questionId).toBe('06-10-p1');
  expect(state.attempts[0].questionId).toBe('q-old');
});
