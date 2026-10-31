# Freeport LNG, 18-inch LNG transfer line: data sheet

Facility facts are from PHMSA's public notice on the Freeport LNG export terminal (Quintana Island, Texas): Amended Notice of
Probable Violation CPF 4-2024-033-NOPV, 20 December 2024 (cited as NOPV p.N). Real tag numbers, the segment length, the pipe
specification and the design pressure are not public (the operator's root-cause report is redacted). Everything not in the
NOPV is marked ILLUSTRATIVE, with the reason for the value chosen. Tags on the drawing are ILLUSTRATIVE.

## The line

- LNG is transferred from the storage tanks to the ship dock through 18-inch vacuum-insulated piping (VIP) (NOPV p.2).
- The segment on the drawing, VIP-18, runs between block valve XV-101 (tank side) and block valve XV-102 (dock side).
- Relief: PSV-101 protects the segment through isolation valve HV-101.
- Instruments: four inner-pipe skin temperature points TI-101 to TI-104 were installed for cooldown (commissioning). The DCS
  logs them (NOPV p.4).

## Operating record before the period in question

- 26 April 2022: PSV-101 annual test. HV-101 was closed to isolate PSV-101 from the segment for the test (NOPV p.2).
- 3 June 2022, 08:22: the DCS operator closed XV-101 while lining up for a ship transfer. The VIP temperature began to rise
  and LNG in the line vaporised back to an LNG tank through the still-open path (NOPV p.3).
- 3 June 2022, 16:44: the operator closed XV-102. From then on VIP-18 is closed at both ends. It was partially filled with
  LNG, at 37 psig (NOPV p.3).

## Fluid

- LNG (ILLUSTRATIVE: the composition is not public). A lean Gulf Coast export LNG is assumed, in mole fractions: methane
  0.95, ethane 0.035, propane 0.010, nitrogen 0.005.
- Start state: 37 psig, at its bubble point (NOPV p.3).

## Assumptions to state and vary

- **Liquid fill fraction** of the segment when XV-102 closed. The NOPV says only "partially filled" (NOPV p.3).
  - ILLUSTRATIVE range: 0.70 to 0.95 by volume.
  - The line had been draining to the tank for about 8 hours after XV-101 closed, so it was not liquid-full.
  - But it was a transfer line in service shortly before, so it was mostly liquid.
- **Heat leak into the inner pipe.** Not public.
  - ILLUSTRATIVE: a sound vacuum jacket on an 18-inch line takes in about 1 to 3 W per metre.
  - Where the vacuum is degraded, and at valve bodies, supports and flanges, conventional-insulation values of about 10 to
    30 W per metre apply.
  - The NOPV records that the VIP temperature rose as soon as XV-101 closed (NOPV p.3), so the line was taking in heat.
- **Pipe (inner)**, ILLUSTRATIVE: NPS 18, austenitic stainless 304L, Schedule 10S. That is 457.2 mm OD and 4.78 mm wall.
- **Design pressure**, ILLUSTRATIVE 230 psig. This is the ASME B16.5 Class 150 rating for 304L (material group 2.3) at
  −29 to 38 °C. Cryogenic transfer lines at LNG terminals are commonly Class 150. The segment's actual design pressure is not
  public.
- **PSV-101 set pressure**, ILLUSTRATIVE: equal to the design pressure, 230 psig.
- **Estimated burst pressure**, ILLUSTRATIVE 1,456 psig. It comes from the Barlow formula with a 70 ksi minimum tensile
  strength for 304L at ambient temperature, on the illustrative wall. Weld quality and cryogenic strength would move it.
- **Length**, ILLUSTRATIVE 100 m. It does not change the pressure history: the trapped mass and the heat leak both scale
  with length.

## Request

VIP-18 was isolated for relief-valve testing and left blocked in. What happens to its pressure over the following days?
When does it exceed design? What should have prevented it?
