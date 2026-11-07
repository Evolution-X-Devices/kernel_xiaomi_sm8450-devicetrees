.. SPDX-License-Identifier: GPL-2.0-only
.. Copyright (C) 2026 The LineageOS Project

Waipio on the Xiaomi 6.6 platform
================================

Scope and provenance
--------------------

Zeus is the first hardware target. Cupid is built but has no runtime
validation. Cape runtime behavior is likewise unverified. The first approved
USB recovery test and its outcome are recorded in zeus-test-report.rst.

Starting revisions, dirty paths and binary-diff SHA256 values are recorded
in waipio-baseline.json. The DT tree started clean: the previously reported
Mondrian edit was already committed. The power-key edit and the three dirty
sm8450-common files were preserved. Only the additional Waipio PHY load line
was staged from modules.load.vendor_boot. Baseline patches and detailed logs
are in /tmp/waipio-port on the development host.

The Cape import d2452eb5acadd1d7feac7cbc30030bcb86fbe9aa records KP 1.0
DT revision e0f68cedcf57. Missing Waipio DTs and their include closure are
snapshots of that same revision. Existing shared files were never replaced.
The display subtree is absent from that old DT revision; its missing
foundation is taken from Xiaomi 5.10 DT revision
13fe1ba65b42d44c6f501085a516454bfbb11335. That subtree was imported from
8b213c136573ee1f621ca9747eedd391c7f9fe62 by aaf9f794ece68b476a7b367aec7299c55c088712.
waipio-snapshots.json lists each imported path and revision. Snapshot commits
are separate from subsequent binding and Xiaomi adaptations.

The existing GCC import ca2c2d5e815c records msm-5.10 d27499aa23d2.
The existing Cape UFS PHY import 5c468339cd26 records msm-5.10 4f330bf60e44.
Neither import was rewritten. The Waipio PHY already exists in 6.6 and only
needs configuration, packaging and early module loading. No additional
multimedia driver snapshot is required.

Supported identities
--------------------

Enabled bases are limited to SM8450 ID 457::

    waipio.dtb       457 0x10000
    waipio-v2.dtb    457 0x20000

Zeus reports ID 457 revision 2.2 via /sys/devices/soc0, confirming v2.
Both revisions remain enabled for Zeus/Cupid compatibility; Cupid runtime
and silicon revision are unverified. The old board overlays also advertised
482 and 552, but no hardware evidence requires P/LTE variants for these
phones. Their initial snapshot files were removed in a scope follow-up,
and the overlay claims narrowed to the two enabled pairs. No reference-board
overlays are enabled. Zeus has board IDs <0x10008 0> and <0x03010008 3>,
Xiaomi board ID <1 0>. Cupid has board ID <0x10008 0>, Xiaomi board ID <2 0>.

The standard fdtoverlay tool uses root metadata to identify the inputs;
it does not copy overlay-root model/board/SoC metadata into the base root.
Inspect identities on both packaged inputs, and peripheral properties on
the applied tree. A combined tree retaining the base board ID <0 0> is
consistent with the existing Cape build behavior.

Binding migration review
------------------------

The complete Cape history affecting the imported base and included files
was considered, including later Xiaomi integration. Derived commits retain
the originating author, identify the source commit and carry a new Change-Id
and Assisted-by trailer. Hardware policy is distinguished from binding work.

* b17b17024: applicable; AOSS uses qcom,sm8450-aoss-qmp.
* 65b2cdf5c: applicable; LLCC uses qcom,sm8450-llcc and six bank/broadcast
  register ranges consumed by drivers/soc/qcom/llcc-qcom.c.
* 64a7ddf61: applicable; RPMh uses qcom,sm8450-rpmh-clk and its XO input.
  Included with the RSC adaptation; supported by drivers/clk/qcom/clk-rpmh.c.
* ee47c7fb0: already present in the shared waipio-clock.dtsi; preserved.
* 49a8d6f51: applicable; apps DRV2 and display DRV0 get child/channel nodes.
  rpmh-rsc.c requires qcom,drv-count. Regulators reference apps_rsc_drv2.
* 64c58ed26: applicable; PMIC GLINK uses the existing qti-pmic-glink binding.
* e58decd6f: applicable; migrate relevant AOSS consumers to qcom,qmp.
  Keep qmp_aop for mailbox consumers such as the gen7 GMU, whose driver
  still calls mbox_request_channel().
* c4da53237: applicable; consolidate sleep statistics into rpmh-stats-v3,
  supported by drivers/soc/qcom/qcom_stats.c.
* 13942a96b: applicable to base, USB and display; use iommu-addresses.
* 1e5d22b96: applicable; remove legacy FastRPC compute/RPMSG descriptions
  and use the migrated DSP context-bank descriptions. CDSP/SLPI edge
  labels are added without changing their resources.
* 46f2a3bfa: ADSP glink_edge naming is already present in the Waipio
  snapshot and shared audio; do not rename it a second time.

Other included-file migrations cover PM8350 ADC channel encodings, upstream
QUP, SMMU IOVA width, SDHC reset/XO, RNG, cache compatibles, CPUCP SCMI,
remoteproc message queues, PCIe supply/clock consumer names and clock-array
sizes. The PCIe supplies retain Waipio phandles and current limits; the
current pci-msm driver requires a rate and suppressibility cell per clock.
The shared QUP, clocks, SMMU, PMICs and thermal overlay retain their existing
6.6 migrations. Remoteproc and TLMM already use Waipio compatibles.

Cape's UFS multilevel-clock revert is inapplicable: Waipio already uses
300 MHz without those multilevel properties. Cape-specific UFS PHY and
GPU data are not substituted. The v2 CAMCC/GPUCC compatibles and
Adreno730v2/gen7-0-1 power data remain in waipio-v2.dtsi and
waipio-v2-gpu.dtsi. Both clock drivers explicitly match the v2 compatibles;
the graphics module has gen7-0-0 and gen7-0-1 core data.

Cape SPSS disabling was rejected as hardware policy; a follow-up restores
the original Waipio status. The TOF pinctrl migration is required because
the Zeus/Cupid board files already reference PM8350B GPIO2; its provider and ADC
mux selection follow b673568ce. Thor UART definitions
are omitted from Waipio. The Xiaomi UART states for Zeus/Cupid are derived
from 40263fb53; Zeus panel VCI from 32eff8a18. The legacy reference ramoops
allocation is removed to avoid a second allocation alongside Xiaomi's
reserved ramoops area. Xiaomi uses USB2; USB hardware-LPM handling follows
the existing platform migration.

Multimedia integration follows 808d1f4c9 and f781400c0: base descriptions
include audio, Waipio camera, display, DSP, GPU, video, EVA, MMRM and synx;
board overlays include their audio, camera sensor and panel descriptions.
v2 selects v2 GPU and MMRM data. The kernel build therefore does not need
separate techpack DT merging. Existing module targets already provide the
Waipio multimedia drivers; the audio target_product flag must be set to
the selected device (zeus for this validation).

Reproducing checks
------------------

From the Android source root::

    python3 kernel/platform/kernel-6.6/vendor/xiaomi/sm8450-devicetrees/tools/validate-waipio.py --out /tmp/waipio-dt
    source build/envsetup.sh
    breakfast zeus
    m bootimage vendorbootimage recoveryimage dtboimage vendor_dlkmimage system_dlkmimage

The DT validator compiles all three bases and eight overlays and applies all
four intended Waipio combinations plus six Cape combinations. Compiler
warnings are retained per input. Applied trees also check display RPMh
client ownership and USB BAM register cell encoding against the driver
contracts. These checks reject both saved broken artifacts from attempt 1
and pass all ten fixed Waipio/Cape combinations. They do not claim
dt-schema compliance.

The standalone kernel distribution command is run from kernel/platform/kernel-6.6::

    ./tools/bazel run --experimental_convenience_symlinks=ignore --cpu=arm64 --//vendor/xiaomi/sm8450-modules/qcom/opensource/audio-kernel:target_product=zeus //vendor/xiaomi/sm8450-build:sm8450_dist -- --destdir=/home/arian/android/lineage-24/out/waipio-zeus/dist

When building directly into kernel/platform/kernel-6.6/out, create its
standard .out-dir marker so Android's source finder skips Bazel's sandbox
symlinks. The normal Android build keeps its Bazel output under Android out.

Validation and hardware status
------------------------------

All three bases and eight overlays compile, and all ten matching overlay
applications pass. Inspection resolves supply and memory-region phandles
and confirms base/v2 camera/GPU clock and GPU-core selections. Rebuilding
Cape and all six existing overlays from the starting revision yields
byte-identical DTB/DTBO binaries. No shared pre-existing SoC file changed.

The standalone kernel/external-module distribution build passed (1032
actions). Its distribution contains the three bases, eight overlays and both
UFS PHY modules. All six Android images built successfully. waipio-validation.json records
image hashes, packaged DT identities and module dependency checks. Recovery
contains 261 modules and the vendor DLKM ramdisk 348; both include and load
both UFS PHYs. The system_dlkm and vendor_dlkm filesystem images contain
79 and 361 modules respectively, all byte-identical to staging and with
all dependencies present across the two partitions.

USB baseline on 2026-11-07: Zeus serial 4feb552c, model 2201122G, slot _a,
firmware fingerprint Xiaomi/zeus_global/zeus:15/AQ3A.250226.002/OS3.0.4.0.VLBMIXM:user/release-keys,
kernel 5.10.269-gki-31259-g1d16d5feabd4, built 2026-10-30 22:32:05 CET.
The shell is unprivileged, ro.debuggable=0, verified boot state orange;
Direct DT identity, dmesg and pstore reads are denied. Sysfs reports ID
457 revision 2.2; boot properties report DTB index 10 and DTBO index 87. Recent userspace logs were
collected separately; no baseline kernel failure diagnosis is possible
from those restricted reads alone.

Pre-port local images are preserved in out/waipio-zeus/pre-port-images,
with SHA256 manifest. The backed-up boot kernel release and build time
match the running baseline; these are local build outputs, not partition
readbacks. Recovery has header v4 and no kernel, so fastboot boot of
recovery.img alone is not an appropriate test.

First proposed hardware test requires separately approved writes of the
matching boot_a, vendor_boot_a, dtbo_a and recovery_a, then recovery boot.
Do not write either DLKM partition or boot Android for that first test.
Inspect the final packaged recovery module dependencies before approval.
Keep the original slot _a selected. To recover, enter bootloader using the
hardware keys and restore those same four _a partitions from the pre-port
images, then reboot. Slot _b remains untouched. Exact artifact hashes must
be supplied with the approval request. No such operation is authorized by
USB attachment.

The first recovery attempt panicked in display RPMh. After the binding fix,
the second approved attempt reached 6.6 recovery with root ADB, UFS reads,
visible display and working buttons. Touch remains nonfunctional in recovery.
The third approved recovery trial confirms ADSP startup and battery/charging
telemetry after the firmware-sized memory fix. Full thermal, DSP/audio, sensors, WLAN, Bluetooth,
modem, GPU, camera, video, suspend and sustained stability are unverified.
See zeus-test-report.rst for evidence and pending fixes. Android testing
also requires matching DLKM images and explicit deployment approval.

Image integration also requires two additive miuicamera-cupid policy fixes:
exclude app-only policy from recovery, where the app domain lacks Android
attributes, and restrict nonsecure DSP grants to read/ioctl while removing
the forbidden secure-device grant. The selected Qualcomm neverallows are
unchanged. Android camera behavior through the existing HAL binder path
needs explicit runtime testing; the previous direct-open permissions are
not compatible with that policy. This is a separately recorded build
integration dependency, not evidence of camera functionality.

Both separate-overlay and combined-output platform-map paths were checked.
Combined outputs filter overlays by SoC family, avoiding unsupported Cape
and Waipio cross-pairings. Other platforms retain their default behavior.

Frozen test artifacts and exact commands are in
out/waipio-zeus/test-images/TEST-PLAN.txt, with SHA256SUMS and the packaging
report. The first operation was explicitly approved and executed; recovery/ADB
did not appear. Rollback completed; the second approved recovery attempt
subsequently reached working 6.6 recovery.
An exported additive patch series and index are under
out/waipio-zeus/patches and out/waipio-zeus/commit-series.txt.
The final kernel is 6.6.144-android15-8-g3bfb6974dd86-dirty-4k; dirty marks
the preserved, pre-existing power-key edit. Recovered minidump logs identify
a display/RPMh parent-binding fault; its fix passed the second recovery
trial. The ADSP memory and USB BAM type fixes passed the third recovery trial.
Touch still produces no contact interrupts; baseline recovery comparison
is the next prepared diagnostic.

The Cape regression build also passed with audio target_product=mondrian
(135 executed actions, 135.8 seconds), producing out/waipio-cape/dist.
This verifies compilation and packaging, not Cape runtime operation.

The validator accepts --adsp-metadata pointing to the installed adsp.mdt.
It computes the loadable ELF32 image span, excluding MDT hash segments,
and checks the remoteproc memory-region capacity. The Zeus firmware needs
49 MiB; the previous 33 MiB reservation is rejected. The metadata stays in
local test evidence and is not imported into the source tree.
