"""
Basic Example: Using the LLM Orchestrator System
Demonstrates all components working together
"""

from orchestrator.integration import OrchestratorSystem, SystemConfig
from skills.built_in.text_processing import TextProcessingSkill
from skills.built_in.data_analysis import DataAnalysisSkill
from skills.built_in.knowledge_retrieval import KnowledgeRetrievalSkill
from skills.built_in.synthesis import SynthesisSkill
from skills.skill_base import SkillInput
from skills.skill_router import SkillRouter, RoutingRule, RoutingStrategy
from loguru import logger


def setup_logging():
    """Configure logging."""
    logger.remove()  # Remove default handler
    logger.add(
        "logs/orchestrator.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )


def setup_skills() -> SkillRouter:
    """
    Set up and register all skills with the router.
    """
    
    router = SkillRouter()
    
    # Create skill instances
    text_skill = TextProcessingSkill()
    analysis_skill = DataAnalysisSkill()
    retrieval_skill = KnowledgeRetrievalSkill()
    synthesis_skill = SynthesisSkill()
    
    # Register skills
    router.register_skill(text_skill)
    router.register_skill(analysis_skill)
    router.register_skill(retrieval_skill)
    router.register_skill(synthesis_skill)
    
    # Define routing rules (OmniRoute-style)
    router.register_routing_rule(
        RoutingRule(
            source_skill=text_skill.id,
            target_skill=analysis_skill.id,
            condition="success:true",
            priority=1,
            strategy=RoutingStrategy.SEQUENTIAL,
        )
    )
    
    router.register_routing_rule(
        RoutingRule(
            source_skill=analysis_skill.id,
            target_skill=synthesis_skill.id,
            condition="success:true",
            priority=1,
            strategy=RoutingStrategy.SEQUENTIAL,
        )
    )
    
    logger.info("Skills configured: Text Processing → Analysis → Synthesis")
    
    return router


def example_1_basic_objective():
    """
    Example 1: Execute a basic objective through the hierarchy.
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Objective Execution")
    print("="*80 + "\n")
    
    # Initialize system
    config = SystemConfig(
        num_managers=2,
        workers_per_manager=2,
        enable_rag=True,
        enable_mcp=True,
        enable_work_tracking=True,
    )
    
    system = OrchestratorSystem(config)
    
    # Execute objective
    objective = "Analyze customer feedback and generate insights"
    result = system.execute_objective(objective)
    
    print(f"\nObjective Status: {result.get('status')}")
    print(f"Total Skills Executed: {result.get('total_skills_executed')}")
    print(f"Execution Time: {result.get('execution_time'):.2f}s")
    print(f"Tokens Used: {result.get('total_skills_executed')} (ZERO-TOKEN MODE)")
    print(f"\nSynthesis:\n{result.get('synthesis')}")


def example_2_skill_routing():
    """
    Example 2: Execute through intelligent skill routing.
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 2: OmniRoute-Style Skill Routing")
    print("="*80 + "\n")
    
    # Initialize system
    system = OrchestratorSystem(SystemConfig(enable_rag=False))
    
    # Set up skills
    router = setup_skills()
    system.skill_router = router
    
    # Execute through skill path
    text_skill_id = [s.id for s in router.skills.values() if s.name == "Text Processing"][0]
    
    input_data = {
        "text": "The LLM Orchestrator is a hierarchical system. It has Commanders, Managers, and Workers.",
        "action": "extract"
    }
    
    result = system.execute_with_skills(text_skill_id, input_data)
    
    print(f"\nExecution Steps: {result.get('execution_steps')}")
    print(f"Skills Executed: {result.get('skills_executed')}")
    print(f"Execution Time: {result.get('execution_time_ms'):.2f}ms")
    print(f"Tokens Used: 0 (ZERO-TOKEN MODE)")


def example_3_knowledge_base():
    """
    Example 3: Use the knowledge graph as your second brain.
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Knowledge Graph (Second Brain)")
    print("="*80 + "\n")
    
    # Initialize system with RAG
    system = OrchestratorSystem(SystemConfig(enable_rag=True))
    
    # Add knowledge
    print("Adding knowledge to your second brain...")
    system.add_knowledge(
        title="LLM Orchestrator Architecture",
        content="""The LLM Orchestrator uses a three-tier hierarchy:
        - Commander: Strategic planning and decomposition
        - Managers: Tactical coordination and allocation
        - Workers: Skill execution with zero-token overhead
        
        The system integrates Skills, RAG, MCP, and Work Tracking.
        """,
        source="system_documentation"
    )
    
    system.add_knowledge(
        title="Skill System",
        content="""Skills are reusable work units that execute without LLM API calls.
        Supported skill types: Text Processing, Data Analysis, Knowledge Retrieval, Synthesis.
        Skills can be chained together using OmniRoute-style intelligent routing.
        """,
        source="system_documentation"
    )
    
    # Query knowledge
    print("\nQuerying the knowledge graph...")
    query_result = system.query_knowledge("What is the architecture of the orchestrator?")
    
    print(f"\nQuery: {query_result.get('query')}")
    print(f"Matched Nodes: {query_result.get('matched_nodes')}")
    print(f"Results Found: {len(query_result.get('top_results', []))}")
    
    for idx, result in enumerate(query_result.get('top_results', [])[:3], 1):
        print(f"  [{idx}] {result.get('label')} (Score: {result.get('score'):.2f})")


def example_4_system_status():
    """
    Example 4: Check complete system status.
    """
    
    print("\n" + "="*80)
    print("EXAMPLE 4: System Status and Statistics")
    print("="*80 + "\n")
    
    # Initialize system
    system = OrchestratorSystem(SystemConfig())
    
    # Get status
    status = system.get_system_status()
    
    print(f"System ID: {status['system_id']}")
    print(f"Mode: {status['mode']}")
    print(f"\nCommander Status:")
    print(f"  Active Objectives: {status['commander'].get('active_objectives')}")
    print(f"  Completed Executions: {status['commander'].get('completed_executions')}")
    print(f"  Managers: {len(status['commander'].get('managers', []))}")
    print(f"  Total Workers: {status['commander'].get('workers_count', 0)}")
    
    if status.get('knowledge_graph'):
        print(f"\nKnowledge Graph:")
        print(f"  Documents: {status['knowledge_graph'].get('total_documents')}")
        print(f"  Nodes: {status['knowledge_graph'].get('total_nodes')}")
        print(f"  Edges: {status['knowledge_graph'].get('total_edges')}")
        print(f"  Tokens Used: {status['knowledge_graph'].get('tokens_used')} (ZERO-TOKEN)")
    
    print(f"\nWork Tracking:")
    print(f"  Total Works: {status['work_tracking'].get('total_works')}")
    print(f"  Total Versions: {status['work_tracking'].get('total_versions')}")
    print(f"  Total Tokens Used: {status['work_tracking'].get('total_tokens_used')} (UNLIMITED)")


def main():
    """
    Run all examples.
    """
    
    setup_logging()
    
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════════╗")
    print("║        LLM Orchestrator: Three-Tier Hierarchical System Examples              ║")
    print("║                                                                                ║")
    print("║  Features:                                                                     ║")
    print("║  • Zero-Token Execution (No LLM API calls)                                    ║")
    print("║  • Unlimited Credits Mode                                                     ║")
    print("║  • OmniRoute-Style Skill Routing                                              ║")
    print("║  • Graph-Based RAG (Second Brain)                                             ║")
    print("║  • Work Versioning & Tracking                                                 ║")
    print("║  • MCP Integration                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════════╝\n")
    
    # Run examples
    example_1_basic_objective()
    example_2_skill_routing()
    example_3_knowledge_base()
    example_4_system_status()
    
    print("\n" + "="*80)
    print("All examples completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
