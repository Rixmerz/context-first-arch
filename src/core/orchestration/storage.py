"""
SQLite storage for Nova Agent Orchestration System.

Provides persistent storage for agent instances, objectives, loops, and safe points.
Database: {project_path}/.claude/orchestration.db
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from datetime import datetime

from src.core.orchestration.models import (
    AgentInstance, Objective, ExecutionLoop, SafePoint, Checkpoint,
    InstanceStatus, ObjectiveStatus, LoopStatus, ModelType
)


class OrchestrationStorage:
    """SQLite persistence for Nova orchestration state."""
    
    def __init__(self, project_path: Path):
        """
        Initialize orchestration storage.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = project_path
        self.db_path = project_path / ".claude" / "orchestration.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        # Ensure .claude directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # === AGENT INSTANCES TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_instances (
                    id TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    task TEXT NOT NULL,
                    context TEXT,
                    status TEXT NOT NULL,
                    spawned_at TEXT NOT NULL,
                    completed_at TEXT,
                    timeout_ms INTEGER DEFAULT 120000,
                    max_tokens INTEGER DEFAULT 8000,
                    tags TEXT,
                    project_path TEXT,
                    result TEXT,
                    error TEXT,
                    tokens_used INTEGER DEFAULT 0
                )
            """)
            
            # === OBJECTIVES TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objectives (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    success_criteria TEXT,
                    checkpoints TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_iteration INTEGER DEFAULT 0,
                    max_iterations INTEGER DEFAULT 10,
                    progress REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    failed_at TEXT,
                    failure_reason TEXT,
                    project_path TEXT,
                    tags TEXT,
                    history TEXT
                )
            """)
            
            # === EXECUTION LOOPS TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_loops (
                    id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    max_iterations INTEGER DEFAULT 10,
                    iteration_delay_ms INTEGER DEFAULT 1000,
                    enable_safe_points INTEGER DEFAULT 1,
                    escalation_threshold INTEGER DEFAULT 5,
                    status TEXT NOT NULL,
                    current_iteration INTEGER DEFAULT 0,
                    objective_id TEXT,
                    project_path TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    completion_reason TEXT,
                    history TEXT,
                    FOREIGN KEY (objective_id) REFERENCES objectives(id)
                )
            """)
            
            # === SAFE POINTS TABLE ===
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS safe_points (
                    id TEXT PRIMARY KEY,
                    commit_hash TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    files_changed INTEGER DEFAULT 0,
                    project_path TEXT NOT NULL
                )
            """)
            
            # === ACTIVE STATE TABLE ===
            # Stores singleton state like active_objective_id
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # === INDEXES ===
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_instances_status 
                ON agent_instances(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_instances_model 
                ON agent_instances(model)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_objectives_status 
                ON objectives(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_loops_status 
                ON execution_loops(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_safe_points_project 
                ON safe_points(project_path, timestamp DESC)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            yield conn
        finally:
            conn.close()
    
    # === AGENT INSTANCE METHODS ===
    
    def create_instance(self, instance: AgentInstance) -> None:
        """Store a new agent instance."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_instances 
                (id, model, task, context, status, spawned_at, timeout_ms, 
                 max_tokens, tags, project_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instance.id,
                instance.model.value,
                instance.task,
                instance.context,
                instance.status.value,
                instance.spawned_at.isoformat(),
                instance.timeout_ms,
                instance.max_tokens,
                json.dumps(instance.tags),
                instance.project_path
            ))
            conn.commit()
    
    def get_instance(self, instance_id: str) -> Optional[AgentInstance]:
        """Retrieve instance by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, model, task, context, status, spawned_at, completed_at,
                       timeout_ms, max_tokens, tags, project_path, result, error, tokens_used
                FROM agent_instances
                WHERE id = ?
            """, (instance_id,))
            row = cursor.fetchone()
            
            if row:
                return AgentInstance(
                    id=row[0],
                    model=ModelType(row[1]),
                    task=row[2],
                    context=row[3],
                    status=InstanceStatus(row[4]),
                    spawned_at=datetime.fromisoformat(row[5]),
                    completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    timeout_ms=row[7],
                    max_tokens=row[8],
                    tags=json.loads(row[9]) if row[9] else [],
                    project_path=row[10],
                    result=row[11],
                    error=row[12],
                    tokens_used=row[13]
                )
            return None
    
    def update_instance(self, instance_id: str, updates: Dict[str, Any]) -> bool:
        """Update instance fields."""
        if not updates:
            return False
        
        # Build SET clause dynamically
        set_parts = []
        values = []
        for key, value in updates.items():
            set_parts.append(f"{key} = ?")
            # Handle enums and datetimes
            if hasattr(value, 'value'):
                value = value.value
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, (list, dict)):
                value = json.dumps(value)
            values.append(value)
        
        values.append(instance_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE agent_instances
                SET {', '.join(set_parts)}
                WHERE id = ?
            """, values)
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
    
    def list_instances(
        self, 
        status: Optional[InstanceStatus] = None,
        model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[AgentInstance]:
        """List instances with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            query = """
                SELECT id, model, task, context, status, spawned_at, completed_at,
                       timeout_ms, max_tokens, tags, project_path, result, error, tokens_used
                FROM agent_instances
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            if model:
                query += " AND model = ?"
                params.append(model)
            
            if tags:
                for tag in tags:
                    query += " AND tags LIKE ?"
                    params.append(f'%"{tag}"%')
            
            query += " ORDER BY spawned_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            instances = []
            for row in rows:
                instances.append(AgentInstance(
                    id=row[0],
                    model=ModelType(row[1]),
                    task=row[2],
                    context=row[3],
                    status=InstanceStatus(row[4]),
                    spawned_at=datetime.fromisoformat(row[5]),
                    completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    timeout_ms=row[7],
                    max_tokens=row[8],
                    tags=json.loads(row[9]) if row[9] else [],
                    project_path=row[10],
                    result=row[11],
                    error=row[12],
                    tokens_used=row[13]
                ))
            
            return instances
    
    # === OBJECTIVE METHODS ===
    
    def create_objective(self, objective: Objective) -> None:
        """Store a new objective."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Serialize checkpoints
            checkpoints_json = json.dumps([{
                'id': cp.id,
                'description': cp.description,
                'achieved': cp.achieved,
                'achieved_at': cp.achieved_at.isoformat() if cp.achieved_at else None,
                'notes': cp.notes
            } for cp in objective.checkpoints])
            
            cursor.execute("""
                INSERT INTO objectives 
                (id, description, success_criteria, checkpoints, status, 
                 current_iteration, max_iterations, progress, created_at, 
                 project_path, tags, history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                objective.id,
                objective.description,
                json.dumps(objective.success_criteria),
                checkpoints_json,
                objective.status.value,
                objective.current_iteration,
                objective.max_iterations,
                objective.progress,
                objective.created_at.isoformat(),
                objective.project_path,
                json.dumps(objective.tags),
                json.dumps(objective.history)
            ))
            conn.commit()
    
    def get_objective(self, objective_id: str) -> Optional[Objective]:
        """Retrieve objective by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, success_criteria, checkpoints, status,
                       current_iteration, max_iterations, progress, created_at,
                       completed_at, failed_at, failure_reason, project_path, tags, history
                FROM objectives
                WHERE id = ?
            """, (objective_id,))
            row = cursor.fetchone()
            
            if row:
                # Deserialize checkpoints
                checkpoints_data = json.loads(row[3])
                checkpoints = [Checkpoint(
                    id=cp['id'],
                    description=cp['description'],
                    achieved=cp['achieved'],
                    achieved_at=datetime.fromisoformat(cp['achieved_at']) if cp['achieved_at'] else None,
                    notes=cp['notes']
                ) for cp in checkpoints_data]
                
                return Objective(
                    id=row[0],
                    description=row[1],
                    success_criteria=json.loads(row[2]),
                    checkpoints=checkpoints,
                    status=ObjectiveStatus(row[4]),
                    current_iteration=row[5],
                    max_iterations=row[6],
                    progress=row[7],
                    created_at=datetime.fromisoformat(row[8]),
                    completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
                    failed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                    failure_reason=row[11],
                    project_path=row[12],
                    tags=json.loads(row[13]) if row[13] else [],
                    history=json.loads(row[14]) if row[14] else []
                )
            return None
    
    def update_objective(self, objective_id: str, updates: Dict[str, Any]) -> bool:
        """Update objective fields."""
        if not updates:
            return False
        
        # Handle checkpoints serialization
        if 'checkpoints' in updates:
            checkpoints = updates['checkpoints']
            updates['checkpoints'] = json.dumps([{
                'id': cp.id,
                'description': cp.description,
                'achieved': cp.achieved,
                'achieved_at': cp.achieved_at.isoformat() if cp.achieved_at else None,
                'notes': cp.notes
            } for cp in checkpoints])
        
        # Build SET clause
        set_parts = []
        values = []
        for key, value in updates.items():
            set_parts.append(f"{key} = ?")
            if hasattr(value, 'value'):
                value = value.value
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, (list, dict)) and not isinstance(value, str):
                value = json.dumps(value)
            values.append(value)
        
        values.append(objective_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE objectives
                SET {', '.join(set_parts)}
                WHERE id = ?
            """, values)
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
    
    def get_active_objective_id(self) -> Optional[str]:
        """Get current active objective ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM active_state WHERE key = 'active_objective_id'
            """)
            row = cursor.fetchone()
            return row[0] if row and row[0] else None
    
    def set_active_objective_id(self, objective_id: Optional[str]) -> None:
        """Set active objective ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO active_state (key, value, updated_at)
                VALUES ('active_objective_id', ?, ?)
            """, (objective_id or "", datetime.now().isoformat()))
            conn.commit()
    
    # === LOOP METHODS ===
    
    def create_loop(self, loop: ExecutionLoop) -> None:
        """Store a new execution loop."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execution_loops
                (id, task, condition_type, max_iterations, iteration_delay_ms,
                 enable_safe_points, escalation_threshold, status, current_iteration,
                 objective_id, project_path, created_at, history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loop.id,
                loop.task,
                loop.condition_type,
                loop.max_iterations,
                loop.iteration_delay_ms,
                1 if loop.enable_safe_points else 0,
                loop.escalation_threshold,
                loop.status.value,
                loop.current_iteration,
                loop.objective_id,
                loop.project_path,
                loop.created_at.isoformat(),
                json.dumps(loop.history)
            ))
            conn.commit()
    
    def get_loop(self, loop_id: str) -> Optional[ExecutionLoop]:
        """Retrieve loop by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, task, condition_type, max_iterations, iteration_delay_ms,
                       enable_safe_points, escalation_threshold, status, current_iteration,
                       objective_id, project_path, created_at, completed_at, completion_reason, history
                FROM execution_loops
                WHERE id = ?
            """, (loop_id,))
            row = cursor.fetchone()
            
            if row:
                return ExecutionLoop(
                    id=row[0],
                    task=row[1],
                    condition_type=row[2],
                    max_iterations=row[3],
                    iteration_delay_ms=row[4],
                    enable_safe_points=bool(row[5]),
                    escalation_threshold=row[6],
                    status=LoopStatus(row[7]),
                    current_iteration=row[8],
                    objective_id=row[9],
                    project_path=row[10],
                    created_at=datetime.fromisoformat(row[11]),
                    completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
                    completion_reason=row[13],
                    history=json.loads(row[14]) if row[14] else []
                )
            return None
    
    def update_loop(self, loop_id: str, updates: Dict[str, Any]) -> bool:
        """Update loop fields."""
        if not updates:
            return False
        
        set_parts = []
        values = []
        for key, value in updates.items():
            set_parts.append(f"{key} = ?")
            if hasattr(value, 'value'):
                value = value.value
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, bool):
                value = 1 if value else 0
            elif isinstance(value, (list, dict)):
                value = json.dumps(value)
            values.append(value)
        
        values.append(loop_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE execution_loops
                SET {', '.join(set_parts)}
                WHERE id = ?
            """, values)
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
    
    # === SAFE POINT METHODS ===
    
    def create_safe_point(self, safe_point: SafePoint) -> None:
        """Store a new safe point."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO safe_points
                (id, commit_hash, message, timestamp, files_changed, project_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                safe_point.id,
                safe_point.commit_hash,
                safe_point.message,
                safe_point.timestamp.isoformat(),
                safe_point.files_changed,
                safe_point.project_path
            ))
            conn.commit()
    
    def get_safe_point(self, safe_point_id: str) -> Optional[SafePoint]:
        """Retrieve safe point by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, commit_hash, message, timestamp, files_changed, project_path
                FROM safe_points
                WHERE id = ?
            """, (safe_point_id,))
            row = cursor.fetchone()
            
            if row:
                return SafePoint(
                    id=row[0],
                    commit_hash=row[1],
                    message=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    files_changed=row[4],
                    project_path=row[5]
                )
            return None
    
    def list_safe_points(
        self,
        project_path: Optional[str] = None,
        limit: int = 10
    ) -> List[SafePoint]:
        """List recent safe points."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if project_path:
                cursor.execute("""
                    SELECT id, commit_hash, message, timestamp, files_changed, project_path
                    FROM safe_points
                    WHERE project_path = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (project_path, limit))
            else:
                cursor.execute("""
                    SELECT id, commit_hash, message, timestamp, files_changed, project_path
                    FROM safe_points
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            
            safe_points = []
            for row in rows:
                safe_points.append(SafePoint(
                    id=row[0],
                    commit_hash=row[1],
                    message=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    files_changed=row[4],
                    project_path=row[5]
                ))
            
            return safe_points
