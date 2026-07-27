# Comparative GitHub Review

This implementation borrows design lessons, not source code.

## Generative Agents

The Stanford Generative Agents work demonstrates the value of observation, memory retrieval, reflection, planning, and a persistent simulated environment. This fork keeps memory and reflection but replaces LLM-authored cognition with bounded deterministic state so the subject can run offline on modest hardware.

## Concordia

Concordia separates acting entities from an environment or Game Master that resolves outcomes. This fork follows the same essential authority boundary: the organism proposes conduct, while the host supplies objective consequences.

## MIMo

MIMo emphasizes that embodiment includes multiple sensory channels such as vision, touch, proprioception, and vestibular input. This fork begins with a lightweight scalar sensorium that can later accept richer adapters without binding the organism to a 3D body.

## Neuroca and cognitive-memory projects

Modern memory projects emphasize maintenance, forgetting, associations, and consolidation. The organism retains bounded decay, associative retrieval, protected narrative memories, and evidence-linked self-narrative while avoiding mandatory vector databases.

## Artificial-life and homeostasis projects

Artificial-life simulations demonstrate how simple energy budgets and continuous regulation can generate persistent behavior. This fork uses homeostatic imbalance as the source of autonomous activity instead of waiting for language prompts.

## Missing element addressed here

Most agent repositories answer: "What should the agent do or say?"

This fork first asks: "What is continuously happening to this same subject?"
