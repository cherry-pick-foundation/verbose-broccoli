import {StdioServerTransport} from '@modelcontextprotocol/sdk/server/stdio.js';
import {server} from '../upstream/src/index.ts';

await server.connect(new StdioServerTransport());
