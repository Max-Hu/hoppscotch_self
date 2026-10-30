import { randomBytes } from 'node:crypto';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const envPath = fileURLToPath(new URL('.env', import.meta.url));
const templatePath = fileURLToPath(new URL('.env.example', import.meta.url));
const secretLengths = {
  POSTGRES_PASSWORD: 48,
  DATA_ENCRYPTION_KEY: 32,
  JWT_SECRET: 64,
  SESSION_SECRET: 64,
  PROXYSCOTCH_TOKEN: 48,
};

function validate(content) {
  const values = Object.fromEntries(content.split(/\r?\n/)
    .filter(line => line.trim() && !line.trim().startsWith('#'))
    .map(line => {
      const separator = line.indexOf('=');
      if (separator < 1) throw new Error('Invalid .env entry. Use KEY=value.');
      return [line.slice(0, separator).trim(), line.slice(separator + 1).trim()];
    }));
  for (const [name, length] of Object.entries(secretLengths)) {
    if (!new RegExp(`^[a-f0-9]{${length}}$`, 'i').test(values[name] ?? '')) {
      throw new Error(`${name} must contain ${length} hexadecimal characters. Existing .env was not changed.`);
    }
  }
  const ports = ['APP_PORT', 'MAILPIT_PORT', 'PROXY_PORT'].map(name => {
    const port = Number(values[name]);
    if (!/^\d+$/.test(values[name] ?? '') || !Number.isInteger(port) || port < 1024 || port > 65535) {
      throw new Error(`${name} must be an integer between 1024 and 65535.`);
    }
    return port;
  });
  if (new Set(ports).size !== ports.length) throw new Error('The three host ports must be different.');
  if (!/^[a-z0-9][a-z0-9_-]*$/.test(values.COMPOSE_PROJECT_NAME ?? '')) {
    throw new Error('COMPOSE_PROJECT_NAME must use lowercase letters, digits, underscores or hyphens.');
  }
}

try {
  if (existsSync(envPath)) {
    validate(readFileSync(envPath, 'utf8'));
    console.log('Existing .env validated and preserved. No passwords or keys were changed.');
  } else {
    if (process.argv.includes('--check')) throw new Error('.env is missing. Run docker compose run --rm init first.');
    let content = readFileSync(templatePath, 'utf8');
    for (const [name, length] of Object.entries(secretLengths)) {
      content = content.replace(new RegExp(`^${name}=.*$`, 'm'), `${name}=${randomBytes(length / 2).toString('hex')}`);
    }
    validate(content);
    writeFileSync(envPath, content, { flag: 'wx', mode: 0o600 });
    console.log('Created .env with random local secrets. No secret values were printed.');
  }
  console.log('Next: docker compose up -d');
} catch (error) {
  console.error(`Configuration error: ${error.message}`);
  process.exitCode = 1;
}
