.. SPDX-License-Identifier: GPL-2.0-only
.. Copyright (C) 2026 The LineageOS Project

Zeus hardware validation
========================

Attempt 1: recovery, 2026-11-07
-------------------------------

User explicitly approved the frozen four-partition recovery test after
review of test-images/TEST-PLAN.txt. Before deployment, all six frozen
image SHA256 checks passed. ADB confirmed serial 4feb552c, product zeus,
slot _a, SoC ID 457 revision 2.2, and the baseline 5.10.269 kernel.
Fastboot independently confirmed product zeus and current-slot a.

The boot_a, vendor_boot_a, dtbo_a and recovery_a writes all returned OKAY.
Fastboot accepted reboot recovery. No DLKM or slot-b partition was written.
The flash transcript is /tmp/waipio-port/zeus-flash.log.

Recovery ADB did not appear within the initial 30-second wait. Repeated
USB discovery over the following minutes found neither ADB, Fastboot nor
a Qualcomm USB endpoint. Screen state is awaiting the user's observation.
No shell or kernel log was available, so the failure cannot yet be assigned
to kernel startup, UFS, recovery init, display or USB. A successful recovery
boot is NOT established. No Android boot was requested.

The user was instructed to return the phone to Fastboot with Power plus
Volume Down for the prepared rollback. All four saved rollback image hashes
were rechecked and match pre-port-images/manifest.json. Restoration remains
pending the device reappearing in Fastboot; it must not be reported as done.
The saved boot kernel release/build time match the original running device,
but the backups are local build artifacts, not partition readbacks.

Verified: device identity, frozen artifacts and four successful writes.
Failed milestone: recovery/ADB availability.
Unverified: UFS access, recovery UI, touch, display, charging/thermal, DSP,
audio, sensors, WLAN, Bluetooth, modem, GPU, camera, video and suspend/stability.
Cupid and Cape runtime are unverified. Build and DT validation results remain
as recorded in waipio-port.rst and waipio-validation.json.

Next evidence: regain Fastboot, restore the baseline images, and attempt
baseline recovery to retrieve pstore or persistent crash logs. Do not apply
speculative feature disabling to hide this failure.
