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

Prepared ADSP recovery retry
----------------------------

All six images rebuild successfully with f989a61e0 and 6c5a107ba. The actual
packaged base DTs pass the firmware-size, nonoverlapping ADSP/XBL reservation
and USB BAM controller-type checks. All ten matching overlays apply.
Ramdisk and filesystem-image module dependency checks pass. Exact hashes
and checks are in waipio-validation-attempt3.json and the immutable
out/waipio-zeus/attempt3-images directory, alongside TEST-PLAN.txt.

This retry targeted ADSP startup and battery/charging reporting and did
not claim a touchscreen fix. The user subsequently approved its four
slot-a writes and recovery reboot; the results follow.

Attempt 3: ADSP and battery reporting restored
----------------------------------------------

The user approved the attempt-3 image set. All checksums passed, and Zeus
product/serial/slot were rechecked before the four slot-a writes. All writes
and recovery reboot returned OKAY. The ADB reboot-to-bootloader command
exceeded its 20-second host timeout, but Fastboot appeared and identity was
verified before proceeding. This is a slow transition, not a lost device.

Recovery returns with root ADB and the same 6.6 kernel on slot _a. The live
DT passes the RPMh, USB register and firmware-sized ADSP reservation checks.
ADSP remoteproc reaches running at about 6.3 seconds, with no segment-outside-
range error. Battery, USB and wireless power-supply nodes appear; battery
health reports Good and status Charging. USB reports online. Capacity rises
from 41 to 42 percent during observation, and reported battery temperature
ranges from 30.1 down to 29.4 degrees C. ADSP and charging reporting remain
available at 1041.98 seconds uptime without a panic; pstore is empty.
This verifies idle telemetry/charging indication, not charging-rate or
thermal-stress behavior. USB BAM now has its driver bound successfully.
Other DSPs/modem remain offline in recovery and are not runtime-validated.

The user confirms recovery remains visible. A coordinated 35-second input
capture while the user was at the phone produces device headers only,
with no input events. The FTS IRQ counter stays at 2 before and after the
capture. GPIO20/reset is high and GPIO21/IRQ is input/high. The controller
responds during initialization and to charger-mode commands, but contacts
do not produce new interrupts. Generic IRQ debugfs is not enabled; mounting
the temporary debugfs interface provided GPIO state only. No userdata
filesystem was mounted for these diagnostics.

The mode_active sysfs shadow is zero, but the FOD-aware mode handler does
not populate that shadow as the ordinary branch does. It is not proof that
hardware scanning is disabled. No raw touch commands or firmware writes
were used to work around the failure.

The supplied Diting patches address real but separate defects: FTS uses a
hard-coded GPIO only for HARDWARE_PROJECT_L12=10, and Goodix checks gpio
instead of ret after requesting its ID GPIO. Diting's combined touch node
provides goodix,ts-id-gpio. Zeus is HARDWARE_PROJECT_L2=1 and uses FTS, so
neither identification path explains this failure. Those patches have not
been applied as a speculative Zeus fix. The existing user power-key and
device-tree edits remain untouched.

A reversible A/B plan was prepared at
out/waipio-zeus/touch-ab-test/TEST-PLAN.txt with both exact image sets in
images.json. The user subsequently approved that sequence; its results follow.

Current state: attempt-3 recovery with root ADB, running ADSP, visible UI,
working button navigation and charging telemetry. Touch remains failed.
Android, full audio/sensors/radios, GPU/camera/video, suspend/resume and
long-duration stability remain unverified. Evidence is preserved under
out/waipio-zeus/evidence/attempt-3 with SHA256.json.

Confirmed touch A/B and board audit
-----------------------------------

The first baseline input capture was inconclusive because the user was
away. The same approved A/B sequence was repeated with the user at Zeus.
In 5.10 baseline recovery the user explicitly confirms touch works. The
coordinated 15-second capture contains 98 lines including ABS contact and
BTN_TOUCH events, and the FTS IRQ count rises from 3 to 56. The controller
reports the same firmware release as on 6.6. This establishes a 6.6 touch
regression rather than an unverified baseline problem.

The four approved attempt-3 slot-a images were restored afterward. Root
ADB confirms 6.6 recovery, running ADSP and Charging status. Fastboot product
and slot were checked before writes. One bootloader entry did not expose
product/slot variables; restarting bootloader restored them, and no writes
were made until identity was established. No Android/DLKM or slot-b write
was performed. Evidence, active contact trace and flash transcripts are
under out/waipio-zeus/evidence/touch-ab.

Zeus touch AVDD references PM8008J L3. The generic imported constraints
limited it to 1.8 V, while the working runtime DT specifies 3.3--3.304 V
with BOB as its upstream supply. The 6.6 log confirms the regulator lowered
the rail. Xiaomi source aef1e9aed restores this and the other PM8008J
constraints; eea5f4bd0 ports it without driver changes. This is a concrete
DT error consistent with probing without contact interrupts, but its
hardware fix is not yet verified.

The attempt-4 images containing that rail fix built and passed packaging
checks, but were held undeployed when the user requested a broader audit.
The ensuing 76-commit/112-file audit restored 13 additional Xiaomi source
adaptations, recorded in waipio-xiaomi-audit.json. Further artifacts must
include that complete series and require their own specific deployment
approval. The earlier attempt-4 test plan does not authorize deployment.

Latest verified state: 6.6 attempt-3 recovery with visible display, buttons,
root ADB, UFS read, ADSP startup and idle charging telemetry. Touch works
in the 5.10 A/B baseline and fails in attempt-3 6.6. No corrected-rail
runtime result exists yet. Android, audio/sensors/radios, GPU/camera/video,
suspend/resume and sustained stability remain unverified. Cupid and Cape
runtime behavior remain explicitly unverified.

Prepared audited recovery candidate
-----------------------------------

Attempt-5 is frozen at out/waipio-zeus/attempt5-images and has not been
deployed. The Zeus kernel/external-module/six-image build and separate
Cape/Mondrian build pass. Actual packaged DTs match all ten validated
source combinations; both Zeus bases match 120 baseline regulators and
40 fixed reservations. Ramdisk and filesystem module dependency/byte
checks pass. See waipio-validation-attempt5.json for hashes and provenance.

TEST-PLAN.txt requests exactly the four slot-a recovery-test writes,
then recovery boot, with serial/product/slot verification before writes.
It includes a checksum-verified four-image 5.10 recovery rollback. No
approval for this new image set has been given. The next runtime result
must distinguish corrected supply voltage, touch contacts/IRQ operation,
and preserved ADSP/charging behavior from build-only expectations.
