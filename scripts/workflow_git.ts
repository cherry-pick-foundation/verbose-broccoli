import {join} from '@std/path';
import canonicalize from 'canonicalize';
import {sha256} from './hash.ts';

export const repositoryPathspec = ['.'];

export async function runGit(
  cwd: string,
  args: string[],
  allowDifference = false,
): Promise<string> {
  const result = await new Deno.Command('git', {
    cwd,
    args,
    env: {GIT_OPTIONAL_LOCKS: '0', GIT_TERMINAL_PROMPT: '0'},
    stdout: 'piped',
    stderr: 'piped',
  }).output();
  if (
    !result.success &&
    !(allowDifference && result.code === 1 && result.stdout.length > 0)
  ) {
    throw new Error(
      new TextDecoder().decode(result.stderr).trim() ||
        `git failed (${result.code})`,
    );
  }
  return new TextDecoder().decode(result.stdout);
}

async function fileState(root: string, path: string) {
  const parts = path.split('/');
  let target = root;
  for (let index = 0; index < parts.length; index++) {
    target = join(target, parts[index]);
    let info: Deno.FileInfo;
    try {
      info = await Deno.lstat(target);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) return {path, type: 'missing'};
      throw error;
    }
    if (info.isSymlink) {
      return {
        path,
        type: 'symlink',
        at: parts.slice(0, index + 1).join('/'),
        mode: info.mode,
        target: await Deno.readLink(target),
      };
    }
    if (index === parts.length - 1) {
      if (!info.isFile)
        throw new Error(`Unsupported working tree file: ${path}`);
      return {
        path,
        type: 'file',
        mode: info.mode,
        hash: await sha256(await Deno.readFile(target)),
      };
    }
    if (!info.isDirectory)
      throw new Error(`Non-directory ancestor of tracked file: ${path}`);
  }
}

export async function snapshotWorkingTree(
  cwd: string,
): Promise<{revision: string; dirty_hash: string}> {
  // Git enumerates versionable paths; untracked special files are outside this snapshot.
  const root = (await runGit(cwd, ['rev-parse', '--show-toplevel'])).trim();
  const revision = (
    await runGit(root, ['rev-parse', '--verify', 'HEAD^{commit}'])
  ).trim();
  const index = await runGit(root, [
    'ls-files',
    '--stage',
    '-z',
    '--',
    ...repositoryPathspec,
  ]);
  for (const record of index.split('\0').filter(Boolean)) {
    if (!/^(100644|100755|120000) /.test(record))
      throw new Error(
        `Unsupported index file mode: ${record.slice(0, record.indexOf('\t'))}`,
      );
  }
  const [files, status] = await Promise.all([
    runGit(root, [
      'ls-files',
      '--cached',
      '--others',
      '--exclude-standard',
      '-z',
      '--',
      ...repositoryPathspec,
    ]),
    runGit(root, [
      'status',
      '--porcelain=v1',
      '--untracked-files=all',
      '--no-renames',
      '-z',
      '--',
      ...repositoryPathspec,
    ]),
  ]);
  const working = [];
  for (const path of [...new Set(files.split('\0').filter(Boolean))].sort()) {
    working.push(await fileState(root, path));
  }
  const bytes = new TextEncoder().encode(
    canonicalize({revision, index, status, working}),
  );
  return {revision, dirty_hash: await sha256(bytes)};
}
