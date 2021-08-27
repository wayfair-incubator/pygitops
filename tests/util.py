from dataclasses import dataclass
from pathlib import Path

from git import Actor, Repo

SOME_COMMIT_MESSAGE = "some-commit-message"
SOME_ACTOR = Actor("some-user", "some-user@wayfair.com")
SOME_CONTENT = "some-content"


@dataclass
class Repos:
    local_repo: Repo
    remote_repo: Repo


def _get_local_remote_repos(base_path: Path) -> Repos:
    remote_repo_path = base_path / "some-remote-repo"
    local_repo_path = base_path / "some-local-repo"
    remote_repo = Repo.init(remote_repo_path)

    # remote repo must have initial content in order to be cloned
    new_file_path = remote_repo_path / "foo.txt"
    new_file_path.write_text("some changes")
    remote_repo.index.add([str(new_file_path)])
    remote_repo.index.commit(
        SOME_COMMIT_MESSAGE, author=SOME_ACTOR, committer=SOME_ACTOR
    )

    local_repo = Repo.clone_from(remote_repo.working_dir, local_repo_path)
    return Repos(local_repo=local_repo, remote_repo=remote_repo)


def _get_diff(repo: Repo) -> str:
    index = repo.index
    workdir_path = Path(repo.working_dir)

    untracked_file_paths = [Path(f) for f in repo.untracked_files]
    items_to_stage = untracked_file_paths + [Path(f.a_path) for f in index.diff(None)]

    for item in items_to_stage:
        full_path = workdir_path / item
        index.add(str(item)) if full_path.exists() else index.remove(str(item), r=True)

    return repo.git.diff("--cached")


def _some_source_modifier(repo: Repo, filename: str) -> None:
    # Add new file
    test_file_path = Path(repo.working_dir) / filename
    test_file_path.touch()
    # Modify file
    test_file_path = Path(repo.working_dir) / filename
    test_file_path.write_text(SOME_CONTENT)
