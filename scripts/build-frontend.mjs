import { cp, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const frontendDirectory = path.join(projectRoot, 'frontend');
const outputDirectory = path.join(projectRoot, 'dist');
const configuredApiUrl = process.env.AQG_API_BASE_URL?.trim();

if (!configuredApiUrl) {
  throw new Error('AQG_API_BASE_URL must be set to the deployed backend URL.');
}

let apiUrl;
try {
  apiUrl = new URL(configuredApiUrl);
} catch {
  throw new Error('AQG_API_BASE_URL must be an absolute HTTP or HTTPS URL.');
}

if (!['http:', 'https:'].includes(apiUrl.protocol)) {
  throw new Error('AQG_API_BASE_URL must use HTTP or HTTPS.');
}

await mkdir(outputDirectory, { recursive: true });
await cp(frontendDirectory, outputDirectory, { recursive: true });
await writeFile(
  path.join(outputDirectory, 'config.js'),
  `window.AQG_API_BASE_URL = ${JSON.stringify(apiUrl.toString().replace(/\/$/, ''))};\n`,
);
