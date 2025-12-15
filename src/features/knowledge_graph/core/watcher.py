"""
File Watcher for Knowledge Graph Auto-Updates.

Watches for file changes and triggers incremental Knowledge Graph updates.
Uses watchdog for cross-platform file system monitoring.
"""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Skip patterns for files/directories that shouldn't trigger updates
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".tox", ".pytest_cache", ".mypy_cache", "dist", "build",
    ".next", ".nuxt", "coverage", ".coverage", ".claude",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".rar",
    ".mp3", ".mp4", ".avi", ".mov",
    ".db", ".sqlite", ".sqlite3",
}

SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go",
    ".java", ".kt", ".swift", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".cs", ".md", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg",
}


class KGWatcher:
    """
    File watcher that triggers Knowledge Graph updates on file changes.

    Features:
    - Debounced updates to avoid excessive rebuilds
    - Filters out non-source files
    - Supports start/stop control
    - Async callback support
    """

    def __init__(
        self,
        project_path: Path,
        on_changes: Optional[Callable[[List[str]], Any]] = None,
        debounce_ms: int = 1000,
        auto_build: bool = True
    ):
        """
        Initialize the file watcher.

        Args:
            project_path: Root path of the project to watch
            on_changes: Callback function called with list of changed files
            debounce_ms: Milliseconds to wait before triggering update
            auto_build: If True, automatically trigger KG build on changes
        """
        self.project_path = Path(project_path).resolve()
        self.on_changes = on_changes
        self.debounce_ms = debounce_ms
        self.auto_build = auto_build

        self._pending_changes: Set[str] = set()
        self._debounce_timer: Optional[threading.Timer] = None
        self._observer = None
        self._running = False
        self._lock = threading.Lock()

        # Stats
        self._stats = {
            "started_at": None,
            "changes_detected": 0,
            "builds_triggered": 0,
            "last_build_at": None,
        }

    def _should_watch(self, path: str) -> bool:
        """Check if a file should be watched."""
        p = Path(path)

        # Skip directories
        if any(skip in p.parts for skip in SKIP_DIRS):
            return False

        # Skip non-source extensions
        if p.suffix.lower() not in SOURCE_EXTENSIONS:
            return False

        # Skip hidden files (except config files)
        if p.name.startswith(".") and not p.name.startswith(".env"):
            return False

        return True

    def _on_file_event(self, path: str, event_type: str):
        """Handle file system event."""
        if not self._should_watch(path):
            return

        try:
            rel_path = str(Path(path).relative_to(self.project_path))
        except ValueError:
            return

        with self._lock:
            self._pending_changes.add(rel_path)
            self._stats["changes_detected"] += 1

            # Cancel existing timer
            if self._debounce_timer:
                self._debounce_timer.cancel()

            # Start new debounce timer
            self._debounce_timer = threading.Timer(
                self.debounce_ms / 1000.0,
                self._process_changes
            )
            self._debounce_timer.start()

    def _process_changes(self):
        """Process accumulated changes after debounce period."""
        with self._lock:
            if not self._pending_changes:
                return

            changes = list(self._pending_changes)
            self._pending_changes.clear()

        logger.info(f"Processing {len(changes)} file changes")
        self._stats["builds_triggered"] += 1
        self._stats["last_build_at"] = time.time()

        # Call callback if provided
        if self.on_changes:
            try:
                result = self.on_changes(changes)
                # Handle coroutines
                if asyncio.iscoroutine(result):
                    asyncio.run(result)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")

        # Auto-build if enabled
        if self.auto_build:
            self._trigger_incremental_build(changes)

    def _trigger_incremental_build(self, changed_files: List[str]):
        """Trigger incremental Knowledge Graph build."""
        try:
            from .graph_builder import GraphBuilder
            from .storage import ChunkStorage

            storage = ChunkStorage(self.project_path)
            builder = GraphBuilder(self.project_path, storage)

            stats = builder.build_graph(
                incremental=True,
                changed_files=changed_files
            )
            logger.info(f"Incremental build complete: {stats}")
        except Exception as e:
            logger.error(f"Failed to trigger incremental build: {e}")

    def start(self) -> bool:
        """
        Start watching for file changes.

        Returns:
            True if started successfully, False if watchdog not available
        """
        if self._running:
            return True

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
        except ImportError:
            logger.warning("watchdog not installed. Install with: pip install watchdog")
            return False

        class Handler(FileSystemEventHandler):
            def __init__(handler_self, watcher):
                handler_self.watcher = watcher

            def on_modified(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._on_file_event(event.src_path, "modified")

            def on_created(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._on_file_event(event.src_path, "created")

            def on_deleted(handler_self, event):
                if not event.is_directory:
                    handler_self.watcher._on_file_event(event.src_path, "deleted")

        self._observer = Observer()
        self._observer.schedule(
            Handler(self),
            str(self.project_path),
            recursive=True
        )
        self._observer.start()
        self._running = True
        self._stats["started_at"] = time.time()

        logger.info(f"Started watching: {self.project_path}")
        return True

    def stop(self):
        """Stop watching for file changes."""
        if not self._running:
            return

        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        self._running = False
        logger.info("Stopped watching")

    def is_running(self) -> bool:
        """Check if the watcher is currently running."""
        return self._running

    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics."""
        stats = self._stats.copy()
        stats["is_running"] = self._running
        stats["pending_changes"] = len(self._pending_changes)
        stats["project_path"] = str(self.project_path)
        stats["debounce_ms"] = self.debounce_ms
        stats["auto_build"] = self.auto_build

        if stats["started_at"]:
            stats["uptime_seconds"] = int(time.time() - stats["started_at"])

        return stats

    def trigger_full_build(self) -> Dict[str, Any]:
        """Manually trigger a full Knowledge Graph rebuild."""
        try:
            from .graph_builder import GraphBuilder
            from .storage import ChunkStorage

            storage = ChunkStorage(self.project_path)
            builder = GraphBuilder(self.project_path, storage)

            stats = builder.build_graph(incremental=False)
            self._stats["builds_triggered"] += 1
            self._stats["last_build_at"] = time.time()

            return {"success": True, **stats}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global watcher instance (for MCP tool access)
_global_watcher: Optional[KGWatcher] = None


def get_watcher(project_path: Optional[Path] = None) -> Optional[KGWatcher]:
    """Get or create the global watcher instance."""
    global _global_watcher

    if _global_watcher is None and project_path:
        _global_watcher = KGWatcher(project_path)

    return _global_watcher


def start_watcher(
    project_path: Path,
    debounce_ms: int = 1000,
    auto_build: bool = True
) -> Dict[str, Any]:
    """Start the global file watcher."""
    global _global_watcher

    if _global_watcher and _global_watcher.is_running():
        return {
            "success": False,
            "error": "Watcher already running",
            "stats": _global_watcher.get_stats()
        }

    _global_watcher = KGWatcher(
        project_path=project_path,
        debounce_ms=debounce_ms,
        auto_build=auto_build
    )

    if _global_watcher.start():
        return {
            "success": True,
            "message": f"Watcher started for {project_path}",
            "stats": _global_watcher.get_stats()
        }
    else:
        return {
            "success": False,
            "error": "Failed to start watcher. Is watchdog installed?"
        }


def stop_watcher() -> Dict[str, Any]:
    """Stop the global file watcher."""
    global _global_watcher

    if not _global_watcher or not _global_watcher.is_running():
        return {
            "success": False,
            "error": "Watcher not running"
        }

    stats = _global_watcher.get_stats()
    _global_watcher.stop()

    return {
        "success": True,
        "message": "Watcher stopped",
        "final_stats": stats
    }


def get_watcher_status() -> Dict[str, Any]:
    """Get the current watcher status."""
    global _global_watcher

    if not _global_watcher:
        return {
            "running": False,
            "message": "No watcher configured"
        }

    return {
        "running": _global_watcher.is_running(),
        "stats": _global_watcher.get_stats()
    }
