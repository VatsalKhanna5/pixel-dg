# Documentation Hub

This documentation set is structured to support three audiences: researchers evaluating methodological relevance, engineers operating the simulation pipeline, and downstream users consuming the generated datasets.

## Recommended Reading Order

1. [`../README.md`](/home/dr-robin-kalyan/Desktop/pixel/README.md): repository-level overview and verification highlights.
2. [`research_relevance.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/research_relevance.md): motivation, intended use, and research positioning.
3. [`architecture/system_overview.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/architecture/system_overview.md): layout conventions, port model, and workflow stages.
4. [`architecture/physics_engine.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/architecture/physics_engine.md): physical domain, meshing, and solver design.
5. [`architecture/data_pipeline.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/architecture/data_pipeline.md): reduction, augmentation, and storage flow.
6. [`dataset_specification.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/dataset_specification.md): formal description of stored arrays and metadata semantics.
7. [`verification_and_evaluation.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/verification_and_evaluation.md): baseline validation, EDA figures, and quality checks.
8. [`operations.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/operations.md): execution patterns, outputs, and operational procedures.
9. [`environment.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/environment.md): environment and dependency setup.

## Documentation Map

- [`research_relevance.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/research_relevance.md): explains why pixelated EM data generation matters for RF design automation and surrogate-model development.
- [`architecture/system_overview.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/architecture/system_overview.md): explains what each pipeline component does and how data moves through the system.
- [`architecture/physics_engine.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/architecture/physics_engine.md): explains how the openEMS problem is parameterized and why the meshing and padding decisions matter.
- [`architecture/data_pipeline.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/architecture/data_pipeline.md): explains how solver outputs become learning-ready arrays.
- [`dataset_specification.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/dataset_specification.md): explains the HDF5 schema and how to interpret each tensor.
- [`verification_and_evaluation.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/verification_and_evaluation.md): explains the available evidence artifacts and how to read them.
- [`operations.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/operations.md): explains the supported scripts and their expected outputs.
- [`environment.md`](/home/dr-robin-kalyan/Desktop/pixel/docs/environment.md): explains required local tooling and validation commands.

## Source Of Truth

The governing project constraints remain in [`AGENT_CONTEXT.md`](/home/dr-robin-kalyan/Desktop/pixel/AGENT_CONTEXT.md). This documentation complements that file by translating the constraints into a repository-facing technical narrative.
