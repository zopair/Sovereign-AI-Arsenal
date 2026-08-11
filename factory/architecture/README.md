# Factory Architecture

## Production principle
The factory must maximize successful project completion, not maximize dependency on any single provider.

### Layers
1. Intake / Planning
2. Capability and Skill Registry
3. Agent Registry / Router
4. Execution Broker
5. Replaceable Workers (VM, container, GPU, GitHub adapter)
6. Recovery / Self-healing
7. Evidence / Evaluation / Artifacts
8. Factory Knowledge

### Non-negotiable rules
- Agents decide; workers execute.
- GitHub Actions is optional infrastructure.
- A worker failure triggers rescheduling when possible.
- A provider failure triggers provider switching when possible.
- Every stage produces evidence.
- Recovery is bounded by attempts, time, and cost.
- Do not declare success without a verified artifact.
