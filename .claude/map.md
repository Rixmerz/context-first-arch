# Project Map

## What This Project Does
(analyze contracts/ for description)

## Entry Points
- (no entry points detected)

## Data Flow
[Input] → [Process] → [Output]

## File Purpose Index
| File | Purpose | Key Functions |
|------|---------|---------------|
| src/features/__init__.py | Exports: Memory, MemoryStore | (none) |
| src/features/knowledge_graph/__init__.py | Exports: ChunkType, EdgeType, CompressionLevel | (none) |
| src/features/knowledge_graph/tools/kg_build.py | Exports: kg_build | kg_build |
| src/features/knowledge_graph/tools/kg_get.py | Exports: kg_get | kg_get |
| src/features/knowledge_graph/tools/kg_retrieve.py | Exports: kg_retrieve | kg_retrieve |
| src/features/knowledge_graph/tools/__init__.py | Exports: kg_build, kg_status, kg_retrieve | (none) |
| src/features/knowledge_graph/tools/kg_history.py | Exports: kg_history | kg_history |
| src/features/knowledge_graph/tools/kg_diff.py | Exports: kg_diff | kg_diff |
| src/features/knowledge_graph/tools/kg_search.py | Exports: kg_search | kg_search |
| src/features/knowledge_graph/tools/kg_related.py | Defines: relations, details | kg_related |
| src/features/knowledge_graph/tools/kg_blame.py | Exports: kg_blame | kg_blame |
| src/features/knowledge_graph/tools/kg_expand.py | Exports: kg_expand | kg_expand |
| src/features/knowledge_graph/tools/kg_status.py | Exports: kg_status | kg_status |
| src/features/knowledge_graph/core/models.py | Defines: ChunkType, EdgeType, OmissionReason | to_dict, from_dict, get_content_at_level, to_dict, from_dict |
| src/features/knowledge_graph/core/chunker.py | Defines: CodeChunker, ContractChunker, ConfigChunker | estimate_tokens, infer_feature, chunk_project, chunk_file, chunk_directory |
| src/features/knowledge_graph/core/retriever.py | Defines: ScoredChunk, ContextRetriever, chunk | retrieve_context, retrieve, expand |
| src/features/knowledge_graph/core/__init__.py | Exports: ChunkType, EdgeType, CompressionLevel | (none) |
| src/features/knowledge_graph/core/business_rules.py | Defines: RuleStatus, RuleCategory, BusinessRule | interpret_rules_from_code, to_chunk, from_chunk, save_rule, get_rule |
| src/features/knowledge_graph/core/storage.py | Defines: ChunkStorage | save_chunk, save_chunks, get_chunk, get_chunks, get_chunks_by_type |
| src/features/knowledge_graph/core/git_chunker.py | Defines: GitChunker | estimate_tokens, is_git_repo, get_commits, get_file_history, get_blame_info |
| src/features/knowledge_graph/core/compressor.py | Exports: compress_chunk, strip_comments, extract_signature_docstring | compress_chunk, strip_comments, extract_signature_docstring, extract_signature, estimate_compressed_tokens |
| src/features/knowledge_graph/core/graph_builder.py | Defines: GraphBuilder, edges, edges | build_knowledge_graph, build_graph |
| src/features/contract/__init__.py | Exports: Contract, parse_contract, render_contract | (none) |
| src/features/contract/tools/contract_validate.py | Exports: contract_validate | contract_validate |
| src/features/contract/tools/contract_diff.py | Exports: contract_diff | contract_diff |
| src/features/contract/tools/__init__.py | Exports: contract_create, contract_validate, contract_diff | (none) |
| src/features/contract/tools/contract_create.py | Exports: contract_create | contract_create |
| src/features/contract/tools/contract_sync.py | Exports: contract_sync | contract_sync |
| src/features/contract/core/contract_parser.py | Defines: Contract, name, purpose | parse_contract, generate_contract_from_analysis, render_contract, validate_contract_vs_impl |
| src/features/contract/core/__init__.py | Exports: Contract, parse_contract, render_contract | (none) |
| src/features/analysis/__init__.py | Exports: LanguageAnalyzer, AnalyzerRegistry, FileAnalysis | (none) |
| src/features/analysis/tools/dependency_analyze.py | Exports: dependency_analyze | dependency_analyze |
| src/features/analysis/tools/impact_analyze.py | Exports: impact_analyze | impact_analyze |
| src/features/analysis/tools/__init__.py | Exports: coupling_analyze, dependency_analyze, impact_analyze | (none) |
| src/features/analysis/tools/pattern_detect.py | Exports: pattern_detect | pattern_detect |
| src/features/analysis/tools/coupling_analyze.py | Exports: coupling_analyze | coupling_analyze |
| src/features/analysis/core/coupling_analyzer.py | Defines: CouplingScore, CouplingAnalysis, feature_a | analyze_coupling |
| src/features/analysis/core/impact_analyzer.py | Defines: ImpactAnalysis, file_path, change_type | analyze_impact |
| src/features/analysis/core/dependency_analyzer.py | Defines: FileNode, DependencyGraph, path | build_dependency_graph, get_dependencies, get_dependents, detect_cycles, get_feature_dependencies |
| src/features/analysis/core/__init__.py | Exports: get_registry, LanguageAnalyzer, AnalyzerRegistry | get_registry |
| src/features/analysis/core/pattern_detector.py | Defines: PatternAnalysis, naming_patterns, import_patterns | detect_patterns |
| src/features/analysis/core/typescript_analyzer.py | Type definitions | language, extensions, analyze_file, visit, visit |
| src/features/analysis/core/python_analyzer.py | Defines: PythonAnalyzer | language, extensions, analyze_file |
| src/features/analysis/core/rust_analyzer.py | Defines: RustAnalyzer | language, extensions, analyze_file, visit, visit |
| src/features/analysis/core/base.py | Defines: FunctionInfo, ImportInfo, ClassInfo | language, extensions, can_analyze, analyze_file, get_function_info |
| src/features/memory/__init__.py | Exports: Memory, MemoryStore | (none) |
| src/features/memory/tools/memory_delete.py | Exports: memory_delete | memory_delete |
| src/features/memory/tools/__init__.py | Exports: memory_set, memory_get, memory_search | (none) |
| src/features/memory/tools/memory_search.py | Exports: memory_search | memory_search |
| src/features/memory/tools/memory_list.py | Exports: memory_list | memory_list |
| src/features/memory/tools/memory_get.py | Exports: memory_get | memory_get |
| src/features/memory/tools/memory_set.py | Exports: memory_set | memory_set |
| src/features/memory/core/memory_store.py | Defines: Memory, MemoryStore, key | set, get, search, delete, edit |
| src/features/memory/core/__init__.py | Exports: Memory, MemoryStore | (none) |
| src/features/memory/tests/__init__.py | (unknown purpose) | (none) |
| src/features/memory/tests/test_memory_store.py | Tests | temp_project, store, test_set_and_get, test_get_nonexistent, test_delete |
| src/features/workflow/__init__.py | Exports: generate_onboarding, check_onboarding_status | (none) |
| src/features/workflow/tools/__init__.py | Exports: workflow_onboard, workflow_instructions | (none) |
| src/features/workflow/tools/workflow_onboard.py | Exports: workflow_onboard | workflow_onboard |
| src/features/workflow/tools/workflow_instructions.py | Exports: workflow_instructions | workflow_instructions |
| src/features/workflow/core/onboarding.py | Exports: generate_onboarding, check_onboarding_status | generate_onboarding, check_onboarding_status |
| src/features/workflow/core/__init__.py | Exports: generate_onboarding, check_onboarding_status | (none) |
| src/features/orchestration/__init__.py | Exports: SafePoint, OrchestrationStorage, SafePointManager | (none) |
| src/features/orchestration/tools/safe_point_rollback.py | Defines: _managers | safe_point_rollback |
| src/features/orchestration/tools/safe_point_list.py | Defines: _managers | safe_point_list |
| src/features/orchestration/tools/__init__.py | Exports: safe_point_create, safe_point_rollback, safe_point_list | (none) |
| src/features/orchestration/tools/safe_point_create.py | Defines: _managers | safe_point_create |
| src/features/orchestration/core/models.py | Defines: ModelType, TaskComplexity, InstanceStatus | (none) |
| src/features/orchestration/core/safe_points.py | Defines: SafePointManager | create, rollback, list_safe_points |
| src/features/orchestration/core/__init__.py | Exports: SafePoint, OrchestrationStorage, SafePointManager | (none) |
| src/features/orchestration/core/storage.py | Defines: OrchestrationStorage | create_instance, get_instance, update_instance, list_instances, create_objective |
| src/features/rules/__init__.py | (unknown purpose) | (none) |
| src/features/rules/tools/__init__.py | Exports: rule_interpret, rule_confirm, rule_list | (none) |
| src/features/rules/tools/rule_interpret.py | Exports: rule_interpret | rule_interpret |
| src/features/rules/tools/rule_confirm.py | Exports: rule_confirm, rule_confirm_batch | rule_confirm, rule_confirm_batch |
| src/features/rules/tools/rule_list.py | Exports: rule_list | rule_list |
| src/features/rules/tools/rule_batch.py | Exports: rule_batch | rule_batch |
| src/shared/__init__.py | (unknown purpose) | (none) |
| src/shared/types/__init__.py | (unknown purpose) | (none) |
| src/shared/utils/__init__.py | (unknown purpose) | (none) |

## Current State
- ⏳ Map generated from code analysis

## Non-Obvious Things
(none documented yet)
