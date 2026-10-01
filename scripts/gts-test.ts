import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from 'node:fs/promises';
import {assert, assertMatch} from '@std/assert';
import {dirname, fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('../', import.meta.url));
const gtsCli = join(root, 'node_modules/gts/build/src/cli.js');
const prettierCli = join(root, 'node_modules/prettier/bin/prettier.cjs');

function run(command: string, args: string[], cwd: string) {
  // The gts CLI cannot start under the Permission Model because its CLI loads process.binding.
  const result = spawnSync('env', ['-u', 'NODE_OPTIONS', command, ...args], {
    cwd,
    env: {...process.env, NODE_PATH: join(root, 'node_modules')},
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (result.error) throw result.error;
  return {
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

function gts(args: string[], cwd: string) {
  return run(process.execPath, [gtsCli, ...args], cwd);
}

function prettier(args: string[], cwd: string) {
  return run(process.execPath, [prettierCli, ...args], cwd);
}

function output(result: ReturnType<typeof run>) {
  return (
    new TextDecoder().decode(result.stdout) +
    new TextDecoder().decode(result.stderr)
  );
}

void test('gts and Prettier configs enforce style, boundaries and vendor exclusions', async () => {
  const temp = await mkdtemp('/tmp/gts-test-');
  try {
    for (const config of ['eslint.config.js', 'eslint.ignores.js'])
      await copyFile(join(root, config), join(temp, config));
    // Prettier's configuration is the `prettier` key of the root package.json.
    const {prettier: prettierConfig} = JSON.parse(
      await readFile(join(root, 'package.json'), 'utf8'),
    ) as {prettier?: unknown};
    assert(prettierConfig !== undefined, 'package.json has no prettier key');
    await writeFile(
      join(temp, 'package.json'),
      JSON.stringify({prettier: prettierConfig}),
    );
    await writeFile(
      join(temp, 'tsconfig.json'),
      JSON.stringify(
        {
          compilerOptions: {
            module: 'ESNext',
            moduleResolution: 'Bundler',
            target: 'ESNext',
            types: ['node'],
          },
          include: ['**/*.ts'],
        },
        null,
        2,
      ),
    );
    const write = async (path: string, source: string) => {
      const file = join(temp, path);
      await mkdir(dirname(file), {recursive: true});
      await writeFile(file, source);
    };

    await write('compliant.ts', "export const value = 'ok';\n");
    const compliant = gts(['lint', 'compliant.ts'], temp);
    assert(compliant.success, output(compliant));

    await write(
      'floating.ts',
      'async function finish(): Promise<void> {}\n' +
        'export function start(): void {\n  finish();\n}\n',
    );
    const floating = gts(['lint', 'floating.ts'], temp);
    assert(!floating.success);
    assertMatch(output(floating), /@typescript-eslint\/no-floating-promises/);

    await write('formatting.ts', 'export const value = "double";\n');
    const formatting = gts(['lint', 'formatting.ts'], temp);
    assert(!formatting.success);
    assertMatch(output(formatting), /prettier\/prettier/);

    const sameSource = 'console.log("synthetic");\n';
    await write('scripts/vendor/deviation.js', sameSource);
    await write('scripts/local/deviation.js', sameSource);
    const vendored = gts(['lint', 'scripts/vendor/deviation.js'], temp);
    assert(vendored.success, output(vendored));
    const repositoryOwned = gts(['lint', 'scripts/local/deviation.js'], temp);
    assert(!repositoryOwned.success);
    assertMatch(output(repositoryOwned), /prettier\/prettier/);

    await write('format.json', '{"value" : 1}\n');
    const jsonFormatting = prettier(['--check', 'format.json'], temp);
    assert(!jsonFormatting.success);
    assertMatch(output(jsonFormatting), /format\.json/);
  } finally {
    await rm(temp, {recursive: true, force: true});
  }
});
