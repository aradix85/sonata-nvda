# coding: utf-8
"""
Tests for the voice-key derivation helpers in voice_download.py:

  - _voice_key_from_filename(stem)  -> str | None
  - _voice_key_from_config(config)  -> str  (raises ValueError on missing fields)

These helpers feed `install_voice_from_tar_archive` — the filename path is the
fast path; the config path is the fallback used when a user provides an
archive whose .onnx file doesn't follow the
<language>-<name>-<quality> naming convention (upstream bug
mush42/sonata-nvda#47).

The helpers are extracted from voice_download.py as text rather than imported
because voice_download depends on NVDA-only modules. `normalizeLanguage` is
stubbed as identity for the exec namespace.
"""

import os
import re

import pytest


_VOICE_DOWNLOAD_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "addon",
    "globalPlugins",
    "sonata_tts_global_plugin",
    "voice_download.py",
)


def _load_helpers():
    """Extract VOICE_INFO_REGEX + the two helpers and exec them in a clean
    namespace with a stubbed normalizeLanguage."""
    with open(_VOICE_DOWNLOAD_PATH, encoding="utf-8") as f:
        src = f.read()

    regex_match = re.search(
        r"VOICE_INFO_REGEX\s*=\s*re\.compile\(\s*(.*?)\)\s*\n",
        src,
        re.DOTALL,
    )
    assert regex_match, "VOICE_INFO_REGEX not found"

    fn_match = re.search(
        r"def _voice_key_from_filename\(stem\):.*?(?=\ndef )",
        src,
        re.DOTALL,
    )
    assert fn_match, "_voice_key_from_filename not found"

    cfg_match = re.search(
        r"def _voice_key_from_config\(config\):.*?(?=\ndef )",
        src,
        re.DOTALL,
    )
    assert cfg_match, "_voice_key_from_config not found"

    ns = {"re": re, "normalizeLanguage": lambda x: x}
    exec(f"VOICE_INFO_REGEX = re.compile({regex_match.group(1)})", ns)
    exec(fn_match.group(0), ns)
    exec(cfg_match.group(0), ns)
    return ns["_voice_key_from_filename"], ns["_voice_key_from_config"]


_voice_key_from_filename, _voice_key_from_config = _load_helpers()


class TestVoiceKeyFromFilename:
    @pytest.mark.parametrize("stem,expected", [
        ("en_US-lessac-medium", "en_US-lessac-medium"),
        ("en_GB-southern_english_female-low", "en_GB-southern_english_female-low"),
        ("pl_PL-mls_6892-low", "pl_PL-mls_6892-low"),
        ("vi_VN-vivos-x_low", "vi_VN-vivos-x_low"),
        ("en_US-amy+RT-medium", "en_US-amy+RT-medium"),
    ])
    def test_parses_canonical(self, stem, expected):
        assert _voice_key_from_filename(stem) == expected

    @pytest.mark.parametrize("stem", [
        "aivars",              # the case from upstream #47 — no separators at all
        "voice",                # single word
        "aivars-medium",       # missing language part
        "en-foo-banana",       # quality not in {high,medium,low,x-low,x_low}
    ])
    def test_returns_none_on_mismatch(self, stem):
        assert _voice_key_from_filename(stem) is None


class TestVoiceKeyFromConfig:
    """Modern Piper configs have language.code, dataset, audio.quality —
    enough to construct a voice_key even when the filename is non-standard.
    """

    @pytest.mark.parametrize("config,expected", [
        (
            {"language": {"code": "en_US"}, "dataset": "lessac", "audio": {"quality": "medium"}},
            "en_US-lessac-medium",
        ),
        (
            {"language": {"code": "lv_LV"}, "dataset": "aivars", "audio": {"quality": "medium"}},
            "lv_LV-aivars-medium",
        ),
        (
            {"language": {"code": "pl_PL"}, "dataset": "mls_6892", "audio": {"quality": "low"}},
            "pl_PL-mls_6892-low",
        ),
    ])
    def test_derives_key(self, config, expected):
        assert _voice_key_from_config(config) == expected

    def test_replaces_dashes_in_dataset(self):
        """Dashes inside dataset/quality would break the X-Y-Z structure of voice_key."""
        config = {"language": {"code": "en_US"}, "dataset": "my-dataset", "audio": {"quality": "medium"}}
        assert _voice_key_from_config(config) == "en_US-my_dataset-medium"

    def test_replaces_dashes_in_quality(self):
        config = {"language": {"code": "en_US"}, "dataset": "foo", "audio": {"quality": "x-low"}}
        assert _voice_key_from_config(config) == "en_US-foo-x_low"

    @pytest.mark.parametrize("config", [
        {},                                                                  # totally empty
        {"language": {"code": "en_US"}},                                      # no dataset
        {"language": {"code": "en_US"}, "dataset": "x"},                      # no audio
        {"dataset": "x", "audio": {"quality": "medium"}},                     # no language
        {"language": {}, "dataset": "x", "audio": {"quality": "medium"}},     # language without code
        {"language": "en_US", "dataset": "x", "audio": {"quality": "medium"}},# language as str, not dict
    ])
    def test_missing_field_raises(self, config):
        with pytest.raises(ValueError, match="missing required fields"):
            _voice_key_from_config(config)
