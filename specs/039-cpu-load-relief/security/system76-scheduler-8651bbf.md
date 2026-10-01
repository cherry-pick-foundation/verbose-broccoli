# System76 Scheduler 8651bbf security review

- Version: default branch `master`, short commit `8651bbf`; package version remains `2.0.2`
- Commit: `8651bbf74bcfc8a46443b30199b380e12defa97e`
- Release comparison: tag `2.0.2`, commit `c403d0144eba88b952f663c52e2fcdb1a6c2f35f`
- Review date: 2026-10-01
- Verdict: **not acceptable as shipped for the planned root-service installation**
- Findings: **high 0, medium 6, low 1**
- Difficulty: **difficult**

## Scope and method

Assumption: the proposed installation uses the upstream system-wide daemon,
default configuration, and GNOME focus integration on the supplied Ubuntu
26.04.1 LTS, GNOME Shell 50.1, Wayland laptop. Its supplied CPU topology is
Intel Core Ultra 7 258V, performance cores 0–3 and efficiency cores 4–7.
Archive availability and the supplied desktop/CPU versions were not independently
checked. The execution host's kernel and selected paths were inspected below.

This was a source, release, dependency, integration, and rollback review.
The complete scheduler runtime and configuration modules, workspace manifests,
lockfile, unit, bus policy, installation recipes, and Debian packaging were
read. The complete small standalone extension was read. Pop Shell review
covered its metadata, scheduler client, focus-event and enable/disable paths,
and build/install/configuration scripts; it was not a whole-Pop-Shell audit.
The pinned zbus dispatcher/macro and Tokio channel contract were also inspected
to validate the locking finding. A synthetic Python model checked that wait
cycle; it did not call D-Bus or run the scheduler.

Clones and downloaded API/source/advisory evidence were confined to the
gitignored `.local/system76-scheduler/` directory and removed after the review.
Source references below are upstream-relative paths at the exact commit above,
unless an extension, dependency, tag, or installed file is explicitly named.
They remain reproducible after scratch cleanup through the
[pinned scheduler tree](https://github.com/pop-os/system76-scheduler/tree/8651bbf74bcfc8a46443b30199b380e12defa97e).

```text
$ git -C .local/system76-scheduler/scheduler rev-parse HEAD
8651bbf74bcfc8a46443b30199b380e12defa97e
$ git -C .local/system76-scheduler/scheduler rev-parse '2.0.2^{commit}'
c403d0144eba88b952f663c52e2fcdb1a6c2f35f
$ sha256sum .local/system76-scheduler/scheduler/Cargo.lock
85b7980e28f3ca580d41b0d14de84ef019ca181596033621505b01e4da72d25f
```

No privileged command, installation, service activation, extension activation,
settings change, or execution of the daemon occurred. No build was attempted:
clang, libclang development files, and PipeWire development files are missing.
This record is a worker assessment for coordinator review, not final approval
of an installation or of the feature.

## Verdict

The daemon has no application Internet client, updater, or telemetry path.
It nevertheless introduces a root service that accepts scheduling instructions
from every local bus client and parses every user's PipeWire socket with root
privileges. Two separate queue/locking paths can impair availability. Both
the release and current lockfile contain known advisory matches. The newer
commit is the better functional review target, but choosing it does not resolve
these security controls.

**GNOME 50 support: yes in Pop Shell source; no for the standalone extension.**
Pop Shell `master_noble`, metadata version 2 at
`7898b65c20735057faf0797f8ed056704ca55f0d`, declares GNOME 50 and includes the
focus-to-scheduler call. It is not available for its UUID on
extensions.gnome.org in the checked API. The standalone System76 Scheduler
extension, version 5 at `c181c731f76ca80ce0359efb8fa598e4ab77f881`, supports
40–44 only, both in source and in the site's version map. Neither was loaded
on GNOME 50.1, so source support is not runtime acceptance.

For CHE-73, this program changes priority and global scheduler latency; it does
not cap CPU consumption or place builds on cores 4–7. No affinity, cpuset, or
CPU quota write exists in the reviewed runtime. A whole-desktop extension and
root daemon therefore need a separate benefit measurement before adoption.
The requested `systemd-run`/`nice`/`taskset` build restriction is independent
of this daemon.

## Findings

### F-01 — Medium — Every local D-Bus client can change system-wide scheduling

The default bus policy permits messages to the scheduler without restricting
user, method, session, or process ownership. Its handlers do not inspect the
sender, authorize through Polkit, or verify that a supplied PID belongs to the
caller or focused window. `SetForegroundProcess` walks descendants and can
reassign every otherwise assignable process, including processes in other
sessions. An invalid or nonexistent foreground PID can leave assignable
processes in the background profile. `SetCpuMode` and `SetCpuProfile` change
global kernel settings when that kernel exposes the required files.
`ReloadConfiguration` rereads fixed administrator-controlled paths; it does
not accept an arbitrary filename or configuration body.

Evidence: `data/com.system76.Scheduler.conf:5-13` grants root name ownership
and default-context send/receive access; `daemon/src/dbus.rs:70-98` forwards
all four mutators without authorization; `daemon/src/service.rs:539-569`
applies foreground/background settings across the process map;
`daemon/src/priority.rs:17-60` uses privileged per-thread priority syscalls;
`daemon/src/main.rs:281-326` handles CPU modes and reloads.

The default foreground profile is nice 0, not real-time CPU scheduling.
This is unauthorized cross-user scheduling control and an availability issue,
not demonstrated arbitrary code execution or arbitrary file writing.

Control: deny other accounts and restrict CPU-mode/configuration methods to
root. A bus policy permitting only the desktop account's foreground method
still trusts every process in that account. Accept that boundary explicitly,
or require authenticated session/PID ownership checks in an upstream change.

### F-02 — Medium — A full event queue can deadlock against the D-Bus interface lock

Mutable D-Bus handlers await sends into a four-entry event queue while zbus
holds the interface's write lock. The event consumer must acquire the same
interface's read lock to process CPU-mode and battery events. A previously
waiting refresh, battery, or exec producer can receive the next freed queue
slot before the handler: the handler waits for another slot while holding the
write lock, and the consumer waits for that lock before consuming again.
This wait cycle requires concurrent traffic; ordinary single requests need
not trigger it. The unit has no watchdog, and restarting only on process
exit would not recover an alive deadlocked process.

Evidence: `daemon/src/main.rs:166,187-197,239,272-319,387-390` defines the
bounded queue, independent producers, and consumer-side interface reads;
`daemon/src/dbus.rs:74-97` awaits sends from `&mut self` methods.
At zbus tag `zbus-3.11.1`, `zbus_macros/src/iface.rs:427-444` generates mutable
dispatch and `zbus/src/object_server.rs:666-688` holds the write lock across
the method future; its `:85-86` acquires the read lock for `get()`.
Tokio tag `tokio-1.27.0`, `tokio/src/sync/mpsc/bounded.rs:444-446,474-475`
documents ordered send reservations and implements send through reserve.
The [zbus dispatcher](https://github.com/dbus2/zbus/blob/zbus-3.11.1/zbus/src/object_server.rs#L666)
and [Tokio queue contract](https://github.com/tokio-rs/tokio/blob/tokio-1.27.0/tokio/src/sync/mpsc/bounded.rs#L444)
are the reviewed dependency sources.

The following synthetic check exited 0 and reproduced the wait cycle.
It models the source's ordering; it is not a runtime exploit against zbus.

```python
import asyncio

async def main():
    queue = asyncio.Queue(maxsize=4)
    interface = asyncio.Lock()
    for _ in range(4):
        await queue.put("SetCpuMode")

    async def producer():
        await queue.put("RefreshProcessMap")

    async def setter():
        async with interface:
            await queue.put("SetCpuMode")

    async def receiver():
        await queue.get()
        async with interface:
            pass

    p = asyncio.create_task(producer())
    await asyncio.sleep(0)
    s = asyncio.create_task(setter())
    await asyncio.sleep(0)
    r = asyncio.create_task(receiver())
    await asyncio.sleep(0.05)
    assert p.done() and not s.done() and not r.done()
    print(p.done(), queue.qsize(), interface.locked(), s.done(), r.done())
    for task in (p, s, r):
        task.cancel()
    await asyncio.gather(p, s, r, return_exceptions=True)

asyncio.run(main())
# True 4 True False False
```

The executed equivalent printed:
`producer_done=True queue=4 interface_lock_held=True setter_blocked=True receiver_blocked=True`.
Control: remove the lock/send cycle in upstream and verify concurrent D-Bus
traffic before enabling the service. Restricting callers reduces exposure
but does not remove the cycle with internal event producers.

### F-03 — Medium — PipeWire parsing retains root and trusts user-controlled process IDs

The daemon spawns its own `pipewire` subcommand without dropping credentials.
That child scans every directory in `/run/user`, connects to `pipewire-0`,
and processes its native PipeWire protocol. The socket's UID and peer
credentials are not checked. A user controlling their PipeWire server can
provide `application.process.id` for another existing assignable process;
the root daemon uses it without checking that process's owner. The same input
boundary exposes native libpipewire and its bindings to a root child.
No memory-corruption exploit in that library was established in this review.

Evidence: `daemon/src/pw.rs:51-86,110-123` connects the sockets and spawns
the inherited-privilege child; `pipewire/src/lib.rs:83-89,99-104,125-129`
parses the supplied PID and connects the native client;
`daemon/src/service.rs:573-600` applies the resulting profile to that process
and its descendants. `data/com.system76.Scheduler.service:4-8` has no
`User`, capability restriction, filesystem sandbox, or network restriction.

Control: remove the `pipewire` assignment profile to disable this integration
at startup, or move monitoring into an unprivileged, authenticated session
client and validate PID ownership. A separate process isolates crashes but
does not lower privileges. Configuration reload does not stop an already
running monitor (`daemon/src/pw.rs:43`); changing this control requires a
service restart.

### F-04 — Medium — Exec events enter an unbounded root-process queue

With execsnoop enabled, every successful observed exec contributes owned
name/path strings to an unbounded queue. Consumption waits until two seconds
after creation and then forwards into the small main event queue. A local
exec burst or a blocked main loop can produce events faster than consumption
and retain unbounded memory. This is an additional resource amplifier, beyond
the user's own process load, in a service without `MemoryMax` or task limits.

Evidence: `daemon/src/main.rs:350-390` creates the unbounded channel, allocates
strings per event, and awaits delayed forwarding;
`execsnoop/src/lib.rs:91-115` launches the external tool without a UID filter;
`data/config.kdl:24-25` enables it; the entire 11-line unit defines no resource
limits. No exec flood or memory exhaustion was performed.

Control: use `execsnoop false` and periodic refresh for this use. If realtime
exec tracking is necessary, require bounded/coalesced events and measured
service resource limits upstream before enabling it.

### F-05 — Medium — Both lockfiles retain advisory matches requiring triage

Exact-version OSV queries returned matches for 12 package/version entries in
both snapshots, including memory-safety advisories and unmaintained libraries.
The current lock still pins `bytes` 1.4.0 and `tracing-subscriber` 0.3.16.
There is no demonstrated dependency exploit here: several entries require
specific APIs, features, operating systems, or extreme inputs. Treating every
lockfile match as reachable would overstate the result; treating the lock as
clean would be incorrect. The native system libraries are outside Cargo's
advisory coverage.

Evidence: `Cargo.lock:25-28,74-77,287-290,462-465,509-512,780-783,980-983,1195-1198,1286-1289,1395-1398,1593-1596,1722-1725`
pins the matched versions. The reproducible OSV request and per-package
results are in the dependency section below. `daemon/src/main.rs:67-75`
initializes the vulnerable formatter; `daemon/src/main.rs:318` can format
the D-Bus-controlled CPU profile at debug level.

Control: obtain an upstream lock refresh and rerun exact-version advisory
queries. Resolve reachable advisories; document target/API/feature exclusions
for the rest. Do not silently update the lock and treat this record as covering
the resulting binary.

### F-06 — Medium — The selected root-service source has weaker authentication than the release commit

The last release commit has a valid GPG signature according to GitHub, but
the annotated release tag itself is unsigned. The newer selected commit is
unsigned. Release 2.0.2 supplies only generated source archives, with zero
uploaded assets, checksums, SBOMs, or signed binary attestations to verify.
The repository has no release workflow at the selected commit. A full commit
pin and dependency checksums make input changes visible; they do not establish
an independent publisher-to-build provenance chain.

Evidence: the read-only GitHub APIs returned:

```text
GET /repos/pop-os/system76-scheduler/releases
2.0.2 published_at=2024-08-22T21:36:03Z assets=[]
GET /repos/pop-os/system76-scheduler/commits/c403d0144eba88b952f663c52e2fcdb1a6c2f35f
verification: verified=true reason=valid
GET /repos/pop-os/system76-scheduler/git/tags/b58d09085b073427d48c92d84ef6dffa599eb8f8
verification: verified=false reason=unsigned
GET /repos/pop-os/system76-scheduler/commits/8651bbf74bcfc8a46443b30199b380e12defa97e
verification: verified=false reason=unsigned
$ git -C .local/system76-scheduler/scheduler ls-tree -r HEAD .github
100644 blob 0af2758e76969b29d0d166a367948dc5a1a6f02a .github/PULL_REQUEST_TEMPLATE.md
```

Control: accept the unsigned-source boundary explicitly, pin the full commit
and reviewed lock hash, build with `--locked` as the user, inspect the output,
and install only the resulting fixed artifact. Record its hash and compiler
and native-library versions. A future signed release containing the fixes
is preferable. No local GPG trust or binary attestation was verified.

### F-07 — Low — Stopping does not restore settings, and upstream uninstall deletes whole config directories

There is no original-value snapshot, `ExecStop`, or signal cleanup that restores
autogroup, scheduler parameters, or process priorities. Those changes outlive
the daemon. Upstream uninstall recursively removes its entire configuration
directory and does not preserve preexisting files or disable the unit first.
With a mismatched `sysconfdir`, it also removes a different policy/config path
from the one installed. Pop Shell's `make local-install` changes dconf settings;
its uninstall removes only the extension directory and leaves those settings.

Evidence: `daemon/src/main.rs:176-181,323-330,344-346` writes live values and
returns without restoration; `daemon/src/cfs/mod.rs:16-42` writes without
snapshot; `daemon/src/priority.rs:17-60` changes priority without saving it;
`justfile:55-68` defines overwrite/install and recursive uninstall.
Pop Shell `Makefile:60-68` runs configuration on local install but only removes
the extension on uninstall; `scripts/configure.sh:38-119` writes desktop
settings. This is a rollback/data-preservation risk, not an unprivileged
arbitrary-deletion path.

Control: use the explicit installation manifest and baseline procedure below.
Delete only files introduced by this installation, restore backups where
present, restore captured kernel values, and restart affected workloads or
reboot after removing service startup. Do not infer the prior state from the
upstream profile named `default`.

## Root execution, privileges, and inputs

`data/com.system76.Scheduler.service:4-11` starts
`/usr/bin/system76-scheduler daemon` with `Type=dbus` and bus name
`com.system76.Scheduler`; enabling it links it into `multi-user.target`.
There is no `User`/`Group`, so the system service uses root. The unit adds no
capability bounding set, `NoNewPrivileges`, seccomp filter, private namespace,
read-only filesystem restriction, address-family restriction, CPU/memory
limit, or explicit restart policy. Actual host-wide AppArmor, systemd defaults,
and kernel/BPF restrictions were not inspected or bypassed.

The daemon needs authority to adjust other users' threads: `setpriority`,
`sched_setscheduler`, and `ioprio_set`. `CAP_SYS_NICE` is relevant to these
operations, but the upstream unit gives root rather than proving a minimum
capability set. Its global scheduler/debugfs writes and optional BPF tracing
add privilege needs; no tested capability-only unit exists in this review.
Do not apply a generic syscall or read-only sandbox and claim compatibility.

The service uses the **system** bus, interface `com.system76.Scheduler`, object
`/com/system76/Scheduler` (`daemon/src/main.rs:218-230`). Root may own the name;
the default policy lets any otherwise bus-connected local user send to it.
There is no separate D-Bus activation `.service` file: the file ending in
`.service` under `data/` is the systemd unit, and the installer places it under
`/usr/lib/systemd/system`. Calls are `SetForegroundProcess(u32)`,
`SetCpuMode(u8 enum: auto/custom/default/responsive)`,
`SetCpuProfile(string)`, and `ReloadConfiguration()`, plus read-only
`CpuMode`/`CpuProfile` properties (`daemon/src/dbus.rs:21-98`).
The daemon also reads UPower's battery property and notifications from the
system bus (`daemon/src/main.rs:168-181,333-341`).

The scheduler reads `/proc` process directories, executable symlinks, status
and parent IDs, each PID's `cgroup` text, and child/thread lists
(`daemon/src/process.rs:139-208`, `daemon/src/service.rs:462-537`,
`daemon/src/priority.rs:17-28`). Despite the name `cmdline`, ordinary polling
uses `/proc/<pid>/exe`, not the entire command-line file. Execsnoop sees exec
arguments; its local parser retains the first command field
(`execsnoop/src/lib.rs:44-73`). No student or vault paths were accessed.

Configuration inputs are fixed:

| Input | Resolution |
| --- | --- |
| `/etc/system76-scheduler/config.kdl` | Takes precedence if present |
| `/usr/share/system76-scheduler/config.kdl` | Used when `/etc` main config is absent |
| `/usr/share/system76-scheduler/process-scheduler/*.kdl` | Additional distribution assignments |
| `/etc/system76-scheduler/process-scheduler/*.kdl` | Additional system assignments, read after distribution assignments |

Evidence: `config/src/lib.rs:23-24,46-72` and
`config/src/parser/mod.rs:45-65,103-146`. Files are opened normally, so symlinks
are followed and ownership is not validated by the daemon. Keep both trees
and link targets administrator-owned. Directory entries are not sorted; do
not depend on a stable override order among multiple files in one directory.

The supplied config enables process scheduling and CFS tuning, disables
autogroup, uses a 60-second refresh, and enables execsnoop
(`data/config.kdl:8-25`). Process profiles include nice 0 foreground,
nice 6/idle-I/O background, nice 19/`SCHED_IDLE` batch, and nice -15/realtime-I/O
sound servers (`:29-70`). The realtime sound-server setting is an **I/O class**;
the release removed realtime CPU FIFO for that profile. Root configuration
can still select CPU FIFO/RR priorities 1–99
(`config/src/scheduler/mod.rs:155-213`, `config/src/parser/scheduler.rs:271-297`).

The daemon itself embeds no BPF program. With execsnoop enabled and the
compile-time `EXECSNOOP_PATH` present, it executes that program as root with
`LC_ALL=C`, inherited environment, piped stdout, and discarded stderr; no
shell is used (`execsnoop/src/lib.rs:14-17,91-99`). `justfile:23-24` resolves
the compile-time path from the builder's PATH, so pin a trusted absolute path.
Missing execsnoop produces a warning and leaves periodic polling enabled.

Read-only host inspection found `bpfcc-tools 0.35.0+ds-1ubuntu2` and
`/usr/sbin/execsnoop-bpfcc`, mode 755, root:root. Its script imports BCC,
compiles embedded C into BPF, attaches an execve kprobe/kretprobe, and polls
a perf buffer (`/usr/sbin/execsnoop-bpfcc:23-25,272-275,358-361`). It was
never executed. BPF capability/lockdown support was not tested. No pinning of
BPF objects was found in that script; kernel probe/resource cleanup and
successful attachment remain untested. The optional helper's entire native
dependency chain was not audited.

## Network access

The reviewed scheduler code contains no HTTP client, TCP/UDP listener,
telemetry, updater, or Internet request. Runtime communication uses the local
system D-Bus socket and Unix sockets `/run/user/*/pipewire-0`
(`daemon/src/main.rs:81`, `daemon/src/pw.rs:55-81`). The focus clients use
`Gio.DBus.system`; their scheduler paths make no network request.
PipeWire node enumeration is not audio capture in the reviewed Rust code.

The root unit does not enforce that observed local-only behavior: it provides
no network namespace or address-family restriction. Native libraries/plugins
are outside the complete Rust-source review. A changed configuration,
dependency, executable, or library could extend that boundary.

Git clone/API access, extension API checks, and OSV queries used the network
during review. A future Cargo build normally reads crates.io/index and crate
archives unless dependencies are supplied offline; those downloads and crate
build scripts were not executed here. There was no release download executable
to run. The D-Bus XML DTD URL is a declaration, not an application HTTP call.

## System changes and persistence

These are the complete direct scheduler-file write targets identified in the
runtime; process priorities are changed by syscalls rather than procfs writes.

| Target | Effect and lifetime |
| --- | --- |
| `/proc/sys/kernel/sched_autogroup_enabled` | Writes 0 with shipped config, including when no CFS tuning path exists; remains after stop until restored or reset at boot |
| `/sys/kernel/debug/sched/latency_ns` or `/proc/sys/kernel/sched_latency_ns` | Global scheduler latency, when supported; remains after stop |
| `/sys/kernel/debug/sched/min_granularity_ns` or `/proc/sys/kernel/sched_min_granularity_ns` | Minimum scheduling granularity; remains after stop |
| `/sys/kernel/debug/sched/wakeup_granularity_ns` or `/proc/sys/kernel/sched_wakeup_granularity_ns` | Wakeup granularity; remains after stop |
| `/proc/sys/kernel/sched_cfs_bandwidth_slice_us` | Global bandwidth slice, config value multiplied by 1000; remains after stop |
| `/sys/kernel/debug/sched/preempt` | Writes `full` or `voluntary`, only when detected; remains after stop |
| Every selected PID's threads | Nice, CPU scheduling policy/priority, and I/O priority; retained by surviving threads and potentially inherited by children |

Evidence: `daemon/src/main.rs:344-346`, `daemon/src/cfs/paths.rs:6-7,25-48`,
`daemon/src/cfs/mod.rs:16-42`, and `daemon/src/priority.rs:17-60`.
The source declares migration-cost paths but **does not write them**.
There are no direct writes to CPU-frequency/governor/power-limit sysfs,
cpuset, cgroup membership, `cpu.weight`, `cpu.max`, or disk data.
Cgroup names are only matching inputs. A normal systemd service cgroup is
created by systemd, not by a scheduler cgroup implementation.

The latency formula uses logical CPU count, not core type. For eight CPUs the
modifier is 4,000,000. If the old tuning interface is supported, the shipped
responsive profile writes latency 16,000,000 ns, minimum granularity
1,600,000 ns, wakeup granularity 2,000,000 ns, bandwidth slice 3000 microseconds,
and `full` preemption. The `default` profile writes 24,000,000 ns, 3,000,000 ns,
4,000,000 ns, 5000 microseconds, and `voluntary`. These are configured values,
not a captured Ubuntu baseline (`daemon/src/cfs/mod.rs:17-28,49-50`).

Read-only host checks returned kernel `7.0.0-34-generic`, autogroup 1,
and bandwidth slice 5000. `/proc/sys/kernel/sched_latency_ns` was absent.
The debugfs scheduler files were not visible to the reviewing user;
`/sys/kernel/debug` is mode 700 root:root. This does **not** establish that
the root daemon would find no debugfs interface. When neither latency path
exists for the daemon, it skips all CFS writes; it still changes autogroup
and enabled process priorities (`daemon/src/service.rs:33,290-299`).
No EEVDF-era kernel compatibility or benefit is claimed without a privileged
path check and later runtime measurement.

The daemon writes ordinary logs to stderr, normally retained by journald.
It creates no own persistent database, sysctl.d file, or boot configuration.
Installed binaries/configs/policies/unit files and enable symlinks persist
after stop. BPF and PipeWire helpers are processes in the service cgroup;
the unit does not override systemd's default control-group kill behavior.
The Rust execsnoop wrapper kills/waits for its helper on normal drop
(`execsnoop/src/lib.rs:79-84`); actual signal/BPF cleanup was not tested.
Journal/audit history remains after uninstall and is not erased by the
rollback procedure.

## Source installation and uninstall

### Source recipe and exact installed paths

The following commands are **documentation only**, not approval or an executed
procedure. F-01 through F-06 must be resolved or explicitly accepted before
installation. The recipe shows the unmodified reviewed source, so it cannot
stand in for a later patched-source review.

Prerequisites are Cargo/rustc, clang, just, libclang development files,
libpipewire-0.3 development files, and pkg-config (`README.md:11-29`,
`debian/control:5-13`). Bpfcc-tools is optional when execsnoop is disabled.
On Ubuntu the explicit prerequisite installation is:

```sh
sudo apt-get install cargo rustc clang just libclang-dev libpipewire-0.3-dev pkg-config
```

Run this only in a separate approved installation window after capturing
package state. It can add/upgrade transitive packages; an unconditional
`apt autoremove` or `apt purge` cannot restore their prior state. For a strictly
reversible trial, provision these prerequisites beforehand or take a system
snapshot that includes package state. This review installed none.

From the repository root, with an approved Rust toolchain already selected:

```sh
mkdir -p .local/system76-scheduler
git clone https://github.com/pop-os/system76-scheduler.git .local/system76-scheduler/scheduler
git -C .local/system76-scheduler/scheduler checkout --detach 8651bbf74bcfc8a46443b30199b380e12defa97e
cd .local/system76-scheduler/scheduler
git rev-parse HEAD
sha256sum Cargo.lock
systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7 \
  env EXECSNOOP_PATH=/usr/sbin/execsnoop-bpfcc \
  CARGO_HOME="$PWD/../cargo-home" CARGO_TARGET_DIR="$PWD/target" \
  cargo build --release --locked -p system76-scheduler
sha256sum target/release/system76-scheduler
```

The wrapper is required for every build, including any later extension build.
Cargo build scripts execute as the user; no build runs as root. Never use
`cargo run` or execute the binary to check its version during this review.
Upstream `just build-release` passes `EXECSNOOP_PATH` but does not add `--locked`
(`justfile:37-42`), so the explicit Cargo command fixes that omission.

The README's installer is `sudo just sysconfdir=/usr/share install`. Its exact
five-file manifest is:

| Destination | Source/mode |
| --- | --- |
| `/usr/bin/system76-scheduler` | `target/release/system76-scheduler`, 0755 |
| `/usr/lib/systemd/system/com.system76.Scheduler.service` | `data/com.system76.Scheduler.service`, 0644 |
| `/usr/share/dbus-1/system.d/com.system76.Scheduler.conf` | `data/com.system76.Scheduler.conf`, 0644 |
| `/usr/share/system76-scheduler/config.kdl` | `data/config.kdl`, 0644 |
| `/usr/share/system76-scheduler/process-scheduler/pop_os.kdl` | `data/pop_os.kdl`, 0644 |

With plain `sudo just install`, `sysconfdir` defaults to `/etc`: both configs
and bus policy instead land there (`justfile:4-10,55-61`). Keep the chosen
prefix consistent. A `/usr/local` prefix alone would not update the unit's
hard-coded `/usr/bin` ExecStart. The source installer itself neither enables
nor starts the unit; Debian `debian/postinst:4-5` does both, so Debian package
installation has a different activation boundary.

For the clean-install case, first establish that these five destinations,
`/etc/system76-scheduler`, matching `/etc` bus policy, unit overrides/aliases,
and scheduler enable symlinks do not already exist. If any exists, stop the
clean-install procedure and capture its files, ownership, modes, enablement,
and running state in a protected backup. Do not overwrite another installation.
Capture the actual kernel values in the table above and, for a live no-reboot
rollback, every potentially affected thread's PID **and start time**, nice,
CPU policy/priority, and I/O class/priority. Upstream saves none of these.

The five explicit installation commands, from the pinned source directory,
are equivalent to the reviewed `/usr/share` recipe:

```sh
sudo install -Dm0755 target/release/system76-scheduler /usr/bin/system76-scheduler
sudo install -Dm0644 data/com.system76.Scheduler.service /usr/lib/systemd/system/com.system76.Scheduler.service
sudo install -Dm0644 data/com.system76.Scheduler.conf /usr/share/dbus-1/system.d/com.system76.Scheduler.conf
sudo install -Dm0644 data/config.kdl /usr/share/system76-scheduler/config.kdl
sudo install -Dm0644 data/pop_os.kdl /usr/share/system76-scheduler/process-scheduler/pop_os.kdl
sudo systemctl daemon-reload
sudo systemctl reload dbus.service
```

These steps install but do not activate the scheduler. After an independently
reviewed policy/configuration is in place and rollback is captured, the
explicit activation would be:

```sh
sudo systemctl enable --now com.system76.Scheduler.service
```

An accepted security fix, config edit, or unit drop-in must be added to the
installation manifest and reviewed separately; the commands above intentionally
do not pretend to implement the findings' controls.

### Exact clean-install removal and restoration limits

For the five-file `/usr/share` installation above with no earlier scheduler,
the removal commands are:

```sh
sudo systemctl disable --now com.system76.Scheduler.service
sudo systemctl reset-failed com.system76.Scheduler.service
sudo rm -- /usr/bin/system76-scheduler
sudo rm -- /usr/lib/systemd/system/com.system76.Scheduler.service
sudo rm -- /usr/share/dbus-1/system.d/com.system76.Scheduler.conf
sudo rm -- /usr/share/system76-scheduler/config.kdl
sudo rm -- /usr/share/system76-scheduler/process-scheduler/pop_os.kdl
sudo rmdir -- /usr/share/system76-scheduler/process-scheduler
sudo rmdir -- /usr/share/system76-scheduler
sudo systemctl daemon-reload
sudo systemctl reload dbus.service
```

`rmdir` intentionally fails when unexpected files remain. Remove trial-created
drop-ins or alternate `/etc` files only if they were recorded in the manifest;
restore preexisting files from their protected backups instead of deleting
them. If installed with `/etc`, substitute the two `/etc/system76-scheduler`
paths and `/etc/dbus-1/system.d/com.system76.Scheduler.conf`. The corresponding
upstream command is `sudo just sysconfdir=/usr/share uninstall`, but it uses
recursive deletion and omits service/kernel restoration, so it is not the
preferred rollback procedure.

If the service was started, restore each captured kernel value using root
write authority, for example the following **template**, substituting a value
from the baseline rather than an upstream default:

```sh
printf '%s\n' "$saved_autogroup" | sudo tee /proc/sys/kernel/sched_autogroup_enabled >/dev/null
```

Repeat for every supported target in the write table. The preemption file can
show alternatives with the active mode in brackets; save and restore the active
token, not the whole displayed line. Surviving threads require baseline-derived
`renice`, `chrt`, and `ionice` restoration only after validating start times
against PID reuse. There is no universal exact priority-restoration command
without that baseline, and changing every thread to nice 0 would be wrong.
After stopping/disabling/removing the daemon, a planned reboot restores normal
boot-configured kernel/workload state without guessing thread priorities.
It does not recreate the previous running applications or erase logs.

Thus exact restoration of the **previous live machine state** cannot be promised
by an uninstall command alone. Restoring the persistent manifest and snapshot,
then restarting workloads or rebooting, is the defined rollback boundary.
Package additions/upgrades need the captured package/system snapshot too.
No backup, install, removal, live-setting restoration, or reboot was run here.

## GNOME Shell 50 extension support

### Standalone System76 Scheduler extension: no

Repository: [mjakeman/s76-scheduler-plugin](https://github.com/mjakeman/s76-scheduler-plugin).
Version: metadata version 5. Commit:
`c181c731f76ca80ce0359efb8fa598e4ab77f881`, dated 2023-06-08.
UUID: `s76-scheduler@mattjakeman.com`.
`metadata.json:5-13` lists exactly `40`, `41`, `42`, `43`, `44`.
The [extensions.gnome.org listing](https://extensions.gnome.org/extension/4854/system76-scheduler/)
and `extension-info/?pk=4854` likewise return version 5 for those versions,
with no 50 entry. No GNOME 50 package was found for this UUID.

Its `extension.js:24-27,103-105` uses legacy `imports.*` and `init(meta)`;
`:59-72` gets the focused window PID and calls `SetForegroundProcess` on the
system bus. It runs inside the user's GNOME Shell, not as root. On communication
error, `:75-82` also refers to undeclared `idleId` and `array`, so the error
cleanup is defective. This is additional source evidence against forcing this
old extension into use by disabling version validation. No such setting was
changed. It has no separate npm dependencies or updater/network client in its
four-file source tree.

### Pop Shell: yes in source, unavailable through the checked extension API

Repository: [pop-os/shell](https://github.com/pop-os/shell), branch `master_noble`.
Version: metadata version 2, not a new scheduler-specific release tag. Commit:
`7898b65c20735057faf0797f8ed056704ca55f0d`, dated 2026-03-31, message
`feat: GNOME 50 support`. UUID: `pop-shell@system76.com`.
The [pinned metadata](https://github.com/pop-os/shell/blob/7898b65c20735057faf0797f8ed056704ca55f0d/metadata.json#L7)
at `metadata.json:7-14` lists `45`, `46`, `47`, `48`, `49`, `50`.

The integration is present in code, not just metadata:
`src/extension.ts:1972-2034` handles the focus-window signal and initial focus;
`:873-875` calls `scheduler.setForeground(win.meta)`;
`src/scheduler.ts:3-16,21-35` obtains `Meta.Window.get_pid()` and invokes
`SetForegroundProcessRemote` on the correct system-bus name/path/interface.
It uses `gi://` imports and `src/extension.ts:2681` exports an extension class.
That path does not require X11 focus polling. `src/scheduler.ts:19-21,38-41`
permanently suppresses further sends after its first error for that module's
lifetime; changing enable state alone need not recover the client.

```text
GET https://extensions.gnome.org/extension-info/?uuid=pop-shell%40system76.com
HTTP 404 Not Found
GET https://extensions.gnome.org/extension-info/?pk=4854
shell_version_map keys: 40, 41, 42, 43, 44; each version=5
```

Pop Shell is a tiling/window-management extension, with keybindings, Shell
injections, settings, and launcher integration; it is not a focus-only module.
Its `Makefile:60-68` local-install target installs, configures, enables, and
attempts Shell restart, while uninstall removes only the extension directory.
`scripts/configure.sh:38-119` writes keyboard, user-extension, and workspace
settings. Installing it solely for focus reporting would broaden CHE-73.
The declared GNOME 50 support answers the source question **yes**; safe full
Pop Shell adoption and operation on this laptop remain unverified.

For a separately approved extension trial, capture the existing extension
directory, enabled-extension list, Pop Shell settings, and each dconf subtree
touched by its configure script before installation. Build only with the
required `systemd-run --user --scope -q -p CPUWeight=20 nice -n 10 taskset -c 4-7`
wrapper. Use the narrowly selected build/install targets and avoid
`make local-install` unless its desktop changes are wanted. On rollback,
disable the newly enabled extension, restore the prior directory/settings and
enabled list, and log out/in on Wayland. `make uninstall` alone cannot restore
those settings. Full extension install/rollback approval is outside this
scheduler record's five-file installation manifest.

## Review target: release 2.0.2 or newer default-branch commit

Review and pin **8651bbf**, with the release comparison above. Upstream calls
its default branch `master`, not `main`. The newer commit is not version 2.0.3:
`daemon/Cargo.toml:5` still declares 2.0.2, so record the full source commit.

The release's `daemon/src/main.rs:191-193` sends one refresh event and sleeps
once; it never loops. New commit `b0b7e98b0dbd2cd05e9fe80829e7083048202da7`
adds the interval loop, visible at reviewed `daemon/src/main.rs:187-197`. Head commit
`8651bbf` updates PipeWire/libspa from 0.6 to 0.10 to address monitor SIGABRT,
with owned-FD and reference-counted API changes in `pipewire/src/lib.rs`.
Earlier commits update generator and proc-macro2. The 2.0.2-to-HEAD comparison
changes 10 files, 398 insertions and 140 deletions, mostly lockfile updates.
These are concrete reasons to inspect newer source on a modern PipeWire host;
the commit message is not runtime proof that every abort is fixed.

The newer refresh loop also has a configuration trap: `data/config.kdl:21`
says refresh-rate 0 disables polling, but `config/src/parser/scheduler.rs:26-28`
accepts zero and `daemon/src/main.rs:188-192` passes it to Tokio interval.
Tokio 1.27.0 `tokio/src/time/interval.rs:75,110` asserts a positive duration,
so zero is not a usable disable setting here. Use `process-scheduler enable=false` to disable that
subsystem, or keep a positive refresh period. This is trusted-configuration
correctness debt; it was not counted as a separate attacker-controlled finding.

The release's signed commit offers better authentication, but has older
functional defects and the same 12 matched dependency versions. Neither
snapshot is approved as shipped. Prefer a future signed release carrying
functional fixes and security controls rather than following a moving branch.

## Release provenance and dependency advisories

The [release API](https://api.github.com/repos/pop-os/system76-scheduler/releases)
reports the latest release as `2.0.2`, published 2024-08-22; the selected
[commit API](https://api.github.com/repos/pop-os/system76-scheduler/commits/8651bbf74bcfc8a46443b30199b380e12defa97e)
reports 2026-07-22 and unsigned verification. The annotated tag object is
`b58d09085b073427d48c92d84ef6dffa599eb8f8`, pointing to the signed release
commit. GitHub's verification response was inspected, not locally verified
against an independently trusted maintainer key. No uploaded release binaries
or release attestation were available to hash/verify. No attestation search
was performed for an unbuilt local binary.

The current workspace contains 242 lock entries: four local packages and 238
registry entries, all 238 with checksums. The tag has 211 entries: four local
and 207 registry entries. Main manifests use semver requirements, while the
lock pins exact dependencies. `rust-toolchain.toml:1-3` selects mutable
`stable`, so the source pin alone does not pin the compiler. PipeWire is
dynamically supplied by the system, and its build requires pkg-config and
libclang/bindgen. The lock does not identify the installed native-library or
BPF-helper provenance.

Every registry package/version pair in **both** lockfiles was submitted to
OSV's exact-version batch endpoint on the review date. Both batches returned
12 matched entries and the same 20 advisory IDs, including aliases. These are
package matches across the full lock, not a target-filtered build result or
20 distinct vulnerabilities. The dependency-level disposition is:

| Pinned package | Advisory | Assessment for this Linux daemon |
| --- | --- | --- |
| `anstream 0.3.0` | RUSTSEC-2024-0404 / GHSA-2rxc-gjrp-vjhx | Invalid UTF-8 construction in ANSI stripping; patched 0.6.8. Lock edge is clap_builder. CLI formatting input path not fully validated. |
| `anyhow 1.0.70` | RUSTSEC-2026-0190 | Context plus `downcast_mut` borrow-rule unsoundness; patched 1.0.103. No direct scheduler use of that combination found. |
| `bytes 1.4.0` | RUSTSEC-2026-0007 / GHSA-434x-w66g-qw3r | `BytesMut::reserve` overflow; patched 1.11.1. Tokio dependency; a near-usize-limit reserve is required. A controllable overflow path was not established. |
| `enumflags2 0.7.6` | RUSTSEC-2023-0035 / GHSA-qvc4-78gw-pv8p | `make_bitflags!` can use invalid associated constants; patched 0.7.7. zbus/zvariant dependency; requires adversarial source-level macro input. |
| `mio 0.8.6` | RUSTSEC-2024-0019 / GHSA-r8w9-5wcg-vfj7 | Windows named-pipe tokens; patched 0.8.11. Excluded for Linux, and pinned Tokio predates the affected Tokio use described in the advisory. |
| `rand 0.8.5` | RUSTSEC-2026-0097 / GHSA-cq8v-f236-94qc | Custom logger recursively uses thread RNG during reseeding; patched 0.8.6. zbus dependency. No such scheduler logger implementation found; active features not resolved. |
| `rustix 0.37.6` | GHSA-c827-hfw6-qwvm | Linux raw directory iterator can grow memory after an I/O error; patched 0.37.25 in that branch. Scheduler scans use `std::fs`, not this API. Transitive directory-iterator use was not proven or excluded. The separate rustix 1.1.4 entry had no OSV match. |
| `shlex 1.1.0` | RUSTSEC-2024-0006 / GHSA-r7qv-8r2h-pg27 | Quoting API flaws; patched 1.3.0. Bindgen build dependency. Scheduler subprocesses use `Command`, not shell quoting. Bindgen's affected API use was not audited. |
| `tokio 1.27.0` | RUSTSEC-2025-0023 / GHSA-rr8g-9fpq-6wmg | Broadcast clone unsoundness with Send/non-Sync payload; fixes include 1.38.2. Scheduler's direct channels are mpsc, with a current-thread runtime. Transitive broadcast payloads were not fully audited. |
| `tracing-subscriber 0.3.16` | RUSTSEC-2025-0055 / GHSA-xwfj-jgwm-7wp5 | ANSI log injection; patched 0.3.20. Debug logging can include an untrusted D-Bus profile. Default log level is info and service output goes to journal; terminal-control interpretation depends on viewing mode. |
| `instant 0.1.12` | RUSTSEC-2024-0384 | Unmaintained, not a demonstrated vulnerability. Lock edge through fastrand. |
| `derivative 2.2.0` | RUSTSEC-2024-0388 | Unmaintained, not a demonstrated vulnerability. zbus macro dependency. |

The primary advisory records are reproducible as
`https://api.osv.dev/v1/vulns/<advisory-id>`, including the
[bytes advisory](https://api.osv.dev/v1/vulns/RUSTSEC-2026-0007),
[logging advisory](https://api.osv.dev/v1/vulns/RUSTSEC-2025-0055), and
[rustix advisory](https://api.osv.dev/v1/vulns/GHSA-c827-hfw6-qwvm).
The exact request shape used was:

```python
import json, tomllib, urllib.request
from pathlib import Path

packages = tomllib.loads(Path("Cargo.lock").read_text())["package"]
queries = [
    {"package": {"name": p["name"], "ecosystem": "crates.io"}, "version": p["version"]}
    for p in packages if p.get("source", "").startswith("registry+")
]
request = urllib.request.Request(
    "https://api.osv.dev/v1/querybatch",
    data=json.dumps({"queries": queries}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request) as response:
    results = json.load(response)["results"]
for query, result in zip(queries, results):
    if result.get("vulns"):
        print(query["package"]["name"], query["version"],
              [v["id"] for v in result["vulns"]])
```

This queried 238 entries for HEAD and 207 for `git show 2.0.2:Cargo.lock`.
All 20 returned advisory records were retrieved and read; alias duplicates
were not presented as independent findings. OSV results are date-sensitive.
`cargo --list` contained no `audit` command, so cargo audit was not run or
installed. No dependency update, target feature resolution, build-script
execution, dependency license sweep, or native-library advisory scan occurred.
Read-only package inspection found native PipeWire
`libpipewire-0.3-0t64:amd64 1.6.2-1ubuntu1.2`; that version was not treated as
covered by the Cargo query.

## License

The scheduler declares **MPL-2.0** in `daemon/Cargo.toml:7` and
`execsnoop/Cargo.toml:7`; the complete `LICENSE` is Mozilla Public License 2.0.
Source headers identify MPL-2.0. Its source/executable distribution conditions
and notice preservation are stated in `LICENSE:160-205`. Preserve the license
and covered-file source availability when redistributing a binary or modified
covered files. No scheduler source is vendored into this repository by this
review, and no binary is distributed.

The standalone extension has **GPL-3.0-or-later**, explicitly stated in
`extension.js:6-20`, with a GPLv3 LICENSE. Pop Shell also ships GPLv3 text and
GPL-3.0 notices (`LICENSE:1-5`, `debian/copyright:5-7`). The installed
execsnoop-bpfcc script identifies Apache-2.0 at `:17-18`. These are separate
components; do not describe the extension or BPF helper as MPL-2.0. Their
complete dependency-license obligations were not reviewed for redistribution.

## Required controls

1. Keep adoption blocked until D-Bus caller/method restrictions and the
   interface-lock/event-queue cycle are resolved and independently reviewed.
   State whether every process in the desktop account is trusted to set focus.
2. Disable execsnoop and PipeWire integration for the minimum trial, or obtain
   bounded event handling and an unprivileged, PID-validated PipeWire monitor.
   Pin a root-owned absolute helper path if BPF tracing is later enabled.
3. Resolve dependency advisories or justify target/API/feature exclusions;
   accept the unsigned-source boundary explicitly. Pin the full commit, lock,
   compiler, system inputs, and built hash; rebuild/re-review changed inputs.
4. Use an exact installation manifest and captured rollback baseline. Avoid
   recursive upstream uninstall over preexisting files, and plan workload
   restart/reboot for live priority restoration. Preserve diagnostic history.
5. Treat GNOME 50 source support as separate from runtime acceptance. Do not
   force the standalone 40–44 extension to load. Review Pop Shell's broader
   desktop changes before adopting it solely for focus integration.
6. Verify this modern kernel's available tuning interface and measure the
   intended CPU-load/responsiveness benefit. Keep refresh-rate positive.
   This daemon does not implement efficiency-core affinity or CPU quotas.

## Verification record

Completed: pinned scheduler clone and tag comparison; complete scheduler
runtime/configuration/packaging review; selected extension metadata and code
inspection; Pop Shell focus and lifecycle/install-path inspection; exact Git
commit/tag/release API provenance checks; lock SHA-256 and package/checksum
counts; two exact-version OSV batches and 20 advisory-record reads; dependency
lock-edge inspection and reachability qualifications; pinned zbus/Tokio
locking contract inspection; synthetic queue/lock reproduction with assertions
(exit 0); cargo-audit availability check; compiler/build-prerequisite check;
read-only kernel/path/installed PipeWire/BPF-script inspection; license review;
record-structure/evidence-reference and whitespace checks; scratch removal.

Record checks passed for all 13 required sections, the severity totals, 80
source-reference paths/ranges, six shell blocks (`bash -n`), and two Python
blocks (AST parsing). The model embedded in this record exited 0 and printed
`True 4 True False False`. OSV response-count and extension metadata/API
assertions passed. The final `git diff --no-index --check /dev/null` check
reported no whitespace errors; the post-cleanup absence check exited 0.

Build prerequisite checks: `rustc --version` returned
`rustc 1.98.1 (48a229cea 2026-09-01)`; `command -v clang` found nothing;
`pkg-config --modversion libpipewire-0.3` exited 1; dpkg-query confirmed missing
clang, libclang-dev, and libpipewire-0.3-dev. No build result is claimed.
All builds, if later authorized with prerequisites present, must use the
efficiency-core/low-weight wrapper documented above.

Intentionally not run: sudo; apt/dependency installation; Cargo build/test/run,
fetch, vendor, update, or audit; just/Makefile install or uninstall; scheduler
daemon or CLI execution; service start/reload/enable; extension build/install/
enable; D-Bus attack traffic; BPF attachment; stress/exhaustion tests; GNOME or
kernel-setting writes; npm workflow/verify; staging/commit. No root sandbox,
live rollback, reboot, GNOME 50.1 loading, CPU benefit, or full native-library/
Pop Shell security acceptance is claimed. This worker added only this record to the
repository, and `.local/system76-scheduler/` was removed.
