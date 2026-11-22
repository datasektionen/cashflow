const IMAGE_EXTENSION = /\.(png|jpe?g|gif|webp|bmp|avif|heic|heif)$/i;

export const isImageName = (name: string) => IMAGE_EXTENSION.test(name);

export const fileName = (url: string) =>
	decodeURIComponent(new URL(url).pathname.split('/').pop() ?? '');
