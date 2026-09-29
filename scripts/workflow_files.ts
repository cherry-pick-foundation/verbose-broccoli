import {globSync} from 'node:fs';
import {createRequire} from 'node:module';
import {lstat} from 'node:fs/promises';
import {join, relative} from '@std/path';
import {z} from '@zod/zod';

const ignores = (
  createRequire(import.meta.url)('../eslint.ignores.js') as string[]
).map(pattern => pattern.replace(/\/$/, ''));

export const repositoryFileSchema = z
  .string()
  .min(1)
  .refine(
    path =>
      !/[\\*?[\]{}\0]/.test(path) &&
      !/^[A-Za-z]:/.test(path) &&
      path
        .split('/')
        .every(part => part !== '' && part !== '.' && part !== '..'),
    'Use canonical repository-relative literal file paths.',
  );

export function listCodeFiles(root: string) {
  return [
    ...globSync('**/*.{ts,tsx,js,jsx,mts,cts,mjs,cjs}', {
      cwd: root,
      exclude: [...ignores, '**/node_modules/**', '**/.git/**'],
      withFileTypes: true,
    }),
  ]
    .filter(entry => entry.isFile() && !entry.isSymbolicLink())
    .map(entry => relative(root, join(entry.parentPath, entry.name)))
    .sort();
}

export async function getFileAccessError(
  root: string,
  path: string,
  existingCode: boolean,
) {
  if (existingCode && !/\.(?:[jt]sx?|[cm][jt]s)$/.test(path))
    return `File is not a supported code file: ${path}`;
  let target = root;
  try {
    for (const part of path.split('/')) {
      target = join(target, part);
      const info = await lstat(target);
      if (
        info.isSymbolicLink() ||
        (target === join(root, path) && !info.isFile())
      )
        return `File must be a regular file without symlink components: ${path}`;
    }
  } catch (error) {
    if (!existingCode && (error as NodeJS.ErrnoException).code === 'ENOENT')
      return;
    return `Cannot inspect file ${path}: ${String(error)}`;
  }
}
