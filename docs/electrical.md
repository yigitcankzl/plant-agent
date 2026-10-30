# Electrical discipline

`plantagent/electrical.py` checks whether the plant's power system carries a proposal's new or bigger motors.

## Environment

pandapower runs in its own virtualenv, `.venv-electrical`, the same way WaterTAP has `.venv-watertap`. Installing
pandapower 3.5.6 into the main `.venv` would downgrade numpy 2.5.4 → 2.4.6 and pandas 3.1.0 → 2.3.3 there (checked with
`uv pip install --dry-run`), and that is the DWSIM environment. So the main process never imports pandapower. Each
check runs one subprocess, `.venv-electrical/bin/python -m plantagent.electrical --solve`, with JSON in and out.

Installed on 2026-10-31: pandapower 3.5.6, numpy 2.4.6, pandas 2.3.3, scipy 1.18.1 (Python 3.12); 273 MB on disk.

    uv venv --python 3.12 .venv-electrical
    uv pip install --python .venv-electrical/bin/python -r requirements-electrical.txt

In a git worktree, symlink it: `ln -s <main checkout>/.venv-electrical .venv-electrical`.

## Network

`cases/<case>/electrical.json` is the one-line diagram:
- utility infeed (short-circuit MVA, R/X), included in the load flow as a series impedance;
- transformers (MVA, %uk, %ukr, off-load tap as a ratio);
- buses (kV), on-site generators (PQ), lumped loads (MW, PF);
- motor feeders: kW rating, efficiency, PF, starting method (DOL, VFD, SOFT), locked-rotor current multiple, cable
  type and length, and the process unit id they drive.

Every value is ILLUSTRATIVE unless a case document gives it, and each entry says which:
- salt_mvr: the 1.7 MW steam turbine generator is US 5,366,514 Table I item 35. The patent says it covers approximately
  all plant electricity, and K-201 is gas-turbine driven, so K-201 is not an electrical load.
- chem_c01: the P4711 2.2 kW and P4712 7.5 kW motors are from the site datasheets in basis.md.

## Method

1. Process solve at the checked throughput (DWSIM). A motor's electrical load is the shaft kW of its unit divided by
   its efficiency. A motor whose unit is not in the process model runs at its rated kW.
2. A proposal's changes imply motors:
   - an `add_unit` pump or compressor with `limits.max_kW` becomes a new feeder. It goes on an MV bus from
     `mv_from_kw` (250 kW) upwards, otherwise on an LV bus; of those, the bus whose feeding transformer has the most MVA,
     unless the change names a `bus`.
   - `units|limits.<id>.max_kW`, or "N kW" in a `physical_change`, re-rates an existing motor.
   - Overrides: `motors: [{unit, kw, start, bus}]`.
3. Load flow (pandapower Newton-Raphson). It gives transformer loading, cable loading and bus voltages.
4. Motor start of the largest new or re-rated motor:
   - The motor becomes a shunt admittance at its locked-rotor kVA: DOL is lrc × rated kVA at PF 0.3; a soft starter is
     3.5 × at PF 0.3; a VFD is 1.1 × at PF 0.95.
   - Every other load is a constant-impedance shunt.
   - On-site generators are not credited during the start (conservative).
   - The dip is measured against the same network before the start.
   - Why shunts: constant-impedance *loads* do not converge for deep dips in pandapower's NR, and a constant-power
     generator gives non-physical low-voltage solutions.

## Limits (checks use utilisation = value / limit)

| Check | Limit | Basis |
|---|---|---|
| Transformer loading | 100 % | IEC 60076-1 rated power (continuous) |
| Cable loading | 100 % | manufacturer ampacity, IEC 60287 basis |
| Steady bus voltage | ±5 % | typical plant practice (IEC 60038 allows ±10 % at the supply) |
| Start dip at the motor terminal | 15 % | typical practice (IEC 60034-1 sets no start-dip limit) |
| Start dip on other buses | 10 % | typical practice (contactor drop-out, lighting) |

## Not modelled

- Motor acceleration time and the torque-speed curve: this is a locked-rotor screen, not a dynamic start.
- Short-circuit duty and protection coordination.
- Harmonics from VFDs.
- Generator AVR support during a start.
