"""The app's entry point: ``python -m frame_gallery`` (§4, §17.5; Phase 6).

Importing this module has no side effects (§11.3). :func:`main` builds the
production ports and runs exactly one run:

1. A :class:`CancellationController` that starts deferred, and only then the
   SIGTERM handler (D-141): a stop request during start-up is recorded, and
   the runner honours it inside its classified region.
2. The Supervisor token is read into memory, and the process environment is
   reduced to the allowlist before anything else runs, so no worker can see
   the token (§17.5). The token is kept only with helpers or a loading timer,
   and it is registered with the redactor either way.
3. Logging through the redactor (§19).
4. The process executor (D-163). On Linux every isolation step must be in
   force (:attr:`Launch.enforced`: the parent runs as root, its workers drop
   to 65534); otherwise the app refuses to run, as ``internal_error`` with
   exit code 70, before it contacts anything. Every worker start is shielded
   from stop requests.
5. The store from :class:`StoreLayout` (§13.1), the gateway and the three
   providers (§9), the helper reader (§15.3), the television (§12), and the
   watchdog, which fires at the run's ``T`` + 10 s (§4.3).
6. One run. If the watchdog claimed it, the watchdog emits the only summary
   line and ends the process with exit code 71: :func:`run_app` waits for it.

This is the only module that imports the real network transport and the
process executor; the boundary test enforces that.
"""

from __future__ import annotations

import functools
import logging
import os
import sys
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass, field
from typing import Final, TextIO

from frame_gallery.app.environment import (
    SUPERVISOR_TOKEN_VARIABLE,
    apply_environment,
    reduce_environment,
)
from frame_gallery.app.fetching import SourceFetcher
from frame_gallery.app.networks import ContainerNetworks
from frame_gallery.app.outcomes import Outcome
from frame_gallery.app.ports import NetworkInfo, ProviderBinding
from frame_gallery.app.runner import Runner, RunnerPorts
from frame_gallery.app.signals import CancellationController, deferring, install_sigterm_handler
from frame_gallery.budget.allowance import Allowance
from frame_gallery.budget.clock import Clock, SystemClock
from frame_gallery.budget.limits import METADATA_REQUEST_ALLOWANCE
from frame_gallery.budget.watchdog import RunWatchdog
from frame_gallery.config.options import ConfigError, LogLevel
from frame_gallery.domain import SourceKey
from frame_gallery.ha.client import SupervisorHelperReader
from frame_gallery.isolation.apparmor import ProfileError
from frame_gallery.isolation.executor import Executor
from frame_gallery.isolation.process import Launch, ProcessExecutor
from frame_gallery.logs.redact import Redactor
from frame_gallery.logs.setup import configure_logging, set_app_level
from frame_gallery.logs.summary import format_summary
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.identity import ClientIdentity, project_identity
from frame_gallery.net.transport import SystemResolver, Urllib3Transport
from frame_gallery.net.wire import Resolver, Transport
from frame_gallery.providers import aic, cma
from frame_gallery.providers.aic import AicProvider, aic_policy
from frame_gallery.providers.cma import CmaProvider, cma_policy
from frame_gallery.providers.local_media import LocalInspectionProbe, LocalMediaProvider
from frame_gallery.randomness import RandomSource, SystemRandomSource
from frame_gallery.store.diagnostics import log_storage
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.options_file import OptionsFile
from frame_gallery.store.preview import PREVIEW_PARTS
from frame_gallery.tv.port import Television
from frame_gallery.tv.samsung import HostTelevision

LIBRARY_PARTS: Final = ("frame_gallery", "library")
LEGACY_TOKEN_VARIABLE: Final = "HASSIO_TOKEN"  # noqa: S105 - a name, not a value
REFUSED_EXIT_CODE: Final = Outcome.INTERNAL_ERROR.exit_code

_log = logging.getLogger("frame_gallery.app")


def _process_executor(launch: Launch, clock: Clock, controller: CancellationController) -> Executor:
    return ProcessExecutor(launch, clock, shield=functools.partial(deferring, controller))


def _system_network() -> tuple[Resolver, Transport]:
    return SystemResolver(), Urllib3Transport()


def _host_television(executor: Executor, layout: StoreLayout) -> Television:
    return HostTelevision(executor, layout.data)


@dataclass(frozen=True, slots=True)
class Wiring:
    """What :func:`run_app` builds the run from. Production uses the
    defaults; tests replace the parts that would start processes or reach a
    network."""

    layout: StoreLayout = field(default_factory=StoreLayout)
    clock: Clock = field(default_factory=SystemClock)
    random: Callable[[], RandomSource] = SystemRandomSource
    networks: NetworkInfo = field(default_factory=ContainerNetworks)
    launch: Callable[[], Launch] = Launch.production
    executor: Callable[[Launch, Clock, CancellationController], Executor] = _process_executor
    network: Callable[[], tuple[Resolver, Transport]] = _system_network
    television: Callable[[Executor, StoreLayout], Television] = _host_television
    identity: Callable[[], ClientIdentity] = project_identity
    require_isolation: bool = field(default_factory=lambda: sys.platform.startswith("linux"))
    """Refuse to run unless :attr:`Launch.enforced` (on Linux: the container)."""

    require_apparmor: bool = False
    """Set only by main: own enforced profile is mandatory in the shipped app."""

    watchdog_exit: Callable[[int], object] = os._exit
    watchdog_wait: Callable[[float], bool] | None = None
    """How the watchdog ends the process and waits; replaced only by tests."""


def main() -> int:
    """One production run; returns its exit code (§4.2)."""
    return run_app(os.environ, sys.stderr, Wiring(require_apparmor=True))


def run_app(environ: MutableMapping[str, str], stream: TextIO, wiring: Wiring) -> int:
    """Run once with ``wiring``; see the module docstring. ``environ`` is
    reduced in place (``os.environ`` in production)."""
    controller = CancellationController(start_deferred=True)
    install_sigterm_handler(controller)
    clock = wiring.clock
    started = clock.monotonic()
    layout = wiring.layout
    options = OptionsFile(layout.data)
    secrets = [environ.get(name) for name in (SUPERVISOR_TOKEN_VARIABLE, LEGACY_TOKEN_VARIABLE)]
    timer = options.loading_timer()
    reduced = reduce_environment(
        environ, keep_supervisor_token=options.helpers_configured() or timer is not None
    )
    apply_environment(environ, reduced)
    redactor = Redactor(secret for secret in secrets if secret)
    configure_logging(level=LogLevel.INFO, stream=stream, redactor=redactor)

    try:
        launch = wiring.launch()
    except ProfileError:
        launch = None
    if (
        launch is None
        or (wiring.require_isolation and not launch.enforced)
        or (wiring.require_apparmor and launch.apparmor_profile is None)
    ):
        _log.error(
            "the workers cannot be isolated here: the app must run as root on Linux, "
            "where every worker drops to an unprivileged user, with the own enforced "
            "AppArmor profile (no artwork was sent)"
        )
        _log.error(
            "%s",
            format_summary(
                outcome=Outcome.INTERNAL_ERROR.value,
                exit_code=REFUSED_EXIT_CODE,
                elapsed_s=clock.monotonic() - started,
            ),
        )
        return REFUSED_EXIT_CODE

    random = wiring.random()
    executor = wiring.executor(launch, clock, controller)
    workspace = layout.workspace(None if launch.identity is None else launch.identity[1])
    records = layout.records(clock)
    resolver, transport = wiring.network()
    identity = wiring.identity()
    gateway = Gateway(
        resolver=resolver, transport=transport, clock=clock, random=random, identity=identity
    )
    aic_channel = gateway.channel(
        aic_policy(identity),
        metadata_allowance=Allowance("aic_metadata_requests", METADATA_REQUEST_ALLOWANCE),
    )
    cma_channel = gateway.channel(
        cma_policy(),
        metadata_allowance=Allowance("cma_metadata_requests", METADATA_REQUEST_ALLOWANCE),
    )
    aic_cache = layout.metadata_cache(aic.PROVIDER_KEY, clock)
    cma_cache = layout.metadata_cache(cma.PROVIDER_KEY, clock)
    local = LocalMediaProvider(
        root=layout.media.joinpath(*LIBRARY_PARTS),
        preview_dir=layout.media.joinpath(*PREVIEW_PARTS),
        preview_fingerprints=records.preview_fingerprints(),
    )
    try:
        reader_networks = wiring.networks.container_networks()
    except ConfigError:
        reader_networks = ()  # the run ends as config_invalid in CONFIGURE
    watchdog = RunWatchdog(
        clock=clock,
        on_fire=(executor.terminate_all, workspace.remove),
        emit_line=functools.partial(_log.error, "%s"),
        exit_process=wiring.watchdog_exit,
        wait=wiring.watchdog_wait,
    )
    reader = SupervisorHelperReader(
        token=reduced.supervisor_token,
        resolver=resolver,
        transport=transport,
        networks=reader_networks,
    )
    ports = RunnerPorts(
        options_source=options,
        network_info=wiring.networks,
        state=layout.state_store(clock),
        helper_reader=reader,
        providers={
            SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(
                AicProvider(aic_channel, aic_cache), cache=aic_cache
            ),
            SourceKey.CLEVELAND_MUSEUM_OF_ART: ProviderBinding(
                CmaProvider(cma_channel, cma_cache), cache=cma_cache
            ),
            SourceKey.LOCAL_MEDIA: ProviderBinding(
                local,
                probe=LocalInspectionProbe(local, executor),
                after_discovery=local.report_discovery,
            ),
        },
        fetcher=SourceFetcher(local=local, channels=(aic_channel, cma_channel)),
        executor=executor,
        television=wiring.television(executor, layout),
        workspace=workspace,
        preview=layout.preview(),
        records=records,
        watchdog=watchdog,
        storage_report=functools.partial(log_storage, layout, clock),
        finish_loading=functools.partial(reader.finish_loading, timer),
    )
    runner = Runner(
        ports, clock=clock, random=random, cancellation=controller, set_log_level=set_app_level
    )
    result = runner.run()
    if not result.summary_emitted:
        watchdog.wait_for_exit()
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
