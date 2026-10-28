# Hydraulic profile - base run `base-grav2`

calibrated existing single-basin four-filter train

## Water surface by structure (ft)

| structure | 12.0 mgd | 13.1 mgd | drawing | residual |
|---|---|---|---|---|
| clearwell | 449.0 | 449.0 |  |  |
| filteff-18in | 449.19 | 449.22 |  |  |
| filters-4 | 464.0 | 464.0 | 464.0 | 0.0 / 0.0 |
| filtin-20in | 464.06 | 464.07 |  |  |
| settled-pipe-42in | 464.26 | 464.3 | 464.83 | -0.57 / -0.53 |
| settled-channel | 464.33 | 464.39 |  |  |
| sed-launders | 466.0 | 466.01 | 465.98 | 0.02 / 0.03 |
| floc-basin | 466.2 | 466.25 |  |  |
| rapidmix-1 | 466.25 | 466.31 | 466.0 | 0.25 / 0.31 |

## Flow at which each limit binds

| id | check | binds_at_mgd |
|---|---|---|
| rapidmix-1 | single basin rated 12 mgd | 12.0 |
| filters-4 | treatment 3 mgd per filter | 12.02 |
| sed-launders | max WS 466.0 freeboard to 467.5 | 12.53 |
| settled-channel | max water surface | 21.63 |
| rapidmix-1 | top walls 467.5 | 28.14 |
| filters-4 | top walls 467.5 | None |
