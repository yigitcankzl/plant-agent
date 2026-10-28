# Hydraulic profile - base run `prof-cal-2basin`

Calibrated gravity profile filters to rapid mix via 42-in settled pipe at total plant flows; with two basins each carries half; settled pipe carries full flow

## Water surface by structure (ft)

| structure | 9.0 mgd | 12.0 mgd | 13.1 mgd | 18.0 mgd | 22.0 mgd | drawing | residual |
|---|---|---|---|---|---|---|---|
| clearwell | 449.0 | 449.0 | 449.0 | 449.0 | 449.0 |  |  |
| filters | 464.0 | 464.0 | 464.0 | 464.0 | 464.0 | 464.0 | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 |
| settled42 | 464.12 | 464.2 | 464.23 | 464.42 | 464.61 | 464.83 | -0.71 / -0.63 / -0.6 / -0.41 / -0.22 |
| rapidmix | 466.0 | 466.0 | 466.0 | 466.0 | 466.0 |  |  |

## Flow at which each limit binds

| id | check | binds_at_mgd |
|---|---|---|
| settled42 | sed basin overflow weir 465.0 ft | 28.82 |
| filters | max water surface | None |
| rapidmix | rapid mix top of wall | None |
