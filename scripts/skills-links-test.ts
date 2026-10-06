import {test} from 'node:test';
import {assert, assertEquals} from '@std/assert';
import {basename, fromFileUrl, isAbsolute, join, relative} from '@std/path';
import {glob, lstat, readdir, readlink, realpath, stat} from 'node:fs/promises';

const ROOT = fromFileUrl(new URL('../', import.meta.url));
// The folders that hold skills; the next slice adds skills/<area> and
// tools/ponytail/skills.
const SKILL_ROOTS = ['plugins/*/skills'];

async function skillFolders() {
  const folders: string[] = [];
  for (const pattern of SKILL_ROOTS) {
    for await (const root of glob(pattern, {cwd: ROOT})) {
      for (const entry of await readdir(join(ROOT, root))) {
        const folder = join(ROOT, root, entry);
        if ((await stat(folder)).isDirectory()) folders.push(folder);
      }
    }
  }
  return folders;
}

void test('skills: .agents/skills links and skill folders match one to one', async () => {
  const folders = new Set(await skillFolders());
  const names = new Set(Array.from(folders, f => basename(f)));
  assertEquals(names.size, folders.size, 'two skill folders share a name');

  const linksDir = join(ROOT, '.agents/skills');
  const linked = new Map<string, string>();
  for (const name of await readdir(linksDir)) {
    const link = join(linksDir, name);
    assert((await lstat(link)).isSymbolicLink(), `${name} is not a link`);
    assert(!isAbsolute(await readlink(link)), `${name} is an absolute link`);
    const target = await realpath(link);
    assert(folders.has(target), `${name} resolves outside the skill roots`);
    await stat(join(target, 'SKILL.md'));
    assertEquals(basename(target), name, `${name} links to another name`);
    assert(!linked.has(target), `${name} repeats ${linked.get(target)}`);
    linked.set(target, name);
  }
  for (const folder of folders) {
    assert(linked.has(folder), `${relative(ROOT, folder)} has no link`);
  }
});
