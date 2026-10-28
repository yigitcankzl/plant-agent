# Step 1 - Scope and design criteria

**Question:** VNF plans to replace the out-of-service pumps at Crissey lock pumping station with one new Xylem CT3400/736 submersible pump (nominal 600 l/s) lifting from the River Saône, whose level varies by about six metres. Is this pump a good match for the system and the range of river levels? Would variable speed drives save energy here, given how the pump will be used? What annual energy and saving should we expect compared with the old pump? The proposed discharge arrangement has a DN700 vertical riser with the automated gate valve directly upstream of a DN600 flowmeter, and VNF limits station pipework velocity to 2.2 m/s (CTCG Paper 73): is the pipework right? List the measures you recommend, quantified with the simulator where possible.

## Definitions
_none_

## Criteria
| name | value | source |
|---|---|---|
| Targeted / nominal pump flow | 0.6 m3/s (600 l/s) | p.5 + p.7 (VNF intent + future situation) |
| Pump type | Monoblock centrifugal submersible, dry-well arrangement per Fig.2 | p.5 |
| Motor energy performance target | IE3 or IE4 | p.5 |
| Station pipework velocity limit | 2.2 m/s max in station pipework | Task brief citing CTCG Paper 73 (not in pages) - see RFI-07 |
| Flowmeter accuracy - straight lengths | Requires 5D upstream / 3D downstream undisturbed straight length; gate valve is a disturbance | Standard electromagnetic flowmeter practice (see RFI-02) |
| Control philosophy | Automated from control desk / API driven by upstream level sensors (intermediate + far upstream); gate valve opens fully on low level, pump runs to high level | p.6 + p.7 |
| Monitoring | Smart water and energy monitoring + automation, supervision, telecontrol; optimise operating periods | p.5 |
| Operating duty for energy comparison | 400 basins/year = 880,000 m3/year ~ 408 h/year at 600 l/s | p.14 VNF advice |
| River level operating range to assess | Saone 171.45 (BWL/highest lift) to 177.48 mNGF (TWL/lowest lift); Design 172.4 mNGF; ~6 m variation | p.8 + p.11 |

## Standards
_none_

## Units on the flow path
- River Saone intake / suction sump (pump level 170.353 mNGF)
- Xylem CT3400/736 submersible monoblock centrifugal pump (dry-well)
- DN700 vertical discharge riser (ASSUMPTION per brief - see RFI)
- Automated gate / sectioning valve (directly upstream of meter)
- DN600 electromagnetic flowmeter (ASSUMPTION per brief - see RFI)
- Discharge pipework to canal / backflow (backflow level 182.963 mNGF)
- Upstream canal level sensors - intermediate + far upstream (duty/standby)
- Control desk / API + IHM automation, supervision, telecontrol + smart energy monitoring
