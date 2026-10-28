# Hydraulic profile - base run `base-grav-final`

Calibrated existing gravity train with documented limits; settled pipe fitted to field test

## Water surface by structure (ft)

| structure | 12.0 mgd | 13.1 mgd | 18.0 mgd | drawing | residual |
|---|---|---|---|---|---|
| clearwell_outlet | 449.0 | 449.0 | 449.0 |  |  |
| clearwell | 449.0 | 449.0 | 449.0 | 449.0 | 0.0 / 0.0 / 0.0 |
| filter_effluent_pipe | 449.13 | 449.15 | 449.27 |  |  |
| filters | 464.0 | 464.0 | 464.0 | 464.0 | 0.0 / 0.0 / 0.0 |
| filter_inlet_pipe | 464.04 | 464.04 | 464.08 |  |  |
| filter_influent_channel | 464.16 | 464.19 | 464.35 |  |  |
| settled_water_pipe | 464.36 | 464.42 | 464.77 |  |  |
| settled_channel | 464.41 | 464.48 | 464.88 |  |  |
| sed_launders | 464.49 | 464.58 | 465.06 |  |  |
| sedimentation_basin | 464.59 | 464.7 | 465.29 | 464.83 | -0.24 / -0.13 / 0.46 |
| flocculation_basin | 464.69 | 464.81 | 465.51 |  |  |
| rapid_mix | 464.74 | 464.87 | 465.63 | 466.0 | -1.26 / -1.13 / -0.37 |

## Flow at which each limit binds

| id | check | binds_at_mgd |
|---|---|---|
| sedimentation_basin | single basin treatment 12 mgd | 12.0 |
| filters | filter treatment 3 mgd each | 12.02 |
| settled_channel | basin overflow weir 465.0 ft | 19.25 |
| sedimentation_basin | basin MAX WS 465.98 ft | 22.48 |
| rapid_mix | rapid-mix top 467.5 ft | 26.66 |
| clearwell | clearwell HSPS overflow weir 449.5 ft | None |
| filters | filter top of wall 467.5 ft | None |
