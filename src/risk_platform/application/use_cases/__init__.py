"""One class per use case (e.g. AssessCreditRiskUseCase,
TrainRiskModelUseCase, GenerateRiskNarrativeUseCase).

Each use case depends on injected ports, never on concrete implementations.
"""
