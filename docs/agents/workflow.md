# Workflows

## Grilling issues

`needs-grilling` marks an issue that has been evaluated and now needs a
**grill-with-docs session** (the `grilling` skill) before an agent can pick it
up. The session's job is to turn a rough issue into something buildable.

Workflow for a grilling session on an issue:

1. Run the grill against the issue with the relevant docs in context.
2. **Outcome: a detailed implementation plan.** Write the plan to the local
   `.scratch/` folder (see [`scratch.md`](scratch.md)).
3. **Record decisions on the issue.** Append any decisions reached during the
   grill to the issue body in a separate section at the end (e.g. a
   `## Decisions` heading), so they survive independently of the scratch plan.
4. **Re-label when done:** remove `needs-grilling` and add `ready-for-agent`.

    ```console
    $ gh issue edit <n> --remove-label needs-grilling --add-label ready-for-agent
    ```
