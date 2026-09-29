import {Buffer} from 'node:buffer';

export async function sha256(data: Uint8Array | string): Promise<string> {
  const bytes =
    typeof data === 'string'
      ? new TextEncoder().encode(data)
      : new Uint8Array(data);
  return Buffer.from(await crypto.subtle.digest('SHA-256', bytes)).toString(
    'hex',
  );
}
