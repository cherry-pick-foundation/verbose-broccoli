import {execFile} from 'node:child_process';

type Version = {major: number; minor: number; patch: number};
type VersionResult = [valid: boolean, message: string];

const versionLine = /^\*\*Version\*\*: (\d+)\.(\d+)\.(\d+)(?=\s|$)/;
const constitutionPath = '.specify/memory/constitution.md';

function parseVersion(text: string): Version | null {
  const lines = text
    .split(/\r?\n/)
    .filter(line => line.startsWith('**Version**:'));
  if (lines.length !== 1) return null;
  const match = versionLine.exec(lines[0]);
  return match
    ? {
        major: Number(match[1]),
        minor: Number(match[2]),
        patch: Number(match[3]),
      }
    : null;
}

function git(args: string[]) {
  return new Promise<{
    success: boolean;
    code: number;
    stdout: Buffer;
    stderr: Buffer;
  }>((resolve, reject) => {
    execFile(
      'git',
      args,
      {
        encoding: 'buffer',
        maxBuffer: Infinity,
        signal: AbortSignal.timeout(5000),
      },
      (error, stdout, stderr) => {
        if (error && !Number.isInteger(error.code)) {
          reject(error);
          return;
        }
        resolve({
          success: !error,
          code: error ? (error.code as number) : 0,
          stdout,
          stderr,
        });
      },
    );
  });
}

function gitFailure(action: string, code: number | null): VersionResult {
  return [false, `Could not ${action}; git exited with status ${code}.`];
}

export function constitutionVersion(
  type: string | null | undefined,
  breaking: boolean,
  before: string | null,
  after: string | null,
): VersionResult {
  if (before === null || after === null || before === after) {
    return [true, 'Constitution version check does not apply.'];
  }

  const previous = parseVersion(before);
  const current = parseVersion(after);
  if (!previous) {
    return [
      false,
      'The previous constitution version line is missing or malformed.',
    ];
  }
  if (!current) {
    return [
      false,
      `The constitution version line after the commit is missing or malformed (previous version ${previous.major}.${previous.minor}.${previous.patch}).`,
    ];
  }

  let expected: Version;
  if (breaking) expected = {major: previous.major + 1, minor: 0, patch: 0};
  else if (type === 'feat') {
    expected = {major: previous.major, minor: previous.minor + 1, patch: 0};
  } else if (type === 'docs' || type === 'fix') {
    expected = {
      major: previous.major,
      minor: previous.minor,
      patch: previous.patch + 1,
    };
  } else {
    return [
      false,
      `Commit type '${
        type ?? ''
      }' cannot change the constitution (expected version remains ${previous.major}.${previous.minor}.${previous.patch}).`,
    ];
  }

  const expectedText = `${expected.major}.${expected.minor}.${expected.patch}`;
  const previousText = `${previous.major}.${previous.minor}.${previous.patch}`;
  const currentText = `${current.major}.${current.minor}.${current.patch}`;
  return currentText === expectedText
    ? [
        true,
        `Constitution version ${previousText} correctly bumps to ${expectedText}.`,
      ]
    : [
        false,
        `Constitution version ${previousText} with commit type '${type}' requires ${expectedText}; found ${currentText}.`,
      ];
}

interface ParsedCommit {
  type?: string | null;
  notes?: {title?: string}[];
}

export function isBreakingCommit(notes: {title?: string}[] = []) {
  return notes.some(
    note =>
      note.title === 'BREAKING CHANGE' || note.title === 'BREAKING-CHANGE',
  );
}

export async function constitutionVersionRule(
  parsed: ParsedCommit,
): Promise<VersionResult> {
  try {
    const commit = process.env.CONSTITUTION_VERSION_COMMIT;
    const amend = process.env.CONSTITUTION_VERSION_AMEND;
    const headRef = commit ? `${commit}^` : amend ? 'HEAD^' : 'HEAD';
    const head = await git(['rev-parse', '--verify', '--quiet', headRef]);
    if (head.code === 1) {
      return [true, 'Constitution version check does not apply.'];
    }
    if (!head.success) return gitFailure(`check ${headRef}`, head.code);

    const [headPath, indexPath] = await Promise.all([
      git(['ls-tree', '-r', '--name-only', headRef, '--', constitutionPath]),
      commit
        ? git(['ls-tree', '-r', '--name-only', commit, '--', constitutionPath])
        : git(['ls-files', '--error-unmatch', '--', constitutionPath]),
    ]);
    if (!headPath.success)
      return gitFailure(`check the constitution in ${headRef}`, headPath.code);
    if (!indexPath.success && indexPath.code !== 1)
      return gitFailure(
        `check the constitution in ${commit ?? 'the index'}`,
        indexPath.code,
      );
    if (headPath.stdout.length === 0 || indexPath.stdout.length === 0) {
      return [true, 'Constitution version check does not apply.'];
    }

    const [before, after] = await Promise.all([
      git(['show', `${headRef}:${constitutionPath}`]),
      git(['show', `${commit ?? ''}:${constitutionPath}`]),
    ]);
    if (!before.success)
      return gitFailure(`read the constitution from ${headRef}`, before.code);
    if (!after.success)
      return gitFailure(
        `read the constitution from ${commit ?? 'the index'}`,
        after.code,
      );

    return constitutionVersion(
      parsed.type,
      isBreakingCommit(parsed.notes),
      new TextDecoder().decode(before.stdout),
      new TextDecoder().decode(after.stdout),
    );
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    return [false, `Could not inspect the constitution in Git: ${detail}`];
  }
}
