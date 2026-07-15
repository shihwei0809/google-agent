import subprocess
from typing import Sequence


def run_command(
    command: Sequence[str],
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a system command and raise a readable error when it fails."""
    result = subprocess.run(
        list(command),
        check=False,
        capture_output=capture_output,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else "未知錯誤"
        raise RuntimeError(f"指令執行失敗: {' '.join(command)} | {stderr}")
    return result
