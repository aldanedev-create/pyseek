from pathlib import Path
import shutil

from teloce.build import build_project


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    # Avoid feeding a previous published bundle back into the source asset
    # copier on repeated builds.
    shutil.rmtree(ROOT / "public" / "static", ignore_errors=True)
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    result = build_project(ROOT, options={"dev": False, "source_maps": False})
    # Publish Teloce's dist artifact to the directory served by Vercel.
    dist = ROOT / "dist"
    published = ROOT / "public"
    for source in (dist / "static", dist / "public"):
        if not source.exists():
            continue
        destination = published if source.name == "public" else published / "static"
        destination.mkdir(parents=True, exist_ok=True)
        for item in source.rglob("*"):
            if item.is_file():
                target = destination / item.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    print(result)
