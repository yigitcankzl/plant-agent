# Monterey SWRO historian: sources and transformations

`historian.csv` has 772 daily rows, 2022-01-01 through 2024-02-11.
It is not a Monterey plant export. Monterey had no operating plant when the 2013 RFP was issued.
Three labelled pieces are combined. Pressures and permeate conductivities are calculated.

## 1. Carlsbad flow, temperature and salinity

Source: California State Water Resources Control Board CIWQS eSMR, facility place id 640063,
Claude "Bud" Lewis Carlsbad Desalination Plant, NPDES CA0109223. File
`case-data/raw/desal_ops/carlsbad_esmr/carlsbad_esmr_2015_2026.csv.gz`. License: public domain
(`other-pd` on data.ca.gov). See that folder's SOURCE.txt.

Columns used:

- `M-001` Flow whose comment is `Continuous Reading; Reverse Osmosis Concentrate`, daily, MGD.
  In this window the median is 51.24 MGD.
- `M-001` Flow whose comment is `Calculated Flows of Media Filtration Backwash`. Median
  2.79 MGD.
- `M-INF` Temperature, degrees F, about weekly, converted with (F − 32) × 5/9.
- `M-INF` Salinity, ppth, PSS-78, about weekly. Used as PSS.

Not used as Monterey intake: `M-INF` Flow (`Total Source Water Flow (CDP Intake)`). That series
includes dilution water for the Encina co-discharge and is several times the RO feed. Monterey's
slant-well intake has no such dilution stream.

Scaling. The RFP caps first-pass recovery at 45% (RFP PDF p.346). Rated product is 9.6 MGD
(RFP PDF p.332). Design concentrate at that corner is 9.6 × (1 − 0.45) / 0.45 = 11.73 MGD
on the median day. Each Carlsbad concentrate day is multiplied by 0.229.
Feed is that concentrate divided by (1 − 0.45), so the recovery in the file is exactly 45% and the
median feed is 21.33 MGD. Backwash is the Carlsbad backwash day times the
same concentrate scale factor. The shape is Carlsbad's; the level is Monterey's.

Days with no concentrate or backwash sample are linearly filled from the neighbouring samples
(0 concentrate days in this window were filled). Weekly temperature and
salinity are linearly interpolated and held flat outside the first and last sample. This window's
temperature is 12.17 to 25.28 C and salinity is
22.06 to 34.69 PSS. Carlsbad does not reach Monterey's 8 C design
minimum (RFP PDF p.428). The coldest day in this file is 2023-04-05 at
12.17 C and 33.3 PSS. The saltiest day is
2022-08-22 at 34.69 PSS. Those are Carlsbad observations,
not the RFP design corner (8 C and 37 PSS together).

## 2. Anonymised SWRO fouling and CIP

Source: Su, Yi Hsiang, Zenodo record 21055948, version 1.3 (2026-06-30), CC-BY-4.0.
`derived_daily_indicator_table.csv` and `cip_campaign_ledger.csv`. The plant, the membrane model,
the area and the calendar were removed by the author. `ndp_pct` is the fractional deviation of net
driving pressure from a fixed commissioning baseline, `dp_pct` the normalised feed-channel
differential pressure, `flux_pct` the 25 C specific flux, and `sp_pct` the 25 C salt passage.
Deviations are one-sided and clipped to the range 0 to 1. There are 18 CIP episodes.

Trains A, B and C are applied to Monterey tags RO-201, RO-202 and RO-203. The RFP module is 1.6 MGD
and the 9.6 MGD rated plant implies more than three trains (see basis.md). Only three trains carry
this fouling record. Zenodo `day_index` 0 is placed on 2022-01-01. That alignment is a
label, not the withheld plant's calendar. A missing train-day copies the previous deviation.

`XI-201`, `XI-202` and `XI-203` are days since that train's last CIP on this labelled calendar.
They are blank before the first CIP.

## 3. Derived pressure and conductivity

These columns are not in either dataset. They use a solution-diffusion screening so a limit check
has a pressure to read. Constants that are not in the RFP or the SCADA:

- Operating flux 8.0 gfd, below the RFP maximum of 8.75 gfd. The RFP does not state the design flux.
- Water permeability A = 1.8865e-12 m/(s·Pa). Clean net driving pressure is 20.0 bar.
- Salt permeability B = 2e-08 m/s.
- Osmotic pressure (bar) = 0.797 × salinity (PSS) × T(K) / 298.15, because 35 PSS is taken as 27.9 bar at 25 C.
- With nearly complete rejection, the concentrate factor is 1/(1 − 0.45) and the log-mean factor along the vessel is 1.369.
- Feed pressure (bar) = clean NDP × (1 + ndp deviation) + log-mean osmotic pressure + 1 bar permeate backpressure.
  Throughput is not cut when the flux deviation rises; the NDP deviation is what raises pressure. The flux deviation is still stored.
- Channel dP (bar) = 0.7 × (1 + dp deviation). The 0.70 bar clean value is not a measurement.
- Permeate TDS ≈ (salinity × 1000) × (B / (J + B)) × (1 + salt-passage deviation), with PSS used as g/m³.
  Conductivity (µS/cm) ≈ 2 × that TDS. This is a first-pass screening result, not finished water, and it ignores the partial second pass.

On the cold day above, the derived RO-201 feed pressure is 65.09 bar. On the salty day it is 59.64 bar.
The RFP feed-pressure ceiling is 1000 psi (68.95 bar) (RFP PDF p.346).
