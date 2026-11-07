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
