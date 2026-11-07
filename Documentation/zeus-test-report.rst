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

Rollback and recovered evidence
--------------------------------

After the user returned Zeus to Fastboot, product zeus and slot a were
confirmed again. The four rollback images passed their saved checksums.
All four restoration writes returned OKAY, and baseline recovery booted
with root ADB, kernel 5.10.269-gki-31259-g1d16d5feabd4 and slot _a.
Baseline UFS partitions and recovery ADB are verified working after rollback.
No slot-b or DLKM partition was written.

Pstore is empty and /proc/last_kmsg is absent. Read-only copies of the
16 MiB oops partition, the first 32 MiB of minidump and baseline runtime DT
were collected. The minidump contains the tested 6.6 kernel's boot log,
including the exact release and build ID. Raw evidence, extracted logs,
flash/rollback transcripts and checksums are saved under
out/waipio-zeus/evidence/attempt-1. Historical 5.10 logs in oops are not
used to diagnose the 6.6 failure.

The 6.6 log establishes these stages:

* UFS initializes the Samsung KLUEG8UHGC-B0E1 device and enumerates its LUNs
  and sda through sdf. This verifies discovery, not sustained storage I/O.
* Recovery init and the recovery process start; full recovery availability
  and ADB are not established.
* At 5.694 seconds the display commit thread faults at address 0x50.
  At 5.875 seconds the kernel panics. The call chain is
  rpmh_rsc_get_channel, rpmh_write_sleep_and_wake,
  sde_rsc_client_trigger_vote, sde_core_perf_crtc_update,
  sde_crtc_atomic_begin and drm_atomic_helper_commit_planes.

The display RPMh client remained under the RSC controller container after
multi-DRV migration. rpmh.c:get_rpmh_ctrlr() interprets the immediate
parent's driver data as struct rsc_drv; that data now belongs to drv@0.
Moving the client from disp_rsc to disp_rsc_drv0 matches the existing Cape
DT and fixes this invalid parent relationship. This change is committed;
its effect on hardware still needs a new approved recovery trial.

A separate USB BAM error is also confirmed: its reg property retained two
cells after the wrapper moved to two address and two size cells. DTC flags
the length and the boot log reports device 18000.qcom,usbbam with a missing
BAM memory resource. A separate commit expands the unchanged a704000/18000
range to four cells. No USB functionality was disabled.

Other observations remain tracked, not hidden: SPMI transaction warnings,
BCL probe errors, missing UFS CPU-group masks, and firmware fallback/deferred
probe messages. These require comparison and later testing; they are not
the fatal stack identified above.

Verified for 6.6: kernel reaches userspace, UFS discovery, recovery process
starts. Failed: display/RPMh commit and full recovery/ADB availability.
Unverified: UI/touch operation, charging/thermal, complete DSP startup,
audio, sensors, WLAN, Bluetooth, modem, GPU, camera, video and suspend/stability.
Cupid and Cape runtime remain unverified. The phone is left in the working
baseline recovery. No second deployment has been authorized or performed.

Prepared retry
---------------

The display RSC parent fix is 7d9bb1a98, and the USB BAM register encoding
fix is 17e54d169. Semantic checks reject the saved pre-fix DTs and pass all
ten corrected Waipio/Cape combinations. The final Zeus kernel/external
module build and all six image targets pass. Checks on DTBs extracted from
the actual vendor_boot image confirm both corrected bindings. Ramdisk
module dependencies and both DLKM images pass packaging checks.

The immutable retry images are in out/waipio-zeus/attempt2-images, with
SHA256SUMS, packaging-report.json and TEST-PLAN.txt. Their hashes and checks
are also recorded in waipio-validation-attempt2.json. Attempt-1 artifacts
and crash evidence remain preserved separately. The retry proposes the
same four slot-a partitions and recovery boot, using these new images;
it required explicit approval. The user subsequently approved and executed
that retry; its results are recorded below.

Attempt 2: recovery milestone reached
-------------------------------------

All six frozen retry-image checksums passed. Device/slot were rechecked
from baseline recovery and Fastboot, and the four approved slot-a writes
returned OKAY. Recovery enumerated with root ADB and kernel
6.6.144-android15-8-g3bfb6974dd86-dirty-4k. The selected DTB/DTBO indices
are 1/6, the model is Zeus, and SoC ID/revision are 457/2.2. The actual
runtime DT is saved with this attempt's evidence.

The user confirms that display looks correct and volume/power navigation
works. UFS enumerates normally; a read-only 4 MiB boot_a read is byte-equal
to the flashed image. This capture includes trailing dd statistics, excluded
from the comparison and recorded separately in ufs-read-check.json.
Recovery remains available with root ADB at 606.64 seconds uptime without
a kernel panic. Pstore is empty. Android has not been booted, and slot b
and both DLKM partitions remain unchanged.

Touch does not operate in the recovery UI according to the user. The FTS
driver probes, reads controller firmware information and exposes event7.
Two input captures contain no events, but the user confirmed the first was
idle and did not confirm tapping during the second window. Thus they do
not independently prove an IRQ or input-driver failure. The IRQ counter
reads one. Baseline touch functionality has not been tested in this session.

ADSP remains offline: loading reports segment outside memory range. The
installed adsp.mdt load segments span 0x3100000 bytes (49 MiB), exceeding
the snapshot's 0x2100000 (33 MiB) reservation. There is no battery power-supply
node, and recovery healthd reports no battery device. This blocks charging
and battery-temperature verification; it is consistent with ADSP's failed
startup but charging operation itself has not been established.

The working 5.10 runtime DT reserves ADSP at 0x9fd00000/0x3100000 and XBL
ramdump at 0xa6b80000/0x280000. f989a61e0 adapts c0421c0a6 to those inline
Waipio regions, preserving labels and all other carveouts. Firmware-aware
DT validation rejects the failed runtime layout and accepts the corrected
Waipio and Cape bases/combined trees. No firmware is added to the repository.

The USB BAM node now appears at its correct address, proving the register
encoding change took effect, but probe next rejects a missing qcom,bam-type.
6c5a107ba supplies DWC3_CTRL=0 as defined by the current driver. USB ADB
already works independently of this optional BAM probe.

Passed milestone: 6.6 recovery boot, root ADB, UFS discovery/read, visible
display and button navigation. Known failures: recovery touch, ADSP startup
and battery/charging reporting; optional USB BAM probe. Full thermal,
DSP/audio, sensors, WLAN, Bluetooth, modem, GPU, camera, video, suspend,
reboot and sustained stability remain unverified. Raw logs, DT and firmware
metadata are in out/waipio-zeus/evidence/attempt-2 with a checksum manifest.
The phone remains in attempt-2 recovery; no third deployment has occurred.
