# Continuous benchmarking results


## How it works

- This repository has a workflow that is triggered by any other repository
  (using the `TRIGGER_BENCH_GH_TOKEN` organization secret)
- The workflow dispatch call includes a JSON payload specifying the artifact ID
  containing the benchmark results and the name of the repository that triggered run

## Tokens

- `TRIGGER_BENCH_GH_TOKEN`: fine-grained PAT 
    - read/write access to "Actions" on this repository
    - available to all repositories
    - used to trigger workflows on this repository
- `BENCH_GH_TOKEN`: fine-grained PAT
    - read-only access to "Actions" on all repositories
    - available to this repository only
    - used to download artifacts from other repositories
