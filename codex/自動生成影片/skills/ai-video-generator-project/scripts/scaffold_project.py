from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy the reusable AI video generator project template."
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Directory that should receive the project template.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target directory if it already exists.",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="Optional display name to inject into .env.example.",
    )
    return parser.parse_args()


def copy_template(source_dir: Path, target_dir: Path, force: bool) -> None:
    if target_dir.exists():
        if not force:
            raise FileExistsError(
                f"Target directory already exists: {target_dir}. "
                "Use --force to replace it."
            )
        shutil.rmtree(target_dir)

    shutil.copytree(source_dir, target_dir)


def update_project_name(target_dir: Path, project_name: str | None) -> None:
    if not project_name:
        return

    env_example_path = target_dir / ".env.example"
    if not env_example_path.exists():
        return

    content = env_example_path.read_text(encoding="utf-8")
    updated = content.replace(
        "PROJECT_NAME=AI自動影片生成系統",
        f"PROJECT_NAME={project_name}",
    )
    env_example_path.write_text(updated, encoding="utf-8")


def main() -> None:
    args = parse_args()
    skill_dir = Path(__file__).resolve().parents[1]
    template_dir = skill_dir / "assets" / "project-template"
    target_dir = Path(args.target).resolve()

    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    copy_template(template_dir, target_dir, args.force)
    update_project_name(target_dir, args.project_name)
    print(f"Project scaffold created at: {target_dir}")


if __name__ == "__main__":
    main()
