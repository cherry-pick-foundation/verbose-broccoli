import {assert, assertEquals} from '@std/assert';
import {walk} from '@std/fs';
import {fromFileUrl, join, relative} from '@std/path';
import {applyPatch, parsePatch, reversePatch} from 'diff';

const upstreamDirectory = fromFileUrl(new URL('../upstream/', import.meta.url));
const manifestPath = join(upstreamDirectory, 'upstream.json');

type FileRecord = {
  original_sha256: string;
  current_sha256: string;
  diff: string;
};

async function sha256(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new Uint8Array(bytes).buffer,
  );
  return Array.from(new Uint8Array(digest), byte =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

Deno.test('upstream files match their recorded set, hashes, and reverse diffs', async () => {
  const manifest = JSON.parse(await Deno.readTextFile(manifestPath)) as {
    files: Record<string, FileRecord>;
  };
  const actualFiles: string[] = [];
  for await (const entry of walk(upstreamDirectory, {
    includeDirs: false,
    includeSymlinks: true,
  })) {
    const path = relative(upstreamDirectory, entry.path).replaceAll('\\', '/');
    if (path !== 'upstream.json') actualFiles.push(path);
  }
  actualFiles.sort();
  assertEquals(
    actualFiles,
    Object.keys(manifest.files).sort(),
    'upstream copied file set changed',
  );

  for (const [path, record] of Object.entries(manifest.files)) {
    const bytes = await Deno.readFile(join(upstreamDirectory, path));
    assertEquals(
      await sha256(bytes),
      record.current_sha256,
      `${path} current hash differs from its record`,
    );
    if (!record.diff) {
      assertEquals(
        record.current_sha256,
        record.original_sha256,
        `${path} changed without a recorded diff`,
      );
      continue;
    }
    const patches = parsePatch(record.diff);
    assertEquals(
      patches.length,
      1,
      `${path} must have one recorded unified diff`,
    );
    const restored = applyPatch(
      new TextDecoder().decode(bytes),
      reversePatch(patches[0]),
    );
    assert(typeof restored === 'string', `${path} reverse diff did not apply`);
    assertEquals(
      await sha256(new TextEncoder().encode(restored)),
      record.original_sha256,
      `${path} did not restore its original hash`,
    );
  }
});
