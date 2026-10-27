# Hydraulic profile - base run `base-profile`

Calibrated existing-conditions base profile: gravity train rapid-mix to clearwell at 12-18 mgd

## Water surface by structure (ft)

| structure | 12.0 mgd | 14.0 mgd | 16.0 mgd | 18.0 mgd | drawing | residual |
|---|---|---|---|---|---|---|
| clearwell-ws | 449.0 | 449.0 | 449.0 | 449.0 |  |  |
| clearwell | 449.02 | 449.03 | 449.04 | 449.05 | 449.0 | 0.02 / 0.03 / 0.04 / 0.05 |
| filter-effluent-per-filter | 449.6 | 449.81 | 450.06 | 450.33 |  |  |
| filters-1-4 | 464.0 | 464.0 | 464.0 | 464.0 | 464.0 | 0.0 / 0.0 / 0.0 / 0.0 |
| filter-inlet-20in | 464.18 | 464.24 | 464.31 | 464.4 |  |  |
| settled-pipe-42in | 464.38 | 464.51 | 464.65 | 464.82 |  |  |
| settled-channel | 464.43 | 464.57 | 464.74 | 464.93 | 464.83 | -0.4 / -0.26 / -0.09 / 0.1 |
| sed-launders | 465.98 | 465.99 | 466.01 | 466.02 |  |  |
| floc-sed-basin | 466.18 | 466.26 | 466.36 | 466.47 |  |  |
| rapid-mix | 466.48 | 466.67 | 466.9 | 467.15 | 466.0 | 0.48 / 0.67 / 0.9 / 1.15 |

## Flow at which each limit binds

| id | check | binds_at_mgd |
|---|---|---|
| floc-sed-basin | single existing basin rated 12 mgd (p.111) | 12.0 |
| filters-1-4 | 3 mgd treatment rating per filter (p.112) | 12.02 |
| sed-launders | sed max WS 465.98 (dwg p.136); freeboard 1.5 ft (p.111) | 13.13 |
| settled-channel | basin OF weir 465.0 (p.111)(dwg p.136) | 18.75 |
| rapid-mix | rapid-mix top 467.5 (dwg p.136) | 20.55 |
| clearwell | HSPS OF weir 449.5 (p.114)(dwg p.136) | None |
| filters-1-4 | top of wall 467.5 (dwg p.136) | None |
