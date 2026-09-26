import {relative, resolve} from '@std/path';
import type {ICruiseResult} from 'dependency-cruiser';
import ts from 'typescript';

const extensions = Object.values(ts.Extension).sort(
  (a, b) => b.length - a.length,
);
const unique = <T>(items: T[]) => [
  ...new Map(items.map(item => [JSON.stringify(item), item])).values(),
];

export async function inspectSymbol(
  root: string,
  graph: ICruiseResult,
  file: string,
  line: number,
  column: number,
) {
  const modules = new Map(
    graph.modules.map(module => [resolve(root, module.source), module]),
  );
  const texts = new Map<string, string>();
  for (const name of modules.keys())
    texts.set(name, await Deno.readTextFile(name));
  const service = ts.createLanguageService({
    getCompilationSettings: () => ({
      target: ts.ScriptTarget.ESNext,
      module: ts.ModuleKind.ESNext,
      moduleResolution: ts.ModuleResolutionKind.Bundler,
      jsx: ts.JsxEmit.Preserve,
      allowImportingTsExtensions: true,
      allowJs: true,
      noEmit: true,
      noLib: true,
      types: [],
    }),
    getScriptFileNames: () => [...texts.keys()],
    getScriptVersion: () => '0',
    getScriptSnapshot: name => {
      const text = texts.get(name);
      return text === undefined
        ? undefined
        : ts.ScriptSnapshot.fromString(text);
    },
    getCurrentDirectory: () => root,
    getDefaultLibFileName: () => '',
    useCaseSensitiveFileNames: () => ts.sys.useCaseSensitiveFileNames,
    fileExists: name => texts.has(name),
    readFile: name => texts.get(name),
    resolveModuleNameLiterals: (literals, containing) =>
      literals.map(literal => {
        const edge = modules
          .get(containing)
          ?.dependencies.find(
            dependency =>
              dependency.module === literal.text && !dependency.couldNotResolve,
          );
        const name = edge ? resolve(root, edge.resolved) : '';
        const extension = extensions.find(value => name.endsWith(value));
        return {
          resolvedModule:
            texts.has(name) && extension
              ? {
                  resolvedFileName: name,
                  extension,
                }
              : undefined,
        };
      }),
  });
  try {
    const name = resolve(root, file);
    const source = service.getProgram()?.getSourceFile(name);
    if (!source)
      throw new Error(
        `Symbol file is outside the local code snapshot: ${file}`,
      );
    const starts = source.getLineStarts();
    if (
      !Number.isInteger(line) ||
      !Number.isInteger(column) ||
      line < 1 ||
      line > starts.length ||
      column < 1
    )
      throw new Error(
        'Symbol position must use valid 1-based UTF-16 line and column.',
      );
    const text = source.text
      .slice(starts[line - 1], starts[line] ?? source.text.length)
      .replace(/\r?\n$/, '');
    if (column > text.length + 1)
      throw new Error('Symbol column is outside the selected line.');
    const position = source.getPositionOfLineAndCharacter(line - 1, column - 1);
    const definitions = (
      service.getDefinitionAtPosition(name, position) ?? []
    ).filter(item => item.kind !== ts.ScriptElementKind.alias);
    const references = service.findReferences(name, position) ?? [];
    if (!definitions.length && !references.length)
      throw new Error('No resolvable local symbol at this position.');
    const location = (name: string, span: ts.TextSpan, symbol?: string) => {
      const source = service.getProgram()?.getSourceFile(name);
      if (!source || !texts.has(name))
        throw new Error(
          `Symbol location is outside the local code snapshot: ${name}`,
        );
      const start = source.getLineAndCharacterOfPosition(span.start);
      return {
        file: relative(root, name),
        line: start.line + 1,
        column: start.character + 1,
        name:
          symbol === name
            ? relative(root, name)
            : (symbol ??
              source.text.slice(span.start, span.start + span.length)),
      };
    };
    const prepared = service.prepareCallHierarchy(name, position);
    const items = prepared ? [prepared].flat() : [];
    const relation = (
      target: ts.CallHierarchyItem,
      spans: ts.TextSpan[],
      caller: string,
    ) => ({
      ...location(target.file, target.selectionSpan, target.name),
      calls: unique(spans.map(span => location(caller, span))),
    });
    return {
      status: definitions.length ? 'RESOLVED_LOCAL' : 'UNRESOLVED',
      definitions: unique(
        definitions.map(item =>
          location(item.fileName, item.textSpan, item.name),
        ),
      ),
      references: unique(
        references.flatMap(group =>
          group.references.map(item => location(item.fileName, item.textSpan)),
        ),
      ),
      callers: unique(
        items.flatMap(item =>
          service
            .provideCallHierarchyIncomingCalls(
              item.file,
              item.selectionSpan.start,
            )
            .map(call => relation(call.from, call.fromSpans, call.from.file)),
        ),
      ),
      callees: unique(
        items.flatMap(item =>
          service
            .provideCallHierarchyOutgoingCalls(
              item.file,
              item.selectionSpan.start,
            )
            .map(call => relation(call.to, call.fromSpans, item.file)),
        ),
      ),
      limitations: [
        'Only the supplied local code snapshot and statically resolved import edges are indexed.',
        'External package declarations, standard libraries and Deno globals are not loaded; inferred types and member resolution may be incomplete.',
        'References and call hierarchy are TypeScript static findings, not an exhaustive runtime call graph or a comparison with an earlier revision.',
      ],
    };
  } finally {
    service.dispose();
  }
}
