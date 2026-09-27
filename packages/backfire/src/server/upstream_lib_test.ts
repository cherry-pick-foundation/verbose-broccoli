import {assert, assertEquals} from '@std/assert';
import {ensureUniqueIds, type Identifiable} from '../upstream/src/lib.ts';

function originalEnsureUniqueIds<T extends Identifiable>(
  items: T[],
  fallbackPrefix: string,
): {items: Array<T & {id: string}>; renamed: Map<string, string>} {
  const used = new Set<string>();
  const renamed = new Map<string, string>();
  const out = items.map((item, i) => {
    const raw = item.id ?? '';
    const base =
      raw.replace(/[^A-Za-z0-9_.-]+/g, '_').replace(/^_+|_+$/g, '') ||
      `${fallbackPrefix}${i}`;
    let id = base;
    let n = 1;
    while (used.has(id)) {
      id = `${base}_${n++}`;
    }
    used.add(id);
    if (raw && raw !== id) renamed.set(raw, id);
    return {...item, id} as T & {id: string};
  });
  return {items: out, renamed};
}

Deno.test('ensureUniqueIds preserves duplicate-id results and handles 100,000 shared ids', () => {
  const cases: Identifiable[][] = [
    [{id: 'same'}, {id: 'same'}, {id: 'same'}],
    [{id: 'a'}, {id: 'a_1'}, {id: 'a'}, {id: 'a'}],
    [{id: 'a b'}, {id: 'a_b'}, {}, {id: 'a_b'}],
  ];
  for (const input of cases) {
    assertEquals(
      ensureUniqueIds(input, 'item'),
      originalEnsureUniqueIds(input, 'item'),
    );
  }

  const started = performance.now();
  const result = ensureUniqueIds(
    Array.from({length: 100_000}, () => ({id: 'shared'})),
    'item',
  );
  assert(
    performance.now() - started < 1_000,
    '100,000 duplicate ids must finish within one second',
  );
  assertEquals(result.items.length, 100_000);
  assertEquals(result.items.at(-1)?.id, 'shared_99999');
});
