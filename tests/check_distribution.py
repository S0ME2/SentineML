"""Check built distributions contain runtime assets and no local secrets/state."""

import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path


def check(directory: Path) -> None:
    (wheel,) = directory.glob("*.whl")
    (source,) = directory.glob("*.tar.gz")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required = {
            "app/__init__.py",
            "app/main.py",
            "app/web/index.html",
            "app/web/app.js",
            "app/web/styles.css",
            "app/web/tokens.css",
            "app/web/fonts/sora.ttf",
            "app/web/fonts/DM-Sans-OFL.txt",
            "app/web/fonts/IBM-Plex-Mono-OFL.txt",
            "app/web/fonts/Sora-OFL.txt",
            "app/web/fonts/OFL.txt",
            "app/web/icons/sprite.svg",
            "app/web/icons/LICENSE.txt",
            "sentinelml_client.py",
        }
        assert required <= names, required - names
        (metadata_path,) = (p for p in names if p.endswith(".dist-info/METADATA"))
        metadata = BytesParser().parsebytes(archive.read(metadata_path))
        assert metadata["Name"] == "sentinelml"
        assert metadata["Version"] == "0.1.0"
        assert metadata["License-Expression"] == "Apache-2.0"
        assert set(metadata.get_all("License-File")) == {"LICENSE", "NOTICE"}
        assert any(p.endswith("/licenses/NOTICE") for p in names)
        assert not any(p.startswith(("tests/", "docs/", "sql/")) for p in names)
    with tarfile.open(source) as archive:
        members = archive.getnames()
        names = {name.split("/", 1)[1] for name in members if "/" in name}
        for required in (
            "pyproject.toml",
            "uv.lock",
            "sql/database.sql",
            "docker-compose.yaml",
            "Dockerfile",
            "MANIFEST.in",
            "README.md",
            "NOTICE",
            "CHANGELOG.md",
            "docs/SETUP.md",
            "examples/track_experiment.py",
            "tests/check_distribution.py",
            ".env.example",
            ".env.docker.example",
        ):
            assert required in names, required
        assert not any(
            part in {".codex", ".venv", "__pycache__", ".git", "backups"}
            for name in names
            for part in Path(name).parts
        )
        assert not any(
            Path(name).name.startswith(".env")
            and name not in {".env.example", ".env.docker.example"}
            for name in names
        )
    print(
        "Distribution checks passed: server, client, UI/assets/licenses; "
        "complete source archive; no local state."
    )


if __name__ == "__main__":
    check(Path(sys.argv[1]))
