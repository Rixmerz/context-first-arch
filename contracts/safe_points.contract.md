# SafePoints Contract

## Purpose
(Generated from /Users/juanpablodiaz/my_projects/ASOA/context-first-arch/src/features/orchestration/core/safe_points.py)

## Public Interface
```python
def create(self, project_path: str, task_summary: str, files_changed: Optional[List[str]], prefix: str, include_untracked: bool, dry_run: bool) -> Dict[str, Any]
def rollback(self, project_path: str, safe_point_id: Optional[str], commit_hash: Optional[str], mode: str) -> Dict[str, Any]
def list_safe_points(self, project_path: Optional[str], limit: int) -> Dict[str, Any]
```

## Errors This Can Throw
- (none defined)

## Dependencies
- `typing` - (imported)
- `datetime` - (imported)
- `pathlib` - (imported)
- `subprocess` - (imported)
- `uuid` - (imported)
- `models` - (imported)
- `storage` - (imported)
- `pathlib` - (imported)
- `src.features.memory` - (imported)

## Side Effects
- (none - pure functions)

## Example Usage
```python
// TODO: Add usage example
```
