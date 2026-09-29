import {Deno as deno} from '@deno/shim-deno';

type DenoShim = typeof deno & {exitCode?: number};

declare global {
  namespace Deno {
    type DirEntry = import('@deno/shim-deno').Deno.DirEntry;
    type FileInfo = import('@deno/shim-deno').Deno.FileInfo;
  }
  var Deno: DenoShim;
}

const shim: DenoShim = {...deno};
Object.defineProperty(shim, 'exitCode', {
  get: () => process.exitCode,
  set: (value: number | undefined) => {
    process.exitCode = value;
  },
});
globalThis.Deno = shim;
