import {expandGlobSync} from '@std/fs';
import {join, relative} from '@std/path';
import {z} from '@zod/zod';
import biome from '../biome.json' with {type: 'json'};

const ignores = biome.files.includes
  .filter(pattern => pattern.startsWith('!'))
  .map(pattern => pattern.replace(/^!+/, ''));

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
    ...expandGlobSync('**/*.{ts,tsx,js,jsx,mts,cts,mjs,cjs}', {
      root,
      exclude: [...ignores, '**/.git/**'],
      followSymlinks: false,
    }),
  ]
    .filter(entry => entry.isFile && !entry.isSymlink)
    .map(entry => relative(root, entry.path))
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
      const info = await Deno.lstat(target);
      if (info.isSymlink || (target === join(root, path) && !info.isFile))
        return `File must be a regular file without symlink components: ${path}`;
    }
  } catch (error) {
    if (!existingCode && error instanceof Deno.errors.NotFound) return;
    return `Cannot inspect file ${path}: ${String(error)}`;
  }
}
