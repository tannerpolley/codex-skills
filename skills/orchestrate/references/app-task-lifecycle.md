# App-backed task lifecycle

Use this only when the selected delivery route creates or continues an app-backed task. Keep the originating task's opaque task ID, host or project context, and checkout ownership. A setup or client ID is not a ready task ID and must not be passed to follow-up, wait, read, title, or archive operations.

Verify readiness before sending follow-up work or archiving a source. Preserve live writers and uncommitted changes. If readiness, liveness, or identity cannot be verified, keep the source active and report the blocked operation. A missing optional close or release capability does not block independent local work.
