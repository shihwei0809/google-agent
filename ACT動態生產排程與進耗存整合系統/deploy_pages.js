const fs = require('fs');
const path = require('path');
const blake3 = require('C:/Users/C606/AppData/Roaming/npm/node_modules/wrangler/node_modules/blake3-wasm');

// Load environment variables from C:\GOOGLE ANGET\.env
const envFile = 'C:/GOOGLE ANGET/.env';
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, 'utf-8').split('\n')) {
    const m = line.match(/^\s*([A-Za-z0-9_]+)=(.*)$/);
    if (m) process.env[m[1]] = m[2].trim();
  }
}

const API_TOKEN = process.env.CLOUDFLARE_API_TOKEN;
const ACCOUNT_ID = process.env.CLOUDFLARE_ACCOUNT_ID;
const CF_API_BASE = 'https://api.cloudflare.com/client/v4';

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.css': 'text/css; charset=utf-8',
  '.ico': 'image/x-icon'
};

function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return MIME_TYPES[ext] || 'application/octet-stream';
}

function hashFile(filePath) {
  const contents = fs.readFileSync(filePath);
  const base64Contents = contents.toString('base64');
  const ext = path.extname(filePath).substring(1);
  return blake3.hash(base64Contents + ext).toString('hex').slice(0, 32);
}

function collectFiles(dir, baseDir = dir) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectFiles(fullPath, baseDir));
    } else if (entry.isFile()) {
      const relPath = '/' + path.relative(baseDir, fullPath).replace(/\\/g, '/');
      results.push({
        relPath,
        fullPath,
        hash: hashFile(fullPath),
        contentType: getMimeType(fullPath)
      });
    }
  }
  return results;
}

async function deployProject(projectName, publicDir) {
  console.log(`\n🚀 [Cloudflare Pages Deploy] Project: ${projectName}`);
  console.log(`📁 Source folder: ${publicDir}`);

  const files = collectFiles(publicDir);
  console.log(`📦 Found ${files.length} files to sync.`);

  // 1. Get upload token
  console.log('🔑 Fetching upload token...');
  const tokenRes = await fetch(`${CF_API_BASE}/accounts/${ACCOUNT_ID}/pages/projects/${projectName}/upload-token`, {
    headers: { Authorization: `Bearer ${API_TOKEN}` }
  });
  const tokenData = await tokenRes.json();
  if (!tokenData.success) {
    throw new Error('Failed to get upload-token: ' + JSON.stringify(tokenData.errors));
  }
  const jwt = tokenData.result.jwt;

  // 2. Check missing hashes
  console.log('🔍 Checking for missing file hashes on Cloudflare...');
  const hashes = files.map(f => f.hash);
  const checkRes = await fetch(`${CF_API_BASE}/pages/assets/check-missing`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${jwt}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ hashes })
  });
  const checkData = await checkRes.json();
  if (!checkData.success) {
    throw new Error('Check missing failed: ' + JSON.stringify(checkData.errors));
  }
  const missingHashes = new Set(checkData.result || []);
  console.log(`⚡ Missing hashes needing upload: ${missingHashes.size} / ${files.length}`);

  // 3. Upload missing assets in batches
  if (missingHashes.size > 0) {
    const toUpload = files.filter(f => missingHashes.has(f.hash));
    const payload = toUpload.map(f => ({
      key: f.hash,
      value: fs.readFileSync(f.fullPath).toString('base64'),
      metadata: { contentType: f.contentType },
      base64: true
    }));

    console.log(`⬆️ Uploading ${payload.length} assets...`);
    const uploadRes = await fetch(`${CF_API_BASE}/pages/assets/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${jwt}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    const uploadData = await uploadRes.json();
    if (!uploadData.success) {
      throw new Error('Asset upload failed: ' + JSON.stringify(uploadData.errors));
    }
    console.log('✅ Asset upload complete!');
  } else {
    console.log('✨ All file hashes already exist on Cloudflare Edge!');
  }

  // 4. Create deployment
  console.log('🌐 Creating deployment...');
  const manifest = {};
  for (const f of files) {
    manifest[f.relPath] = f.hash;
  }

  const formData = new FormData();
  formData.append('manifest', JSON.stringify(manifest));
  formData.append('branch', 'main');
  formData.append('commit_dirty', 'true');

  const deployRes = await fetch(`${CF_API_BASE}/accounts/${ACCOUNT_ID}/pages/projects/${projectName}/deployments`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${API_TOKEN}` },
    body: formData
  });

  const deployData = await deployRes.json();
  if (!deployData.success) {
    throw new Error('Create deployment failed: ' + JSON.stringify(deployData.errors));
  }

  const url = deployData.result.url;
  console.log(`🎉 SUCCESS! Deployment active at: ${url}`);
  console.log(`🌍 Project domain: https://${projectName}.pages.dev\n`);
  return url;
}

async function main() {
  const publicDir = path.resolve(__dirname, 'public');
  try {
    await deployProject('prod-planner-pwa', publicDir);
    await deployProject('act-planner-pwa', publicDir);
    console.log('====================================================');
    console.log('🎯 All deployments finished successfully!');
    console.log('👉 https://prod-planner-pwa.pages.dev');
    console.log('👉 https://act-planner-pwa.pages.dev');
    console.log('====================================================');
  } catch (err) {
    console.error('❌ Deployment error:', err);
    process.exit(1);
  }
}

main();
