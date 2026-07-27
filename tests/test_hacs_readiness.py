"""HACS pre-submission checks.

These tests assert every requirement HACS validates when you submit an
integration to the default repository. They scan the actual on-disk
files; no network calls.

If any of these fail, HACS will reject the submission. Fix the failing
assertion before tagging a release.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = REPO_ROOT / "custom_components" / "mnemos"


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _read_json(rel: str) -> dict:
    return json.loads(_read(rel))


def test_manifest_json_parses():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    assert manifest["domain"]
    assert manifest["name"]
    assert manifest["version"]
    assert manifest["config_flow"] is True
    assert manifest["iot_class"]
    assert manifest["codeowners"]


def test_manifest_version_is_semver():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    semver = re.compile(r"^\d+\.\d+\.\d+$")
    assert semver.match(manifest["version"]), (
        f"manifest.json version must be SemVer (X.Y.Z), got {manifest['version']!r}"
    )


def test_manifest_domain_matches_folder():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    assert manifest["domain"] == INTEGRATION_ROOT.name, (
        "Domain in manifest.json must match the folder name under custom_components/"
    )


def test_hacs_json_parses():
    hacs = _read_json("hacs.json")
    assert hacs["name"]
    assert hacs["homeassistant"]


def test_hacs_name_matches_manifest_name():
    hacs = _read_json("hacs.json")
    manifest = _read_json("custom_components/mnemos/manifest.json")
    assert hacs["name"] == manifest["name"], (
        "hacs.json `name` must match manifest.json `name`"
    )


def test_hacs_homeassistant_minimum_is_valid():
    hacs = _read_json("hacs.json")
    assert hacs["homeassistant"] >= "2025.1.0"


def test_readme_present():
    assert (REPO_ROOT / "README.md").exists()
    readme = _read("README.md")
    assert len(readme) > 200, "README.md is too short"
    assert "Mnemos" in readme


def test_info_md_present():
    assert (REPO_ROOT / "info.md").exists()
    info = _read("info.md")
    assert len(info) > 50


def test_license_present_and_mit_compatible():
    assert (REPO_ROOT / "LICENSE").exists()
    license_text = _read("LICENSE").lower()
    assert "mit" in license_text or "apache" in license_text or "bsd" in license_text


def test_codeowners_are_github_handles():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    for owner in manifest["codeowners"]:
        assert owner.startswith("@"), f"codeowner {owner!r} must start with @"


def test_issue_tracker_url_is_github():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    assert "github.com" in manifest["issue_tracker"], (
        "issue_tracker should be a GitHub URL so HACS can route users correctly"
    )


def test_no_underscored_or_private_modules():
    """HACS rejects any custom_components/*/.* files."""
    for path in (REPO_ROOT / "custom_components" / "mnemos").rglob("*"):
        if path.is_file() and path.name.startswith("."):
            if path.name not in {".gitkeep"}:
                pytest.fail(f"Hidden file at {path} — HACS rejects these")


def test_brand_assets_exist():
    brand_dir = INTEGRATION_ROOT / "brand"
    assert brand_dir.is_dir()
    required = {"icon.png", "logo.png"}
    present = {p.name for p in brand_dir.iterdir() if p.is_file()}
    missing = required - present
    assert not missing, f"Missing brand assets: {missing}"


def test_translations_present():
    """HACS expects at least English translations for the config flow."""
    translations = INTEGRATION_ROOT / "translations" / "en.json"
    assert translations.is_file(), "translations/en.json is required"
    data = json.loads(translations.read_text(encoding="utf-8"))
    assert "config" in data, "translations/en.json must have a `config` block"
    assert "error" in data.get("config", {}), "config error strings must be translated"


def test_services_have_descriptions():
    """HACS shows service descriptions in the UI. Empty descriptions look broken."""
    services_yaml = (INTEGRATION_ROOT / "services.yaml").read_text(encoding="utf-8")
    assert "identify:" in services_yaml
    assert "refresh:" in services_yaml
    assert "description:" in services_yaml


def test_pyproject_toml_present():
    """HACS now requires a `pyproject.toml` at the repo root so it can detect
    the project for release automation and publish metadata."""
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.is_file(), (
        "pyproject.toml is required at the repo root for HACS submission"
    )
    text = pyproject.read_text(encoding="utf-8")
    assert "[build-system]" in text
    assert "[project]" in text
    assert "name" in text
    assert "version" in text


def test_pyproject_name_matches_domain():
    pyproject_text = _read("pyproject.toml")
    manifest = _read_json("custom_components/mnemos/manifest.json")
    match = re.search(r'^name\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    assert match, "pyproject.toml must declare `name`"
    name = match.group(1)
    assert name.startswith(manifest["domain"]), (
        f"pyproject.toml `name` {name!r} should start with the integration "
        f"domain {manifest['domain']!r} (HACS uses this to associate the project)"
    )


def test_pyproject_version_matches_manifest():
    """Keep pyproject.toml `version` and manifest.json `version` in sync —
    HACS uses the manifest value but a mismatch is a smell that one is stale."""
    pyproject_text = _read("pyproject.toml")
    manifest = _read_json("custom_components/mnemos/manifest.json")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    assert match, "pyproject.toml must declare `version`"
    assert match.group(1) == manifest["version"], (
        f"pyproject.toml version {match.group(1)!r} does not match "
        f"manifest.json version {manifest['version']!r}"
    )


def test_pyproject_runtime_deps_match_manifest():
    """The `dependencies` list in pyproject.toml should agree with
    `manifest.json` `requirements`."""
    pyproject_text = _read("pyproject.toml")
    manifest = _read_json("custom_components/mnemos/manifest.json")
    declared = set(re.findall(r'"([a-zA-Z0-9_.\-]+[<>~=!].+?)"', pyproject_text))
    declared_pkgs = {
        re.split(r"[<>=!~]", d, maxsplit=1)[0].lower() for d in declared
    }
    manifest_pkgs = {
        re.split(r"[<>=!~]", r, maxsplit=1)[0].lower()
        for r in manifest.get("requirements", [])
    }
    missing = manifest_pkgs - declared_pkgs
    assert not missing, (
        f"pyproject.toml dependencies missing packages from manifest: {missing}"
    )


def test_iot_class_is_valid():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    valid = {
        "local_polling",
        "local_push",
        "cloud_polling",
        "cloud_push",
    }
    assert manifest["iot_class"] in valid, (
        f"iot_class must be one of {valid}, got {manifest['iot_class']!r}"
    )


def test_dependencies_is_a_list():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    assert isinstance(manifest.get("dependencies", []), list)


def test_requirements_pinned():
    manifest = _read_json("custom_components/mnemos/manifest.json")
    for req in manifest.get("requirements", []):
        assert any(c in req for c in (">=", "==", "<=")), (
            f"Requirement {req!r} is unpinned — HACS requires version constraints"
        )


def test_no_test_only_packages_in_manifest_requirements():
    """Test-only packages must live in tests/requirements-test.txt, not in
    the integration's runtime requirements (which get baked into images)."""
    manifest = _read_json("custom_components/mnemos/manifest.json")
    forbidden = {"pytest", "pytest-asyncio", "pytest-aiohttp", "pytest-homeassistant-custom-components"}
    for req in manifest.get("requirements", []):
        pkg = re.split(r"[<>=!~]", req, maxsplit=1)[0].strip().lower()
        assert pkg not in forbidden, (
            f"Test-only package {pkg!r} in manifest.json requirements"
        )


def test_release_workflow_exists_or_release_docs_exist():
    """HACS picks up new releases from GitHub Releases. There must be either:
    - a release workflow (.github/workflows/release*.yml), OR
    - a docs page explaining how to publish.
    """
    wf_dir = REPO_ROOT / ".github" / "workflows"
    wf = list(wf_dir.glob("release*.yml")) if wf_dir.exists() else []
    has_workflow = bool(wf)
    has_docs = (REPO_ROOT / "docs" / "HACS-Publishing.md").exists()
    assert has_workflow or has_docs, (
        "HACS submission requires either a release workflow or release docs"
    )


def test_identify_endpoint_used_in_services():
    """The `mnemos.identify` service must use the public identify endpoint."""
    services_src = _read("custom_components/mnemos/services.py")
    api_src = _read("custom_components/mnemos/api.py")
    assert "client.identify(" in services_src or ".identify(" in services_src
    assert "/api/v1/identify" in api_src


def test_version_stamped_in_manifest():
    """manifest.json `version` is what HACS shows users. Don't leave it at 0.x."""
    manifest = _read_json("custom_components/mnemos/manifest.json")
    parts = manifest["version"].split(".")
    major = int(parts[0])
    assert major >= 1, (
        f"manifest.json version is {manifest['version']!r}. "
        "Bump to 1.0.0 or higher before submitting to HACS default."
    )