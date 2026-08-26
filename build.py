from pathlib import Path
import shutil

from teloce.build import build_project


ROOT = Path(__file__).resolve().parent


def patch_component_props(dist: Path) -> None:
    """Bridge dynamic component bindings for the currently supported runtime.

    Teloce compiles ``:prop`` on a component to ``data-teloce-bind-prop``.
    Older generated runtimes applied those bindings to native elements but
    did not expose them through the child component prop reader.  PySeek
    relies on dynamic props for results, stats, and browser history, so patch
    the generated bundle during the build until the runtime release carrying
    this fix is available.
    """
    old = 'if (attribute.name.startsWith(":")) props[attribute.name.slice(1)] = __evaluate(attribute.value, parentState);'
    new = 'if (attribute.name.startsWith("data-teloce-bind-")) props[attribute.name.slice("data-teloce-bind-".length)] = __evaluate(attribute.value, parentState); else if (attribute.name.startsWith(":")) props[attribute.name.slice(1)] = __evaluate(attribute.value, parentState);'
    old_plain = 'else if (!attribute.name.startsWith("data-")) props[attribute.name] = attribute.value;'
    new_plain = 'else if (!attribute.name.startsWith("data-") && !element.hasAttribute("data-teloce-bind-" + attribute.name)) props[attribute.name] = attribute.value;'
    for file in dist.rglob("*.js"):
        source = file.read_text(encoding="utf-8")
        updated = source.replace(old, new).replace(old_plain, new_plain)
        if updated != source:
            file.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    # Avoid feeding a previous published bundle back into the source asset
    # copier on repeated builds.
    shutil.rmtree(ROOT / "public" / "static", ignore_errors=True)
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    result = build_project(ROOT, options={"dev": False, "source_maps": False})
    # Publish Teloce's dist artifact to the directory served by Vercel.
    dist = ROOT / "dist"
    patch_component_props(dist)
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
