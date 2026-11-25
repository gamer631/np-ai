# NP.ai OS Platform Matrix

**Status:** Candidate choices; final selection follows a working technical spike.

| Area | Desktop track | Mobile track | Shared contract |
|---|---|---|---|
| Kernel | Upstream Linux | Android kernel/common + device vendor tree | None |
| Base | Maintained Linux distribution/image | AOSP | Release policy |
| Display/UI | Wayland + established desktop stack | Android framework / SystemUI integration | Design system and accessibility principles |
| Shell | NP Shell | NP Launcher | User experience language |
| System integration | D-Bus, desktop portals, systemd | Binder, Android services and intents | Typed capability model |
| Application ecosystem | Existing Linux desktop apps; Flatpak where appropriate | Existing Android apps / APK ecosystem | Developer documentation |
| Security | Linux users/groups, namespaces, LSM, portals, sandboxing | SELinux, verified boot, app sandbox, permissions, Keystore | Threat model and privacy policy |
| AI runtime | Local inference where hardware allows; remote providers by user choice | On-device runtime where supported; remote providers by user choice | NP Intelligence API |
| Updates | Signed atomic image updates | Signed OTA | Signed metadata and release gates |
| Languages | Nepali and English | Nepali and English | Localization catalog |

## Candidate desktop base

Evaluate a maintained, image-oriented Linux base such as Fedora Atomic variants or another distribution with reliable update/rollback mechanics, active security maintenance and hardware coverage. Select only after a prototype verifies graphics, Wi-Fi, suspend/resume, audio, accessibility, packaging and recovery.

Do not promise a custom distribution before the image build, signing, mirror, update and support lifecycle are maintainable.

## Candidate mobile base

Use AOSP, initially targeting one reference device with:
- available and legally usable device trees/vendor binaries;
- documented bootloader unlock and recovery procedure;
- a maintained kernel/vendor baseline;
- working display, touch, modem, Wi-Fi, Bluetooth, camera, audio, sensors and power management;
- a feasible signing and OTA path.

A generic AOSP build is not a phone-ready product. Device compatibility is a major engineering program and must be tracked per exact model and revision.

## Shared code strategy

Share stable contracts, policy semantics, localization, design tokens, protocol schemas, test vectors and selected business logic. Do not force a single UI framework or privileged service implementation across Linux and Android where native platform mechanisms are safer.

## Decision gates

1. Desktop base selected after bootable image and update/recovery spike.
2. Mobile reference device selected after hardware and bootloader feasibility audit.
3. Shared API frozen only after one real desktop vertical slice and one mobile proof of concept.
4. Additional devices and distributions added only when automated build and release coverage exists.
