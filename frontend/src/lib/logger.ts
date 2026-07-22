import { dev } from '$app/environment';
import pino, { type Logger, type LoggerOptions } from 'pino';

const options: LoggerOptions = {
	level: dev ? 'debug' : 'info',
	// pino-pretty is a devDependency; production logs plain JSON
	...(dev && {
		transport: {
			target: 'pino-pretty',
			options: {
				colorize: true
			}
		}
	})
};

export const logger: Logger = pino(options);
