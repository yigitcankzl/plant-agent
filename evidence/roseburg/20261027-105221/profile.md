# Hydraulic profile - base run `BASE-CALIB-EXIST`

Calibrated existing 1-basin 4-filter profile for base run

## Water surface by structure (ft)

| structure | 11.5 mgd | 12.0 mgd | 13.1 mgd | 18.0 mgd | drawing | residual |
|---|---|---|---|---|---|---|
| Clearwell-447 | 447.0 | 447.0 | 447.0 | 447.0 |  |  |
| Filters-464 | 464.0 | 464.0 | 464.0 | 464.0 | 464.0 | 0.0 / 0.0 / 0.0 / 0.0 |
| FiltInfl-1of4 | 464.03 | 464.03 | 464.03 | 464.06 |  |  |
| Settled-42in | 464.21 | 464.23 | 464.27 | 464.48 | 464.83 | -0.62 / -0.6 / -0.56 / -0.35 |
| Basin-1exist | 465.84 | 466.01 | 466.39 | 468.49 | 465.98 | -0.14 / 0.03 / 0.41 / 2.51 |

## Flow at which each limit binds

| id | check | binds_at_mgd |
|---|---|---|
| Basin-1exist | Influent channel max 466.0 ft (top wall 467.5, 1.5 ft freeboard) | 12.0 |
| Settled-42in | Settled pipe ultimate 22-24 mgd | 24.0 |
| Settled-42in | Basin overflow weir 465.0 ft | 26.82 |
| Filters-464 | driving head | None |
| Filters-464 | max water surface | None |
