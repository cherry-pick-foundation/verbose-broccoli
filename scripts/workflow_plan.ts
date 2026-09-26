import {z} from '@zod/zod';
import {format, type ICruiseResult} from 'dependency-cruiser';
import {analyzeImportGraph} from './clean_architecture.ts';
import {
  getFileAccessError,
  listCodeFiles,
  repositoryFileSchema,
} from './workflow_files.ts';

export const planSchema = z.strictObject({
  tasks: z
    .array(
      z.strictObject({
        id: z.string().trim().min(1),
        files: z.array(repositoryFileSchema).min(1),
      }),
    )
    .min(1)
    .refine(
      tasks => new Set(tasks.map(task => task.id)).size === tasks.length,
      'Task IDs must be unique.',
    ),
});

export type PlanTask = {id: string; files: string[]};
export type PlanResult = {tasks: PlanTask[]; reasons: string[]};

export async function analyzePlan(
  root: string,
  input: unknown,
): Promise<PlanResult> {
  const {tasks} = planSchema.parse(input);
  const reasons: string[] = [];
  const owners = new Map<string, string>();
  for (const task of tasks) {
    for (const path of task.files) {
      const owner = owners.get(path);
      if (owner && owner !== task.id)
        reasons.push(`Tasks ${owner} and ${task.id} both write ${path}`);
      owners.set(path, task.id);
    }
  }
  if (reasons.length) return {tasks, reasons};
  try {
    const realRoot = await Deno.realPath(root);
    for (const path of owners.keys()) {
      const reason = await getFileAccessError(realRoot, path, tasks.length > 1);
      if (reason) reasons.push(reason);
    }
    if (tasks.length === 1 || reasons.length) return {tasks, reasons};
    const entries = listCodeFiles(root);
    const graph = await analyzeImportGraph(root, entries);
    if (graph.summary.error) {
      reasons.push(`Architecture graph has ${graph.summary.error} error(s)`);
      return {tasks, reasons};
    }
    const sources = new Set(graph.modules.map(module => module.source));
    for (const path of owners.keys()) {
      if (!entries.includes(path) || !sources.has(path))
        reasons.push(`Task file is outside the dependency graph: ${path}`);
    }
    if (reasons.length) return {tasks, reasons};
    const affected: Set<string>[] = [];
    for (const task of tasks) {
      const result = await format(graph, {
        outputType: 'json',
        reaches: {path: task.files.map(path => `^${RegExp.escape(path)}$`)},
      });
      const filtered = JSON.parse(result.output as string) as ICruiseResult;
      affected.push(new Set(filtered.modules.map(module => module.source)));
    }
    for (let first = 0; first < tasks.length; first++) {
      for (let second = first + 1; second < tasks.length; second++) {
        const shared = [...affected[first]].filter(path =>
          affected[second].has(path),
        );
        if (shared.length)
          reasons.push(
            `Tasks ${tasks[first].id} and ${tasks[second].id} affect the same files: ${shared.sort().join(', ')}`,
          );
      }
    }
  } catch (error) {
    reasons.push(`Cannot verify parallel dependencies: ${String(error)}`);
  }
  return {tasks, reasons};
}
