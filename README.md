# Continuous benchmarking results


## How it works

- This repository has a workflow that is triggered by any other repository
  (using the `TRIGGER_BENCH_GH_TOKEN` organization secret)
- The workflow dispatch call includes a JSON payload specifying the workflow run ID
  containing the benchmark results and the name of the repository that triggered run
- The workflow then...
    - Downloads the benchmark results
    - Extracts them, and puts them into the correct folder
    - creates graphs of the changes of benchmark results over time
    - puts the graphs into a document (HTML)
    - publishes the document on github pages

## Tokens

- `TRIGGER_BENCH_GH_TOKEN`: fine-grained PAT 
    - read/write access to "Actions" on this repository
    - available to all repositories
    - used to trigger workflows on this repository
- `BENCH_GH_TOKEN`: fine-grained PAT
    - read-only access to "Actions" on all repositories
    - available to this repository only
    - used to download artifacts from other repositories
