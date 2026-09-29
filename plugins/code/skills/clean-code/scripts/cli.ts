import {Command, ValidationError} from '@cliffy/command';

export {ValidationError};

class CheckFailure extends Error {
  readonly details: unknown;

  constructor(details: unknown) {
    super('The command completed its checks and found violations.');
    this.details = details;
  }
}

export function createCommand(name: string, description: string) {
  return new Command()
    .name(name)
    .description(description)
    .help({colors: false})
    .throwErrors();
}

export function createReport(value: unknown, failed = false) {
  if (failed) throw new CheckFailure(value);
  console.log(JSON.stringify(value, null, 2));
}

export async function runCli(run: () => Promise<unknown>) {
  try {
    if (Deno.args.some(arg => arg === '' || /^--[^=]+=$/.test(arg)))
      throw new ValidationError('Argument values must not be empty.');
    await run();
  } catch (error) {
    const input = error instanceof ValidationError;
    console.error(
      JSON.stringify({
        error: {
          code: input
            ? 'INVALID_ARGUMENT'
            : error instanceof CheckFailure
              ? 'CHECK_FAILED'
              : 'EXECUTION_FAILED',
          message: error instanceof Error ? error.message : String(error),
        },
        ...(error instanceof CheckFailure ? {details: error.details} : {}),
      }),
    );
    Deno.exitCode = input ? 2 : 1;
  }
}
