import {createCommand, createReport, runCli} from './cli.ts';
import {glob, readFile} from 'node:fs/promises';
import {relative, resolve} from '@std/path';
import type {TSESLint} from '@typescript-eslint/utils';
import {ESLint, type Linter} from 'eslint';
import ts from 'typescript';
import tseslint from 'typescript-eslint';

const functionKinds = new Set([
  'FunctionDeclaration',
  'FunctionExpression',
  'ArrowFunctionExpression',
]);
const allowedSyntax = [
  'Program',
  'Identifier',
  'Literal',
  'ExportNamedDeclaration',
  'ExportDefaultDeclaration',
  'ExportSpecifier',
  ...functionKinds,
  'BlockStatement',
  'VariableDeclaration',
  'VariableDeclarator',
  'ExpressionStatement',
  'ReturnStatement',
  'IfStatement',
  'ConditionalExpression',
  'BinaryExpression',
  'LogicalExpression',
  'UnaryExpression',
  'UpdateExpression',
  'AssignmentExpression',
  'SequenceExpression',
  'CallExpression',
  'MemberExpression',
  'ForStatement',
  'ForInStatement',
  'ForOfStatement',
  'WhileStatement',
  'DoWhileStatement',
  'BreakStatement',
  'ContinueStatement',
  'EmptyStatement',
  'LabeledStatement',
  'SwitchStatement',
  'SwitchCase',
  'ThrowStatement',
  'TryStatement',
  'CatchClause',
];
const scopeRule: TSESLint.RuleModule<'noFunction' | 'call' | 'reference', []> =
  {
    meta: {
      type: 'problem',
      schema: [],
      messages: {
        noFunction: 'No implemented function in this file.',
        call: 'Call is not bound to an unchanged function defined in this file.',
        reference: 'Value is not a parameter or a locally defined binding.',
      },
    },
    defaultOptions: [],
    create(context) {
      let functions = 0;
      return {
        ':matches(FunctionDeclaration, FunctionExpression, ArrowFunctionExpression)'() {
          functions++;
        },
        CallExpression(node) {
          const variable = context.sourceCode
            .getScope(node)
            .references.find(
              reference => reference.identifier === node.callee,
            )?.resolved;
          const definition = variable?.defs.find(
            entry =>
              entry.type === 'Variable' ||
              (entry.type === 'FunctionName' &&
                functionKinds.has(entry.node.type)),
          );
          const target =
            definition?.type === 'Variable'
              ? definition.node.init
              : definition?.type === 'FunctionName'
                ? definition.node
                : undefined;
          const reassigned = variable?.references.some(
            reference => reference.isWrite() && !reference.init,
          );
          if (!target || !functionKinds.has(target.type) || reassigned) {
            context.report({node, messageId: 'call'});
          }
        },
        'Program:exit'(node) {
          if (functions === 0) {
            context.report({node, messageId: 'noFunction'});
          }
          for (const scope of context.sourceCode.scopeManager!.scopes) {
            for (const reference of scope.references) {
              if (
                reference.isValueReference &&
                !reference.resolved?.defs.length
              ) {
                context.report({
                  node: reference.identifier,
                  messageId: 'reference',
                });
              }
            }
          }
        },
      };
    },
  };

const syntaxRules: Linter.RulesRecord = {
  'scope/bindings': 'error',
  'no-restricted-syntax': [
    'error',
    {
      selector: `*:not(:matches(${allowedSyntax.join(',')})):not([type=/^TS/])`,
      message: 'Syntax is outside the approved function subset.',
    },
    {
      selector: 'Literal[raw=/^["\']/]',
      message:
        'String literals exclude the whole file, regardless of their contents.',
    },
    {
      selector: ':matches(Literal[regex], VariableDeclaration[declare=true])',
      message:
        'Regular expressions and ambient runtime bindings are outside the subset.',
    },
    {
      selector:
        ':matches(TSEnumDeclaration, TSModuleDeclaration, TSImportEqualsDeclaration, TSExportAssignment)',
      message:
        'Runtime TypeScript declarations are outside the function subset.',
    },
  ],
};
const qualityRules: Linter.RulesRecord = {
  'max-lines-per-function': [
    'error',
    {
      max: 20,
      skipBlankLines: false,
      skipComments: false,
      IIFEs: true,
    },
  ],
  '@typescript-eslint/no-explicit-any': 'error',
  '@typescript-eslint/no-unused-vars': [
    'error',
    {
      args: 'all',
      caughtErrors: 'all',
    },
  ],
  'no-unreachable': 'error',
};

function createLinter(cwd: string, rules: Linter.RulesRecord) {
  return new ESLint({
    cwd,
    overrideConfigFile: true,
    overrideConfig: [
      {
        files: ['**/*.{ts,tsx,mts,cts}'],
        languageOptions: {parser: tseslint.parser},
        linterOptions: {noInlineConfig: true},
        plugins: {
          '@typescript-eslint': tseslint.plugin,
          scope: {rules: {bindings: scopeRule}} as unknown as NonNullable<
            Linter.Config['plugins']
          >[string],
        },
        rules,
      },
    ],
  });
}

export async function classifyFile(
  filePath: string,
  source: string,
  cwd: string,
) {
  const [result] = await createLinter(cwd, syntaxRules).lintText(source, {
    filePath,
  });
  const errors = result.messages.filter(message => message.fatal);
  const exclusions = result.messages.filter(
    message => !message.fatal && message.severity === 2,
  );
  return {
    file: relative(cwd, filePath),
    status: errors.length
      ? 'error'
      : exclusions.length
        ? 'excluded'
        : 'included',
    reasons: [
      ...new Map(
        (errors.length ? errors : exclusions).map(message => [
          message.message,
          {
            message: message.message,
            line: message.line,
            column: message.column,
            rule: message.ruleId,
          },
        ]),
      ).values(),
    ],
  };
}

async function discover(cwd: string) {
  const paths = new Set<string>();
  for (const directory of ['plugins', 'packages', 'scripts']) {
    for await (const entry of glob(`${directory}/**/*.{ts,tsx,mts,cts}`, {
      cwd,
      withFileTypes: true,
      exclude: [
        '**/node_modules/**',
        'scripts/vendor/**',
        '**/*.d.{ts,mts,cts}',
      ],
    })) {
      if (entry.isFile() && !entry.isSymbolicLink())
        paths.add(resolve(entry.parentPath, entry.name));
    }
  }
  return [...paths].sort();
}

export async function checkCleanCode(cwd: string, scopeOnly = false) {
  const snapshots = await Promise.all(
    (await discover(cwd)).map(async file => ({
      file,
      source: await readFile(file, 'utf8'),
    })),
  );
  const scope = await Promise.all(
    snapshots.map(({file, source}) => classifyFile(file, source, cwd)),
  );
  const selected = snapshots.filter(
    (_, index) => scope[index].status === 'included',
  );
  const diagnostics: {file: string; message: string; rule: string | null}[] =
    [];
  if (!scopeOnly && !scope.some(file => file.status === 'error')) {
    const linter = createLinter(cwd, qualityRules);
    for (const {file, source} of selected) {
      const [result] = await linter.lintText(source, {filePath: file});
      for (const message of result.messages) {
        diagnostics.push({
          file: relative(cwd, file),
          message: message.message,
          rule: message.ruleId,
        });
      }
    }
    if (selected.length) {
      const options: ts.CompilerOptions = {
        strict: true,
        noEmit: true,
        noUnusedLocals: true,
        noUnusedParameters: true,
        allowUnreachableCode: false,
        target: ts.ScriptTarget.ESNext,
        module: ts.ModuleKind.ESNext,
        moduleResolution: ts.ModuleResolutionKind.Bundler,
        moduleDetection: ts.ModuleDetectionKind.Force,
        skipLibCheck: true,
      };
      const host = ts.createCompilerHost(options);
      const readFile = host.readFile;
      const sourceByPath = new Map(
        selected.map(({file, source}) => [file, source]),
      );
      host.readFile = file => sourceByPath.get(resolve(file)) ?? readFile(file);
      const program = ts.createProgram(
        selected.map(({file}) => file),
        options,
        host,
      );
      for (const {file} of selected) {
        for (const diagnostic of program.getSemanticDiagnostics(
          program.getSourceFile(file),
        )) {
          diagnostics.push({
            file: relative(cwd, file),
            rule: `TS${diagnostic.code}`,
            message: ts.flattenDiagnosticMessageText(
              diagnostic.messageText,
              '\n',
            ),
          });
        }
      }
    }
  }
  const errors = scope.filter(file => file.status === 'error').length;
  return {
    assessment:
      errors || diagnostics.length
        ? 'FAIL'
        : !selected.length
          ? 'NOT_APPLICABLE'
          : scopeOnly
            ? 'SCOPE_ONLY'
            : 'PASS',
    coverage: {
      candidates: scope.length,
      selected: selected.length,
      excluded: scope.filter(file => file.status === 'excluded').length,
      errors,
    },
    scope,
    selected: selected.map(({file}) => relative(cwd, file)),
    diagnostics,
  };
}

if (import.meta.main) {
  await runCli(() =>
    createCommand(
      'clean-code',
      'Check the mechanically selected Clean Code subset from the target workspace root.',
    )
      .option('--scope', 'Report the shared skill/checker file scope only.')
      .action(async options => {
        const result = await checkCleanCode(
          resolve(process.cwd()),
          options.scope ?? false,
        );
        createReport(
          result,
          result.diagnostics.length > 0 ||
            result.scope.some(file => file.status === 'error'),
        );
      })
      .parse(process.argv.slice(2)),
  );
}
