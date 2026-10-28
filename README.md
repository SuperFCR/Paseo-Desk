# PocketRig

**English** | [简体中文](README.zh-CN.md)

**Your workstation, in your pocket.** Drive the always-on computer at home from your phone: the workstation stays online 24/7, and experiment results from your GPU nodes show up right on your phone.

PocketRig turns one always-on computer (Windows + WSL2, native Linux, or macOS) into your personal AI coding rig. Your phone and Mac connect over [Tailscale](https://tailscale.com) to **your own** [Paseo](https://paseo.sh) instance on the workstation, which drives Claude Code / Codex. Heavy work such as training and inference is submitted over SSH to GPU / compute nodes; when a job finishes, only small results come back to the workstation, ready to view on your phone. Start with just yourself, and extend it to family or a small team when you need to.

## See it in 4 minutes

[![PocketRig highlights (click to download the full promo video)](docs/promo/pocketrig-highlights.gif)](docs/promo/pocketrig-promo.mp4)

The animation above loops the highlights of the promo video right in the README. For the full version, [download the promo MP4](docs/promo/pocketrig-promo.mp4) (4:05, 1080p, music only, ~17 MB; on-screen text is in Chinese) · [storyboard and source](docs/promo/README.md) · [30-second clip: start on the phone, continue on the Mac](https://paseo-desk-demo.chic-alder-0364.chatgpt.site). All visuals are rebuilt in code; accounts, hosts, addresses, jobs and metrics are fictional.

## Two highlights

| Online 24/7 | Results on your phone |
| --- | --- |
| Each instance is managed by systemd / launchd and starts at boot; a Windows scheduled task keeps WSL alive. Lock your phone, close your Mac, quit the terminal: the session and the agent keep running on the workstation. | Heavy compute stays on the GPU node. When a job finishes, only a few MB of metrics, curves and log summaries are pulled back to the workstation. Open the same Paseo session on your phone to read them and send the next instruction. |

## Let an agent do the setup: Skills

Every part of this repository is packaged as an [Agent Skill](skills/README.md). Once installed, just tell Claude Code / Codex things like "set up this computer as a PocketRig workstation" or "my phone can't reach Paseo, please check". The agent follows the steps and pauses for your confirmation before sudo, network changes or reboots.

```text
/plugin install pocketrig --marketplace SuperFCR/PocketRig
```

On older Claude Code versions, use two steps: `/plugin marketplace add SuperFCR/PocketRig`, then `/plugin install pocketrig@pocketrig`. For Codex or other tools: `./skills/install.sh --codex` (or `--target <dir>`).

| Skill | What it does |
| --- | --- |
| [pocketrig-setup](skills/pocketrig-setup/SKILL.md) | Single-user start: install the shared parts and create your own Paseo instance |
| [pocketrig-always-on](skills/pocketrig-always-on/SKILL.md) | Online 24/7: no sleep, WSL never reclaimed, start at boot, cold-boot acceptance |
| [pocketrig-connect](skills/pocketrig-connect/SKILL.md) | Connect phone and Mac over Tailscale and verify session hand-off |
| [remote-compute](skills/remote-compute/SKILL.md) | Submit node jobs, check status, pull back small results as a phone-friendly summary |
| [pocketrig-doctor](skills/pocketrig-doctor/SKILL.md) | Layer-by-layer read-only diagnosis and acceptance |
| [pocketrig-team](skills/pocketrig-team/SKILL.md) | Extend to family or a small team: add members, reset passwords, deactivate |

The skills and detailed docs are currently written in Chinese; agents can follow them in any language.

## How it works

![Architecture](docs/architecture.svg)

```text
Phone / Mac (Paseo app or web)
        │ Tailscale private network: no public ports, only your own devices
Always-on workstation: your Paseo instance (systemd / launchd, online 24/7)
        │ runs Claude Code / Codex as your UID (shared install, via wrapper scripts)
        │ your own ~/.ssh config
GPU / compute node: data, models, training and full artifacts; only small results come back
```

## Quick start (just you)

Prefer not to do it by hand? Install the plugin above and let the agent run `pocketrig-setup` → `pocketrig-always-on` → `pocketrig-connect`. Manual steps (Linux / WSL; for macOS see the [platform guide](docs/platforms.md)):

1. Install the shared parts and create your own instance:
   ```bash
   git clone https://github.com/SuperFCR/PocketRig.git
   cd PocketRig
   sudo ./linux/install.sh --install-node 24.22.1 --install-packages   # pick the version you need
   sudo paseo-user add "$USER" 6767
   claude auth login && codex login                                    # sign in with your own accounts
   ```
2. Keep it running: on WSL, register the keep-alive task on the Windows side (it also maintains the Tailscale port forwarding), see section 3 of the [admin guide](docs/admin-guide.md); on native Linux / macOS, let Paseo listen on the local Tailscale address.
3. Sign in to Tailscale on your phone and Mac, add a host in Paseo (`<WS_IP>:6767`, Use SSL off, password in `~/.paseo/client.env`), and complete your first task with the [user guide](docs/user-guide.md).
4. Compute nodes: configure them in your own `~/.ssh/config`, then use [remote-compute](skills/remote-compute/SKILL.md) to submit jobs and bring results back to your phone.

Before relying on it, go through the [acceptance checklist](docs/acceptance-checklist.md).

## Extending to family or a small team

The same workstation can give each person a separate system user and Paseo instance (`sudo paseo-user add alice 6767`, `sudo paseo-user add bob 6768`), authorize Tailscale ports per person, and hand over connection details privately with the [handover template](templates/handover.md). See [pocketrig-team](skills/pocketrig-team/SKILL.md) and the [admin guide](docs/admin-guide.md).

| Item | Arrangement | Boundary |
| --- | --- | --- |
| Node / Paseo / Claude Code / Codex programs | Shared install, maintained by root | Read-only and executable for regular users |
| Paseo, Claude Code, Codex processes | Per person | systemd / launchd run them as the real UID |
| Projects, sessions, config, SSH keys | Per person | Private HOME (700), credential files 600 |
| Paseo connection password | Per person | Randomly generated, readable only in your own `~/.paseo/client.env` |
| Model account sign-in | Per person | Each person runs `claude auth login` / `codex login`; no copying of others' credentials |
| Network, proxy, CPU, memory, disk | Shared host | Add per-user limits when needed |

Isolation relies on system UIDs and file permissions and is **meant for small teams that trust each other**: root/sudo admins, the host administrator and the shared network are all inside the trust boundary. It is not container- or VM-grade isolation against malicious tenants.

## Repository layout

```text
skills/                Agent Skills (setup, always-on, connect, remote compute, doctor, team) + install.sh
.claude-plugin/        Claude Code plugin and marketplace manifests
linux/                 Shared workstation parts (installed by root)
  install.sh           Installs wrappers, systemd template and admin tools; optionally Node and the three npm packages
  bin/                 claude, codex, paseo entry points (pre-launch checks + pass-through)
  sbin/paseo-user      add / reset-password / remove / list per-user instances
  systemd/paseo@.service
  share/               Workstation policy + sync script for each user's CLAUDE.md / AGENTS.md
windows/               Port forwarding and keep-alive task when Tailscale runs on Windows and Paseo in WSL
macos/                 launchd template for per-user instances on macOS
optional/egress-proxy/ Optional: transparent egress gateway for all users (mihomo TUN + nftables)
templates/             SSH config, Tailscale ACL and handover templates
docs/                  Design, deployment, user guide, acceptance, troubleshooting; promo/ video and source, demo/ 30-second clip
tests/                 Install, runtime and skills checks that need no real users, services or models
```

## Documentation (Chinese)

- [Skills overview](skills/README.md): purpose, typical requests and installation of each skill
- [Design](docs/design.md): isolation boundaries, task flow, usage accounting, staged rollout
- [Deployment by host platform](docs/platforms.md): Windows + WSL2 / native Linux / macOS
- [Admin guide](docs/admin-guide.md): install, add/remove users, Windows forwarding, Tailscale authorization, keep-alive
- [User guide](docs/user-guide.md): connecting, first task, remote compute, pulling results, web tunnels
- [iPhone: Tailscale built into Shadowrocket](docs/ios-shadowrocket.md): optional way to join the tailnet (verified on a real iPhone)
- [Acceptance checklist](docs/acceptance-checklist.md) · [Troubleshooting](docs/troubleshooting.md) · [Validation record](docs/validation.md)
- [Optional: egress gateway module](docs/egress-proxy.md)
- [Promo storyboard and source](docs/promo/README.md) · [Contributing](CONTRIBUTING.md)

## Tested environment

The reference deployment runs on Windows + WSL2. The scripts in this repository have static checks and simulated tests in temporary directories, but a complete deployment from a blank system has not been accepted yet. Native Linux and macOS still need on-device acceptance; see the [validation record](docs/validation.md) and the [platform guide](docs/platforms.md). Skills and plugin manifests pass structural tests and `claude plugin validate`; skill-driven end-to-end deployment also needs acceptance on test devices.

Reference versions: Paseo 0.13.2, Node 24, Codex 0.164, Claude Code 2.1.308, Windows 11 + WSL2 (Ubuntu, systemd enabled, NAT networking) + Tailscale for Windows. The installer pins Paseo 0.13.2 by default (`PW_PASEO_VERSION`) because `paseo-user` uses an internal module path to hash passwords. Re-verify after upgrading; if the path changes, members can run `paseo daemon set-password` in their own terminal instead.

## Usage notes

- Everyone should use model accounts they are entitled to (personal subscription, team/enterprise seat, or API key) and follow the terms of Anthropic, OpenAI and other providers, including their supported-region policies. This project does not provide or encourage sharing sign-in credentials or circumventing provider restrictions.
- Tailscale only connects your own devices; it is not a proxy. The optional egress gateway module is a generic network egress control tool; you are responsible for complying with local laws and provider terms.
- This project is not affiliated with Paseo, Tailscale, Anthropic or OpenAI.

## Name

This project was formerly called Paseo Desk and was renamed PocketRig on 2026-10-28; the old `SuperFCR/Paseo-Desk` address redirects to the new repository. System install paths and service names (`paseo-user`, `paseo@<user>`, `/etc/paseo-workstation`) are unchanged, so existing workstations need no migration.

## License

[MIT](LICENSE)
