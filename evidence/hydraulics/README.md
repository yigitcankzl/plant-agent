# Liquid hydraulics screening

The control-valve calculation uses the simplified ISA/IEC liquid equation
`Cv = Q(US gpm) × sqrt(SG / ΔP(psi))`, with SG relative to water at 60 °F.
`Cv(US) = 1.156 Kv`. Equal-percentage and linear opening are inverse inherent
characteristics with `Cv_min = Cv_rated / rangeability`; opening is **not clipped**
at the travel limit, so an undersized valve fails the capacity check. The reported
required Cv uses DWSIM's solved liquid density, volume flow and actual inlet/outlet
pressure. Default 10–90% travel is a configurable screening window, not a
manufacturer guarantee. It does not model valve pressure recovery, choked flow,
cavitation, flashing, viscosity correction, installed characteristic or actuator force.
Gas/two-phase rated-valve sizing is explicitly reported unsupported.

Pipe pressure loss is Darcy-Weisbach with a Colebrook Darcy factor from the
installed `fluids` package, plus `K × ρv²/2` fitting loss and `ρgΔz` static head.
The DWSIM implementation is an **outlet-pressure valve**, recalculated from solved
liquid properties twice. `dn_mm` is treated as inside diameter; use measured `id_mm`
for engineering work. Default roughness 0.045 mm is illustrative commercial steel.
The optional 3 m/s liquid-discharge screening limit follows pump manufacturer
guidance, not a universal code limit. Pipe heat transfer, compressible/two-phase
flow, transient/water hammer, erosion and fouling are not modeled. A datasheet and
line list are needed before accepting a capacity increase.

The unchanged `chem_c01` case contains no rated valve Cv. Run
`python evidence/hydraulics/chem_c01_demo.py` from the repo root for a clearly
**illustrative** Cv=35 US assumption on 47123/C1. It deep-copies the committed
model and isolates the new valve limit; other existing case limits may bind earlier.
On the current model it reaches 90% travel at about **1.20×** feed (~21.6 m³/h).

References: [Emerson liquid Cv sizing](https://www.emerson.com/is/content/emerson/en/final-control/flow-controls/documents/d351798x012_02.pdf),
[Spirax Sarco Cv/Kv conversion](https://www.spiraxsarco.com/-/media/spiraxsarco/international/documents/en/ti/dcv6-ti-p134-26-en.ashx),
[KSB head loss](https://www.ksb.com/en-global/centrifugal-pump-lexicon/article/head-loss-1116720),
[Grundfos discharge velocity guidance](https://api.grundfos.com/literature/Grundfosliterature-1073214.pdf).
