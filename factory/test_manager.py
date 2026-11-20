import json
import urllib.error
import unittest
from email.message import Message
from unittest.mock import patch

from factory import manager


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, *_args):
        return self.payload


class GitHubInspectorTests(unittest.TestCase):
    def test_repo_identity_accepts_url_and_rejects_extra_path_segments(self):
        self.assertEqual(manager.repo_identity("https://github.com/acme/app/"), ("acme", "app"))
        with self.assertRaises(ValueError):
            manager.repo_identity("acme/app/tree/main")
        with self.assertRaises(ValueError):
            manager.repo_identity("../app")

    def test_github_get_retries_rate_limit_with_bounded_retry_after(self):
        headers = Message()
        headers["Retry-After"] = "0"
        rate_limit = urllib.error.HTTPError(
            "https://api.github.com/repos/acme/app",
            429,
            "rate limited",
            headers,
            None,
        )
        responses = [rate_limit, FakeResponse({"ok": True})]
        sleeps = []

        def opener(_request, timeout):
            self.assertEqual(timeout, 15)
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        result = manager.github_get(
            "/repos/acme/app",
            opener=opener,
            sleep_fn=sleeps.append,
            max_attempts=2,
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(sleeps, [0.0])

    def test_github_get_fails_fast_when_rate_limit_reset_exceeds_wait_budget(self):
        headers = Message()
        headers["X-RateLimit-Remaining"] = "0"
        headers["X-RateLimit-Reset"] = "1060"
        error = urllib.error.HTTPError(
            "https://api.github.com/repos/acme/app",
            403,
            "rate limited",
            headers,
            None,
        )
        sleeps = []

        with self.assertRaises(manager.GitHubRateLimitError):
            manager.github_get(
                "/repos/acme/app",
                opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
                sleep_fn=sleeps.append,
                time_fn=lambda: 1000.0,
                max_attempts=3,
                max_retry_delay=5.0,
            )

        self.assertEqual(sleeps, [])

    def test_inspect_resolves_commit_tree_and_recovers_truncated_recursive_tree(self):
        requests = []

        def fake_get(path):
            requests.append(path)
            if path == "/repos/acme/app":
                return {
                    "default_branch": "release/stable",
                    "visibility": "public",
                    "archived": False,
                    "stargazers_count": 12,
                    "forks_count": 3,
                    "language": "Python",
                    "topics": ["agents"],
                    "license": {"spdx_id": "MIT"},
                }
            if path == "/repos/acme/app/git/ref/heads/release%2Fstable":
                return {"object": {"sha": "commit-sha"}}
            if path == "/repos/acme/app/git/commits/commit-sha":
                return {"tree": {"sha": "root-tree-sha"}}
            if path == "/repos/acme/app/git/trees/root-tree-sha?recursive=1":
                return {
                    "sha": "root-tree-sha",
                    "truncated": True,
                    "tree": [{"path": "README.md", "type": "blob"}],
                }
            if path == "/repos/acme/app/git/trees/root-tree-sha":
                return {
                    "truncated": False,
                    "tree": [
                        {"path": "README.md", "type": "blob"},
                        {"path": "src", "type": "tree", "sha": "src-tree-sha"},
                    ],
                }
            if path == "/repos/acme/app/git/trees/src-tree-sha":
                return {
                    "truncated": False,
                    "tree": [{"path": "main.py", "type": "blob"}],
                }
            if path == "/repos/acme/app/readme":
                return {
                    "content": "IyBBZ2VudHMK",
                    "encoding": "base64",
                }
            raise AssertionError(f"Unexpected GitHub request: {path}")

        with patch.object(manager, "github_get", side_effect=fake_get):
            report = manager.inspect("acme", "app")

        self.assertEqual(report["path_count"], 2)
        self.assertEqual(report["license_files"], [])
        self.assertTrue(report["tree_recovered_from_truncation"])
        self.assertFalse(report["tree_truncated"])
        self.assertIn("/repos/acme/app/git/commits/commit-sha", requests)
        self.assertIn("/repos/acme/app/git/trees/src-tree-sha", requests)
        self.assertTrue(any(item["capability"] == "agents" for item in report["capabilities"]))

    def test_missing_readme_is_optional_but_other_http_errors_are_not_hidden(self):
        metadata = {
            "default_branch": "main",
            "visibility": "public",
            "archived": False,
            "stargazers_count": 0,
            "forks_count": 0,
            "language": None,
            "topics": [],
            "license": None,
        }

        def base_get(path):
            if path == "/repos/acme/app":
                return metadata
            if path == "/repos/acme/app/git/ref/heads/main":
                return {"object": {"sha": "commit-sha"}}
            if path == "/repos/acme/app/git/commits/commit-sha":
                return {"tree": {"sha": "tree-sha"}}
            if path == "/repos/acme/app/git/trees/tree-sha?recursive=1":
                return {"truncated": False, "tree": []}
            raise AssertionError(path)

        missing = urllib.error.HTTPError(
            "https://api.github.com/repos/acme/app/readme", 404, "missing", Message(), None
        )
        with patch.object(manager, "github_get", side_effect=lambda p: (
            (_ for _ in ()).throw(missing) if p.endswith("/readme") else base_get(p)
        )):
            report = manager.inspect("acme", "app")
        self.assertEqual(report["path_count"], 0)

        forbidden = urllib.error.HTTPError(
            "https://api.github.com/repos/acme/app/readme", 403, "forbidden", Message(), None
        )
        with patch.object(manager, "github_get", side_effect=lambda p: (
            (_ for _ in ()).throw(forbidden) if p.endswith("/readme") else base_get(p)
        )):
            with self.assertRaises(urllib.error.HTTPError):
                manager.inspect("acme", "app")

    def test_inspect_rejects_a_truncated_fallback_tree_instead_of_returning_partial_data(self):
        def fake_get(path):
            if path == "/repos/acme/app":
                return {"default_branch": "main"}
            if path == "/repos/acme/app/git/ref/heads/main":
                return {"object": {"sha": "commit-sha"}}
            if path == "/repos/acme/app/git/commits/commit-sha":
                return {"tree": {"sha": "root-tree-sha"}}
            if path == "/repos/acme/app/git/trees/root-tree-sha?recursive=1":
                return {"sha": "root-tree-sha", "truncated": True, "tree": []}
            if path == "/repos/acme/app/git/trees/root-tree-sha":
                return {"truncated": True, "tree": [{"path": "partial.py", "type": "blob"}]}
            raise AssertionError(path)

        with patch.object(manager, "github_get", side_effect=fake_get):
            with self.assertRaisesRegex(RuntimeError, "truncated directory"):
                manager.inspect("acme", "app")

    def test_github_get_retries_secondary_rate_limit_403_with_retry_after(self):
        headers = Message()
        headers["Retry-After"] = "0"
        headers["X-RateLimit-Remaining"] = "100"
        rate_limit = urllib.error.HTTPError(
            "https://api.github.com/repos/acme/app",
            403,
            "secondary rate limit",
            headers,
            None,
        )
        responses = [rate_limit, FakeResponse({"ok": True})]
        sleeps = []

        def opener(_request, timeout):
            self.assertEqual(timeout, 15)
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        result = manager.github_get(
            "/repos/acme/app",
            opener=opener,
            sleep_fn=sleeps.append,
            max_attempts=2,
        )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(sleeps, [0.0])


if __name__ == "__main__":
    unittest.main()
