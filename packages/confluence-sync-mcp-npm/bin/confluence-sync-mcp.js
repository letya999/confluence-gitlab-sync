#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

function fail(message, error) {
  if (error) {
    console.error(`[confluence-sync-mcp] ${message}: ${error.message}`);
  } else {
    console.error(`[confluence-sync-mcp] ${message}`);
  }
  process.exit(1);
}

function run(cmd, args, opts = {}) {
  const result = spawnSync(cmd, args, {
    stdio: ["ignore", "pipe", "pipe"],
    encoding: "utf8",
    shell: false,
    ...opts,
  });
  if (result.error) return result;
  if (typeof result.status === "number" && result.status !== 0) {
    if (result.stdout) {
      process.stderr.write(result.stdout);
    }
    if (result.stderr) {
      process.stderr.write(result.stderr);
    }
    return { ...result, error: new Error(`${cmd} exited with ${result.status}`) };
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }
  return result;
}

function resolvePythonLauncher() {
  if (process.env.PYTHON_BIN) {
    return { cmd: process.env.PYTHON_BIN, baseArgs: [] };
  }

  if (process.platform === "win32") {
    const py = spawnSync("py", ["-3", "-c", "print('ok')"], { stdio: "ignore", shell: false });
    if (py.status === 0) {
      return { cmd: "py", baseArgs: ["-3"] };
    }
  }

  const candidates = process.platform === "win32" ? ["python", "python3"] : ["python3", "python"];
  for (const cmd of candidates) {
    const probe = spawnSync(cmd, ["-c", "print('ok')"], { stdio: "ignore", shell: false });
    if (probe.status === 0) {
      return { cmd, baseArgs: [] };
    }
  }

  fail("Python 3.11+ not found. Install Python or set PYTHON_BIN");
}

function pickInstallTarget() {
  if (process.env.CONFLUENCE_SYNC_PYTHON_SPEC) {
    return process.env.CONFLUENCE_SYNC_PYTHON_SPEC;
  }

  const localPyProject = path.resolve(__dirname, "../../confluence-sync-mcp/pyproject.toml");
  if (fs.existsSync(localPyProject)) {
    return path.resolve(__dirname, "../../confluence-sync-mcp");
  }

  return "confluence-sync-mcp";
}

function main() {
  const launcher = resolvePythonLauncher();
  const venvDir =
    process.env.CONFLUENCE_SYNC_VENV_DIR || path.join(os.homedir(), ".confluence-sync-mcp", ".venv");
  const installTarget = pickInstallTarget();

  const pythonExe =
    process.platform === "win32"
      ? path.join(venvDir, "Scripts", "python.exe")
      : path.join(venvDir, "bin", "python");

  if (!fs.existsSync(pythonExe)) {
    fs.mkdirSync(venvDir, { recursive: true });
    const created = run(launcher.cmd, [...launcher.baseArgs, "-m", "venv", venvDir]);
    if (created.error) {
      fail("Failed to create virtual environment", created.error);
    }
  }

  const pipInstall = run(pythonExe, ["-m", "pip", "install", "--upgrade", "pip"]);
  if (pipInstall.error) {
    fail("Failed to upgrade pip", pipInstall.error);
  }

  const install = run(pythonExe, ["-m", "pip", "install", "--upgrade", installTarget]);
  if (install.error) {
    fail(`Failed to install Python package target '${installTarget}'`, install.error);
  }

  const forwardedArgs = process.argv.slice(2);
  const server = spawnSync(pythonExe, ["-m", "confluence_sync.server", ...forwardedArgs], {
    stdio: "inherit",
    shell: false,
    env: process.env,
  });

  if (server.error) {
    fail("Failed to launch confluence_sync.server", server.error);
  }

  process.exit(server.status ?? 1);
}

main();
