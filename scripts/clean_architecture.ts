import {
  createCommand,
  createReport,
  runCli,
} from '../plugins/code/skills/clean-code/scripts/cli.ts';
import {existsSync, globSync} from 'node:fs';
import {fromFileUrl, join, relative, resolve} from '@std/path';
import {
  cruise,
  type IConfiguration,
  type ICruiseResult,
} from 'dependency-cruiser';
import ts from 'typescript';

interface PackageConfig {
  name?: string;
  imports?: Record<string, string>;
  exports?: string | Record<string, string>;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
}

const ioPackages =
  '(@hono/hono|hono|@electric-sql/pglite|@kysely/kysely|kysely|drizzle-orm|@modelcontextprotocol/sdk|webdav)';
const ioImport = `^(?:(?:npm|jsr):)?${ioPackages}(?:@|/|$)`;
const resolvedIOImport = `(^|/)node_modules/${ioPackages}/`;
const escapeRegExp = RegExp.escape;

function readPackageConfig(path: string): PackageConfig {
  if (!existsSync(path)) return {};
  const result = ts.readConfigFile(path, ts.sys.readFile);
  if (result.error)
    throw new Error(`Cannot parse package configuration: ${path}`);
  const config = result.config as PackageConfig;
  return {
    name: config.name,
    exports: config.exports,
    imports: {
      ...Object.fromEntries(
        Object.entries({...config.dependencies, ...config.devDependencies}).map(
          ([name, specifier]) => [
            name,
            specifier.startsWith('npm:')
              ? specifier
              : `npm:${name}@${specifier}`,
          ],
        ),
      ),
      ...Object.fromEntries(
        Object.entries(config.imports ?? {}).map(([name, target]) => [
          name,
          /^(?:\.{1,2}\/|\/|file:|npm:|jsr:|node:|https?:|#)/.test(target)
            ? target
            : `npm:${target}`,
        ]),
      ),
    },
  };
}

export function importRules(cwd: string) {
  const configs = [
    {
      directory: cwd,
      value: readPackageConfig(resolve(cwd, 'package.json')),
    },
  ];
  for (const pattern of [
    'plugins/**/package.json',
    'packages/**/package.json',
  ]) {
    for (const entry of globSync(pattern, {
      cwd,
      exclude: ['**/node_modules/**'],
      withFileTypes: true,
    })) {
      if (!entry.isFile() || entry.isSymbolicLink()) continue;
      const path = join(entry.parentPath, entry.name);
      configs.push({
        directory: entry.parentPath,
        value: readPackageConfig(path),
      });
    }
  }
  for (const pattern of ['plugins/*', 'packages/*']) {
    for (const entry of globSync(pattern, {
      cwd,
      withFileTypes: true,
    })) {
      const path = join(entry.parentPath, entry.name);
      if (
        entry.isDirectory() &&
        !entry.isSymbolicLink() &&
        !configs.some(config => config.directory === path)
      ) {
        configs.push({directory: path, value: {}});
      }
    }
  }
  const alias: Record<string, string> = {};
  const external = ['^(?:npm|jsr|node|https?):'];
  const externalAliases: {name: string; pattern: RegExp}[] = [];
  const localNames = new Set<string>();
  const forbiddenIO = [ioImport, resolvedIOImport];
  const forbidden: NonNullable<IConfiguration['forbidden']> = [
    {name: 'no-cycles', severity: 'error', from: {}, to: {circular: true}},
    {
      name: 'domain-dependency-direction',
      severity: 'error',
      from: {path: '(^|/)domain/'},
      to: {
        path: '(^|/)(application|infrastructure|presentation|platform|mcp|cli)/',
      },
    },
    {
      name: 'application-dependency-direction',
      severity: 'error',
      from: {path: '(^|/)application/'},
      to: {path: '(^|/)(infrastructure|presentation|platform|mcp|cli)/'},
    },
    {
      name: 'no-feature-internals',
      severity: 'error',
      from: {path: '^(.*/(?:modules|features)/[^/]+/)'},
      to: {path: '/(?:modules|features)/[^/]+/internal/', pathNot: '^$1'},
    },
    {
      name: 'no-package-to-plugin',
      severity: 'error',
      from: {path: '^packages/'},
      to: {path: '^plugins/'},
    },
    {
      name: 'no-node-in-inner-layers',
      severity: 'error',
      from: {path: '(^|/)(domain|application)/'},
      to: {dependencyTypes: ['core']},
    },
  ];
  for (const {directory, value} of configs) {
    const owner = relative(cwd, directory);
    const imports = {...value.imports};
    const exported =
      typeof value.exports === 'string'
        ? {'.': value.exports}
        : (value.exports ?? {});
    if (/^(plugins|packages)\/[^/]+$/.test(owner)) {
      const publicFiles = Object.values(exported).map(target =>
        resolve(directory, target),
      );
      if (publicFiles.some(file => !file.startsWith(`${directory}/`))) {
        throw new Error(`Public exports must stay inside ${owner}`);
      }
      forbidden.push({
        name: `public-api:${owner}`,
        severity: 'error',
        from: {pathNot: `^${escapeRegExp(owner)}/`},
        to: {
          path: `^${escapeRegExp(owner)}/`,
          pathNot: publicFiles.map(
            file => `^${escapeRegExp(relative(cwd, file))}$`,
          ),
        },
      });
      if (value.name) {
        for (const [subpath, target] of Object.entries(exported)) {
          imports[value.name + (subpath === '.' ? '' : subpath.slice(1))] =
            target;
        }
      }
    }
    for (const [name, target] of Object.entries(imports)) {
      const key = name.endsWith('/') ? name.slice(0, -1) : `${name}$`;
      if (/^(\.{1,2}\/|\/|file:)/.test(target)) {
        localNames.add(name);
        const destination = target.startsWith('file:')
          ? fromFileUrl(target)
          : resolve(directory, target);
        if (alias[key] && alias[key] !== destination) {
          throw new Error(
            `Conflicting local alias needs scoped resolver support: ${name}`,
          );
        }
        alias[key] = destination;
      } else {
        if (!/^(npm|jsr|node|https?):/.test(target)) {
          throw new Error(`Unsupported or conflicting import target: ${name}`);
        }
        const packageRoot = /^(?:npm|jsr):(?:@[^/]+\/)?[^/@]+(?:@[^/]+)?$/.test(
          target,
        );
        const suffix = name.endsWith('/') ? '' : packageRoot ? '(?:/|$)' : '$';
        const pattern = `^${escapeRegExp(name)}${suffix}`;
        externalAliases.push({name, pattern: new RegExp(pattern)});
        external.push(pattern);
        if (new RegExp(ioImport).test(target)) forbiddenIO.push(pattern);
      }
    }
  }
  for (const name of localNames) {
    if (
      externalAliases.some(
        external =>
          external.pattern.test(name) ||
          (name.endsWith('/') &&
            (external.name.startsWith(name) ||
              external.name === name.slice(0, -1))),
      )
    ) {
      throw new Error(
        `Conflicting alias requires scoped resolver support: ${name}`,
      );
    }
  }
  forbidden.push(
    {
      name: 'no-unresolved-local-imports',
      severity: 'error',
      from: {},
      to: {couldNotResolve: true, pathNot: external},
    },
    {
      name: 'no-io-packages-in-inner-layers',
      severity: 'error',
      from: {path: '(^|/)(domain|application)/'},
      to: {path: forbiddenIO},
    },
  );
  return {alias, forbidden};
}

export async function analyzeImportGraph(
  cwd = process.cwd(),
  entryPaths?: string[],
) {
  const {alias, forbidden} = importRules(cwd);
  const result = await cruise(
    entryPaths ??
      ['plugins', 'packages', 'scripts', 'tests'].filter(path =>
        existsSync(resolve(cwd, path)),
      ),
    {
      baseDir: cwd,
      outputType: 'json',
      ruleSet: {forbidden},
      validate: true,
      tsPreCompilationDeps: true,
      exclude: '^scripts/vendor/|\\.md$',
      doNotFollow: {
        path: entryPaths
          ? `^(?!(?:${entryPaths.map(escapeRegExp).join('|')})$)|(^|/)node_modules/`
          : '^(?!(?:plugins|packages|scripts|tests)/)|(^|/)node_modules/',
      },
    },
    {alias},
  );
  return JSON.parse(result.output as string) as ICruiseResult;
}

if (import.meta.main) {
  await runCli(() =>
    createCommand(
      'clean-architecture',
      'Check import directions, cycles and public package boundaries from the workspace root.',
    )
      .action(async () => {
        const result = await analyzeImportGraph();
        const {violations, error, totalCruised} = result.summary;
        createReport({violations, error, totalCruised}, error > 0);
      })
      .parse(process.argv.slice(2)),
  );
}
