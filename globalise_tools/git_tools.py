import subprocess


def there_are_uncommitted_changes() -> bool:
    git_status = subprocess.check_output(['git', 'status', '--short']).decode('ascii').strip()
    git_committable_changes = [line for line in git_status.split('\n') if not line.startswith('?? ')]
    return len(git_committable_changes) > 0


def read_current_commit_id():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
