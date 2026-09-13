import unittest

from llm_providers.provider_base import LLMProvider, LLMRequest
from scripts.setup import setup_llm_providers


class LocalRoutingTests(unittest.TestCase):
    def test_default_configuration_registers_only_local_provider(self):
        router = setup_llm_providers()

        self.assertEqual(set(router.providers), {LLMProvider.LOCAL})

        decision = router.decide(
            LLMRequest(prompt="Explain local routing", task_type="general"),
            use_skills=False,
        )

        self.assertTrue(decision.use_llm)
        self.assertEqual(decision.provider, LLMProvider.LOCAL)
        self.assertEqual(decision.fallback_providers, [])
        self.assertEqual(decision.estimated_cost, 0.0)
        self.assertLessEqual(decision.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()
