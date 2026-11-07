.. SPDX-License-Identifier: GPL-2.0-only
.. Copyright (C) 2026 The LineageOS Project

Zeus hardware validation
========================

Latest verified milestone: attempt 5 has working 6.6 recovery, display/touch,
root ADB, UFS read, ADSP startup and idle charging telemetry. Full Android
boot is pending approval of the complete OTA described at the end of this
report. Cupid and Cape runtime remain unverified.

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

Attempt 5: approved deployment, recovery availability unresolved
-----------------------------------------------------------------

The user explicitly approved the frozen attempt-5 four-partition recovery
test. All six frozen image hashes and the four saved rollback image hashes
passed before deployment. Root recovery ADB confirmed Zeus serial 4feb552c,
slot _a, SoC 457 revision 2.2 and the running attempt-3 6.6 kernel. Pre-test
state, input/IRQ enumeration, dmesg and power-supply data were saved.

The first bootloader entry reported product zeus, but slot queries failed,
then other variables became unavailable. No partitions were written in
that state. A bootloader restart restored product zeus, current-slot a and
is-userspace no; all three were verified before proceeding. Each approved
boot_a, vendor_boot_a, dtbo_a and recovery_a write returned OKAY, as did
reboot recovery. Slot b, DLKM and userdata were not written.

Recovery ADB did not return within the initial 35-second wait. Later USB
discovery found neither ADB, Fastboot nor a Qualcomm endpoint. Screen state
is awaiting the user's observation. There is no post-test kernel log yet,
so a kernel panic, a startup hang and a USB-only failure are not distinguished.
Touch, corrected live supply voltage, ADSP and charging are not verified
for this candidate. No rollback or additional write has occurred.

Evidence and full flash transcript are under
out/waipio-zeus/evidence/attempt-5 with SHA256.json. The initial failure to
return ADB is recorded in result.json. Previous attempts and the working
5.10 baseline remain separate; this result supersedes the candidate's
earlier undeployed status. Further diagnosis requires device observation
and recovery of logs; no subsystem is disabled to bypass the failure.

Attempt 5 follow-up: working recovery, touch and ADB
---------------------------------------------------

The user confirms recovery is visible and touch navigation works. Root
ADB subsequently returned during the cable-reconnect investigation, at
approximately 426 seconds uptime on the same 6.6 boot and slot _a. The boot
log shows USB configured at 6.463 seconds, disconnected at 7.439 seconds,
then configured again at 426.784 seconds. This was not a failure to boot
recovery. The cause of the initial disconnect is not established and should
be checked during later USB/reboot testing; no speculative USB change was made.

The saved 293-line input capture contains event7 ABS contact positions,
tracking IDs and BTN_TOUCH down/up. The FTS IRQ counter rises from 1377 to
1569 across the capture. Live PM8008J L3 is enabled at 3304000 microvolts,
consistent with its restored 3.3--3.304 V limits. This verifies touch on the
audited candidate, rather than only on the 5.10 A/B baseline.

ADSP reaches running at 5.879 seconds and remains running at 612 seconds.
Battery reports Charging, health Good, capacity 62 percent and temperature
about 30.8--30.9 degrees C. This verifies telemetry, not charging rate or
thermal stress. A read-only 4 MiB boot_a read matches the frozen attempt-5
image exactly. USB BAM is bound; pstore is empty. Recovery has not mounted
userdata. The previously observed SPMI PMIC 0-05 probe warning remains.
Other DSPs/modem are offline in recovery and remain unverified.

Current milestone: recovery, display, touch, root ADB, UFS read, ADSP startup
and idle charging telemetry work on 6.6. Android boot and its subsystem tests
remain pending. The user requested a complete build for that test; it is
being prepared with the local g.sh setup and build zeus helper, including
ccache, for a separately reviewed OTA deployment. Existing recovery-test
approval does not authorize that OTA's writes or slot change.

Complete system candidate prepared
------------------------------------

The user requested a complete build for system testing and the local
g.sh/build zeus flow. That flow, including ccache, passed in 00:54:19
(Android build 54:16, 101673 Ninja steps). The wrapper's Telegram hook was
suppressed in this shell; source scripts were unchanged. Full source refs
and dirty-input state are in out/waipio-zeus/full-build.

The frozen full OTA is lineage-24.0-20261107-UNOFFICIAL-zeus.zip, 1844154954
bytes, SHA256 c2ad893abeff524f12322de9077b61bc08e409746bfbb29d136625d34259c9a1.
It is under out/waipio-zeus/full-build/deploy with TEST-PLAN.txt, checksum
and payload/image validation reports. waipio-system-candidate.json records
the exact artifact and checks. No complete OTA has been deployed yet.

All 33 payload partition hashes match the assembled target-files images.
The builder repacks boot/vendor_boot from target-files, so their final
payload images were independently inspected. The kernel bytes are identical
to the working attempt 5 kernel. All 10 applied DT combinations equal the
validated source outputs. Both Zeus bases retain the 120 regulator/40 fixed
reservation baseline checks. Recovery has 261 modules; the final vendor_boot
fragment has 90 early modules, with both PHYs loaded and all dependencies
present. The 79 system and 361 vendor filesystem modules match staging and
the running kernel's vermagic. First-stage fstab mounts both DLKMs.

The full payload adds system_dlkm, absent from the old 5.10 logical layout.
All 20 firmware images match exact payload-sized prefixes of the currently
installed slot-a partitions. Certificate, ZIP CRC, payload/metadata hashes,
full-update metadata and timestamps pass. No wipe/downgrade flag or
userdata/metadata payload is present. At 4296 seconds recovery uptime, ADSP
still runs, battery is Charging/Good at 68 percent and 29.1 C, AVDD remains
3.304 V, root ADB works and pstore is empty. This is idle observation, not
a thermal/load stress test.

The reviewed plan proposes eat with serial 4feb552c and its OUT pinned to
the one frozen ZIP. A/B installation targets slot b and automatically boots
Android. This broader operation requires new specific approval. The plan
provides a hardware-key/Fastboot path back to tested slot-a recovery and
retains actual inactive-slot boot/recovery readbacks plus the original
full 5.10 package. Virtual A/B snapshot merging means slot selection alone
is not a promise of full OS/application-data rollback. No factory reset or
format is proposed. Android and subsequent subsystem tests remain unverified.

System attempt 1: camera SMMU probe panic
----------------------------------------

The user explicitly approved the complete frozen OTA, slot-b installation
and automatic Android boot. Hash and device/slot checks passed immediately
before eat. The helper completed with exit status 0 and Total xfer 1.00x.
Android ADB did not appear. The user observed repeated Mi-logo/off cycles.
Fastboot subsequently confirmed product zeus, current-slot b, successful no,
unbootable no and retry-count 2 for b. The approved rescue selected slot a
and rebooted the known-working recovery, without flashing or wiping.
Recovery ADB returned after the user's USB reconnect.

Pstore is empty. Read-only minidump/oops copies and recovery logs are in
out/waipio-zeus/evidence/system-attempt-1. The changed minidump contains
several 6.6 boot records, including three with the same camera probe fault.
The camera build ID c61fdd956bb2ab9955e475cf68cc2e1c77b681df matches the
actual installed candidate module. Old oops records are not used to
diagnose this failure. Raw evidence, extracted boots and checksums remain
separate from earlier recovery failures.

The system reaches mounted OS/DLKM partitions and second-stage init/module
loading. At about 4.82--4.99 seconds, camera SMMU validation reports
Discard [0,0] versus [0xe0000000,0x800000]. Failure cleanup calls
gen_pool_destroy(NULL) via cam_smmu_release_cb; the kernel panics at
4.945/5.375 seconds in the saved boots. This is a kernel/DT probe failure,
not a CamX userspace-library resolution failure. Data decryption and a
complete Android boot are not established by these logs.

The existing 13942a96b camera DT migration removed the context-bank
iova-region-discard property but retained its IO-map counterpart. The
current driver still compares both values. f1ee6531e restores the Waipio
8 MiB discard hole and reserves it through iommu-addresses; the 6.6
cam_smmu_util_iommu_custom helper no longer reserves it dynamically. It
also restores the original pool's upper boundary: 0x10c00000 plus
0xee300000 ends at 0xfef00000. Waipio firmware/shared/QDSS ranges remain
unchanged. Cape's DT files are not altered.

Module commit 99a739b2776 separately guards shared_mem_pool during
teardown: the DT support flag can be set before a pool is allocated.
The camera feature and its validation remain enabled. The updated DT
checks reject the actual failed artifact and accept all ten corrected
Waipio/Cape combinations, including baseline supply/memory checks. This
adds camera-specific semantic coverage missing from the earlier audit;
compilation and existing-file migration history alone did not catch it.

A new complete build is being prepared with the same g.sh/build zeus
flow. Its new artifact needs separate review and specific approval before
another deployment. The original failed OTA remains frozen. The CamX
wrapper proposal was declined by the user; existing extraction behavior
and commit 55f365eb4 remain unchanged. Android subsystem tests remain
pending a successful system boot.

System candidate 2: camera fix built and packaged
------------------------------------------------

The corrected full build passed with g.sh/build zeus and ccache in 07:17
(17715 Ninja steps). The separate Cape kernel/module build passed in
178.740 seconds with 97 actions. Sources are recorded in
out/waipio-zeus/full-build-2/build-inputs.json and source-manifest.xml.
The camera module includes 99a739b2776; its packaged build ID is
a228a8fc5cb5ab96291e50252d3c153ca9cfb727, different from the failed OTA.

The independent frozen OTA is under out/waipio-zeus/full-build-2/deploy:
lineage-24.0-20261107-UNOFFICIAL-zeus.zip, 1844161094 bytes, SHA256
bc1ee1aad1bb59c32161d2753e80353e6152b678ce64989de05f0ed6484b1615.
waipio-system-candidate-2.json records the exact build and validation.
The previous failed candidate and crash evidence are retained separately.

All 33 payload image hashes and ZIP/payload metadata checks pass. All 20
firmware images still match installed slot a. All ten packaged, applied
DT combinations equal the independently compiled corrected source outputs;
camera discard/bounds checks pass. All six Cape combinations are unchanged
from the previous candidate. Both Zeus bases pass the same 120 regulator
and 40 fixed reservation comparisons. The kernel bytes equal the working
attempt 5 kernel. Recovery/vendor ramdisks contain 261/90 modules, and
system/vendor DLKM contain 79/361 modules. Module dependency/load lists,
all 440 filesystem module bytes/vermagic and both first-stage DLKM mounts
pass. These are build/package checks, not camera runtime verification.

Zeus remains in working slot-a recovery. Read-only USB checks confirm
root ADB, charging/Good at 76 percent and 29.5 C, ADSP running and empty
pstore. Metadata is unmounted; snapshot merge status is not established.
The prepared TEST-PLAN.txt proposes eat of this exact new OTA into slot b
with automatic Android boot and a Fastboot return to slot-a recovery if
needed. This new deployment awaits specific approval; no further writes,
slot changes or reboots have been performed. Android boot and subsystem
tests, plus Cupid/Cape runtime, remain unverified.

System attempt 2: installation complete, boot observation pending
----------------------------------------------------------------

The user approved the exact candidate 2 OTA and its slot-b install/automatic
Android boot, including return to slot-a recovery if necessary. The serial,
Zeus identity, recovery mode, slot a and ZIP checksum were verified before
eat. Installation completed at 2026-11-07 18:52:22 UTC with exit status 0
and Total xfer 1.00x. The complete transcript, approval, pre-install kernel
log and USB observations are in out/waipio-zeus/evidence/system-attempt-2.

Android ADB has not appeared after installation. No post-install kernel
log or boot-completed result is available yet; screen observation has been
requested. Successful installation does not establish successful Android
boot, and the camera fix is not runtime-verified. The approved fallback
requires Fastboot access to select physical slot a and boot its tested
recovery, then collect new minidump/pstore logs. No rescue slot change or
additional partition write has been performed at this point.

System attempt 2: watchdog resets recovered from valid dump sections
-------------------------------------------------------------------

The user reported Fastboot. Read-only getvar checks found product zeus,
current slot a, and slot b unsuccessful/unbootable with retry count zero.
The bootloader had already selected a; the approved recovery return used
only reboot recovery. Root ADB returned, with charging/Good, ADSP running
and empty pstore. No rescue partition flash or set_active was required.

Readbacks of boot_b, vendor_boot_b, dtbo_b and recovery_b exactly match
candidate 2. The new minidump contains five changed valid records with
Android log timestamps from 18:54:30 through 18:58:01 UTC on 2026-11-07.
Their hypervisor diagnostics report watchdog bites from VM 3 around
24.7--25.7 seconds. Current saved kernel logs have no panic and reach
F2FS data mounting and Android userspace. A full boot and credential
decryption remain unverified. The cause of the watchdog expiry is still
unresolved; a watchdog report alone does not identify the stalled code.

The sixth valid record is unchanged from attempt 1 and contains its old
camera panic/build ID. Raw string scanning also reads stale bytes in
unused portions of the 6 MiB dump slots. The initial unbounded derivatives
are retained under unbounded-strings-scan but superseded. Use the actual
header section offsets/sizes, dump-N/kernel.txt, decoded md_pmsg logs and
valid-dump-analysis.json. Raw captures, dump-age proof, image readback proof
and watchdog-excerpt.txt remain under the attempt-2 evidence directory.

Current logs separately show the v2 GPU probe rejected for missing chip ID
and a camera CPAS component bind failure with -EINVAL. 4c0b57cbd supplies
Waipio v1/v2 IDs 0x07030000/0x07030001 from the pinned 5.10 adreno-gpulist.h
and removes the obsolete GPU AOSS clock argument. Power tables and revision
compatibles remain intact. bdb05b328 rejects the candidate-2 GPU DT and
accepts all ten corrected combinations, with the six Cape trees unchanged.
These fixes are not yet GPU runtime verification or proof of watchdog cause.

Common-device bc8b7438 adds a temporary debug-build service gated to Zeus.
It saves a bounded post-fs-data kernel snapshot, watchdog bindings/module
state and relocation symbols, and retains informational console output.
This addresses console filtering of camera errors logged at KERN_INFO;
drivers and watchdog remain enabled. Existing user debug edits are intact.
A third complete build is being prepared. The user explicitly authorized
installing that described candidate after validation, without another
confirmation, with the tested slot-a recovery as the fallback.

A separate WLAN failure is recorded: CNSS requests qca6490/amss20.bin,
while the installed firmware has amss20.bin and m3.bin at the image root.
The current candidate does not change this path. Camera CPAS, WLAN and
the watchdog need further diagnosis; Android/Cupid/Cape runtime remain
unverified.

System candidate 3: GPU fix and scoped diagnostics
-------------------------------------------------

The complete g.sh/build zeus build passed with ccache in 00:07:13
(Android build 07:10, 17548 Ninja steps). The frozen full OTA is in
out/waipio-zeus/full-build-3/deploy, 1844158205 bytes, SHA256
2b85c426e3e234b430fbdd79d1c0a7c35a72793702c0c111f54e5563f3ed60c3.
It contains the GPU binding fix and Zeus-only debug service, with no
additional driver imports. The previous camera fixes remain included.

All 33 payload hashes, ZIP/payload metadata/certificate checks and 20
unchanged installed-firmware comparisons pass. All ten applied DTs match
the independently validated corrected sources; six Cape combinations are
unchanged. Baseline Zeus supplies/reservations pass. Recovery/early vendor
module counts remain 261/90, with 79/361 system/vendor DLKM modules, both
UFS PHYs, complete dependency/load lists and 440 matching module bytes and
vermagic checks. Kernel bytes match the working recovery. The actual final
vendor image contains the exact new diagnostic script and init file.
Candidate metadata and detailed image checks are recorded separately in
waipio-system-candidate-3.json and the frozen deployment directory.

The user explicitly requested installing this described candidate directly
after the build. Its checksum and Zeus recovery/slot-a identity were checked
again; eat was started with OUT pinned to the frozen candidate directory.
The installation transcript and boot monitor are under
out/waipio-zeus/evidence/system-attempt-3. Installation/boot results and
GPU/watchdog runtime behavior are pending at this preparation checkpoint.
