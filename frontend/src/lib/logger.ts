import pino, { type Logger, type LoggerOptions } from 'pino';

const options: LoggerOptions = {
	transport: {
		target: 'pino-pretty',
		options: {
			colorize: true
		}
	}
};

export const logger: Logger = pino(options);
