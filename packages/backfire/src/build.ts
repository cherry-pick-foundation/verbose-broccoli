import {copy, walk} from '@std/fs';
import {
  basename,
  dirname,
  fromFileUrl,
  join,
  relative,
  resolve,
} from '@std/path';

const root = fromFileUrl(new URL('../../../', import.meta.url));
const runtimePaths = [
  'deno.json',
  'deno.lock',
  'pyproject.toml',
  '.python-version',
  'uv.lock',
  'src/bin',
  'src/upstream',
  'src/server',
  'src/backfire_backend',
];

function refuseExisting(output: string) {
  try {
    Deno.lstatSync(output);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) return;
    throw error;
  }
  throw new Error(`Output already exists: ${output}`);
}

async function build(output: string) {
  output = resolve(output);
  refuseExisting(output);
  const resolvedRoot = await Deno.realPath(root);
  const destination = join(
    await Deno.realPath(dirname(output)),
    basename(output),
  );
  for (const path of [output, destination]) {
    const directory = relative(resolvedRoot, path).split(/[\\/]/)[0];
    if (directory === 'plugins' || directory === 'packages')
      throw new Error(
        `Output must be outside plugins/ and packages/: ${output}`,
      );
  }
  output = destination;
  const maxBytes = 16 * 1024 * 1024;
  const budget = Number(
    Deno.env.get('BACKFIRE_TEST_BUILD_MAX_BYTES') ?? maxBytes,
  );
  if (!Number.isSafeInteger(budget) || budget < 0 || budget > maxBytes)
    throw new Error(
      `BACKFIRE_TEST_BUILD_MAX_BYTES must be between 0 and ${maxBytes}`,
    );

  const interrupted = new AbortController();
  const interrupt = () => interrupted.abort(new Error('Build interrupted'));
  const signals: Deno.Signal[] = ['SIGINT', 'SIGTERM'];
  for (const signal of signals) Deno.addSignalListener(signal, interrupt);
  let partial: string | undefined;
  let bytes = 0;
  try {
    partial = await Deno.makeTempDir({
      dir: dirname(output),
      prefix: `${basename(output)}.partial-`,
    });
    const sources: [string, string, RegExp[]][] = [
      [join(root, 'plugins/code'), partial, []],
      ...runtimePaths.map((path): [string, string, RegExp[]] => [
        join(root, 'packages/backfire', path),
        join(partial!, 'backfire', path),
        path === 'src/server'
          ? [/_test\.ts$/, /[\\/]server[\\/]testing(?:[\\/]|$)/]
          : path === 'src/backfire_backend'
            ? [/[\\/]__pycache__(?:[\\/]|$)/]
            : [],
      ]),
    ];
    for (const [source, target, skip] of sources) {
      const info = await Deno.lstat(source);
      const entries = info.isDirectory
        ? walk(source, {skip})
        : [{path: source, ...info}];
      for await (const entry of entries) {
        interrupted.signal.throwIfAborted();
        if (entry.isSymlink)
          throw new Error(`Source symbolic link is not allowed: ${entry.path}`);
        const destination = join(target, relative(source, entry.path));
        if (entry.isDirectory) {
          await Deno.mkdir(destination, {recursive: true});
        } else if (entry.isFile) {
          bytes += (await Deno.stat(entry.path)).size;
          if (bytes > budget)
            throw new Error(
              `Build exceeds ${budget}-byte budget: ${entry.path}`,
            );
          await Deno.mkdir(dirname(destination), {recursive: true});
          await copy(entry.path, destination);
        } else {
          throw new Error(
            `Source is not a regular file or directory: ${entry.path}`,
          );
        }
      }
    }
    interrupted.signal.throwIfAborted();
    refuseExisting(output);
    Deno.renameSync(partial, output);
    partial = undefined;
    console.log(output);
  } finally {
    try {
      if (partial) await Deno.remove(partial, {recursive: true});
    } finally {
      for (const signal of signals)
        Deno.removeSignalListener(signal, interrupt);
    }
  }
}

try {
  const args = Deno.args[0] === '--' ? Deno.args.slice(1) : Deno.args;
  if (args.length !== 1 || !args[0])
    throw new Error('Usage: deno task backfire:build -- <output>');
  await build(args[0]);
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  Deno.exitCode = 1;
}
