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

## Enrolling a new repository to the benchmark collection

1) Create a repository on the JSC GitLab, note down the project ID in the
   general settings, allow force pushes etc. as documented in github2lab
2) Copy the continuous benchmarking (`cb.yml`) workflow and `.gitlab-ci.yml` from the
   `cb-testing` repo to the GitHub repo you want to enroll
3) Change the project ID in the `cb.yml` workflow
4) Update the `.gitlab-ci.yml` file to install dependencies and run the benchmarks,
   as it fits the concrete project; possibly change branch names etc.
5) In the GitHub repository, add a `benchmark` label, that is used to control triggering
   benchmarks for pull requests
