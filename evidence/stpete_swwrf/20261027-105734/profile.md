# Hydraulic profile - base run `SW_base40`

Calibrated existing-conditions gravity profile CCB to headworks at 20 and 40 MGD against Figure 5-1 water surfaces; filters held at blinded overflow 115.3 ft

## Water surface by structure (ft)

| structure | 20.0 mgd | 40.0 mgd | drawing | residual |
|---|---|---|---|---|
| CCB_eff | 107.78 | 107.78 |  |  |
| CCB_weir | 108.09 | 108.31 | 109.0 | -0.91 / -0.69 |
| P54_Filt_CCB | 109.83 | 114.61 | 115.3 | -5.47 / -0.69 |
| Filters_blinded | 115.3 | 115.3 | 115.3 | 0.0 / 0.0 |
| P48_Sec_Filt | 116.09 | 118.15 | 118.15 | -2.06 / -0.0 |
| SC3_vnotch | 118.18 | 118.28 | 118.15 | 0.03 / 0.13 |
| P48_Aer_Sec | 118.63 | 119.92 | 122.02 | -3.39 / -2.1 |
| Aer_basin | 122.92 | 122.92 | 122.92 | 0.0 / 0.0 |
| Headworks_primary_lumped | 124.92 | 130.93 | 132.93 | -8.01 / -2.0 |

## Flow at which each limit binds

| id | check | binds_at_mgd |
|---|---|---|
| Headworks_primary_lumped | Primary clarifier peak (bypass at 40 MGD) | 40.0 |
| P54_Filt_CCB | Filter overflow (blinded) | 42.26 |
| Headworks_primary_lumped | Headworks top | 49.98 |
| P48_Sec_Filt | Clarifier No.3 top (assumed) | 56.17 |
| Filters_blinded | max water surface | None |
| P48_Aer_Sec | Aeration top (assumed) | None |
| Aer_basin | max water surface | None |
