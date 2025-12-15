# Current Task

## Goal
Migrar Nova a arquitectura CFA: extraer business logic a src/core/orchestration/, crear 15 tools individuales, implementar SQLite persistence

## Status
IN_PROGRESS

## What's Done
(none)

## Files Modified This Session
(none)

## Blockers
None

## Next Steps
1. Crear src/core/orchestration/models.py con 8 dataclasses + 5 enums
2. Crear src/core/orchestration/storage.py con SQLite y 5 tablas
3. Implementar 6 managers en core (router, executor, objective, loop, safe_points)
4. Refactorizar 5 tools existentes a thin wrappers
5. Crear 10 nuevas tools individuales
6. Actualizar integración en __init__.py y server.py
7. Eliminar loop_until.py y prehook_commit.py
8. Crear documentación

## Context for Next Session
Nova actualmente tiene 7 archivos de tools MCP (~1,858 líneas) con lógica de negocio embebida y estado en memoria. Necesitamos seguir el patrón CFA: Tool Layer (thin wrappers) → Core Layer (business logic) → Storage Layer (SQLite). Patrón 1:1 archivo-función como memory_*, symbol_*, file_*, kg_*.
