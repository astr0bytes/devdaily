import tempfile
import unittest
from pathlib import Path

from devdaily.workspace import find_repos


class FindReposTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def make_repo(self, *parts, gitfile=False):
        path = self.root.joinpath(*parts)
        path.mkdir(parents=True)
        if gitfile:
            # worktrees and submodules have a .git file instead of a directory
            (path / ".git").write_text("gitdir: /somewhere/else\n")
        else:
            (path / ".git").mkdir()
        return path

    def test_finds_repos_at_several_levels(self):
        a = self.make_repo("a")
        b = self.make_repo("group", "b")
        self.assertEqual(find_repos([self.root]), [a, b])

    def test_root_is_a_repo(self):
        self.make_repo("nested")
        (self.root / ".git").mkdir()
        self.assertEqual(find_repos([self.root]), [self.root])

    def test_does_not_descend_into_repos(self):
        outer = self.make_repo("outer")
        self.make_repo("outer", "vendor", "inner")
        self.assertEqual(find_repos([self.root]), [outer])

    def test_max_depth(self):
        shallow = self.make_repo("one")
        self.make_repo("one_level", "two", "three", "deep")
        self.assertEqual(find_repos([self.root], max_depth=2), [shallow])

    def test_excluded_and_hidden_directories(self):
        kept = self.make_repo("src", "app")
        self.make_repo("node_modules", "lib")
        self.make_repo(".cache", "repo")
        self.assertEqual(find_repos([self.root], exclude={"node_modules"}), [kept])

    def test_git_file(self):
        wt = self.make_repo("worktree", gitfile=True)
        self.assertEqual(find_repos([self.root]), [wt])

    def test_missing_root_and_duplicates(self):
        a = self.make_repo("a")
        roots = [self.root, self.root / "a", self.root / "missing"]
        self.assertEqual(find_repos(roots), [a])


if __name__ == "__main__":
    unittest.main()
