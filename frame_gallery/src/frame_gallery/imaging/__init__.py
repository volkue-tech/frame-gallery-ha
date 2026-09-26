"""Image preparation (§11).

Only ``imaging.worker_tasks`` may import Pillow; it runs in the worker (in
process during Phase 2). The other modules are standard-library only and are
safe to use in the parent.
"""
