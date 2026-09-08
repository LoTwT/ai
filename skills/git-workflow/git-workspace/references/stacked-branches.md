# Local stacked branches

Read this for creating or restacking dependent local branches.

Establish stack base, parent relationships, branch ownership/occupancy, old tips, and replay boundaries from the request and actual topology. Branch names alone do not establish a stack. Distinguish a native platform stack from a conventional chain of PR bases.

For a linear example, if B was based on old A, first update A, then replay only B's own range with `git rebase --onto NEW_A OLD_A B`. Use actual recorded OIDs. Do not derive OLD_A from the already rewritten A. Prevent implicit updates to branches outside the explicit set.

Track each branch's before/after OIDs, old parent, replay boundary, and completion state. If B conflicts after A succeeds, resolve/continue B before touching C. Reentry must inspect the current sequencer and branch tips; it must not restart A or restore every branch to old tips by default.

After remote stack updates or merges, refresh the platform topology before local rewrites. Some platforms already retarget or rebase remaining PRs. Squash merging A changes commit identity: replay B's own commits onto the resulting base, not A's entire former history merely because ancestry no longer matches. Use recorded boundaries, merge receipts, and patch/range evidence to identify remaining work. If these cannot establish the right range, stop the rewrite.

Local restack never implicitly force-pushes, changes PR bases, or deletes merged branches. Handoff the exact changed refs to push, remaining metadata changes to PR submit, and deletions to cleanup only within the task's authorization.

Source: [Git range-diff](https://git-scm.com/docs/git-range-diff).
