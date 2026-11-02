# BP Lima saturates-gas-plant de-ethanizing stripper: blind operating basis

Source: Deley and Graf, *Oil & Gas Journal*, 1 August 1994, sections "Stripper tower" and "Project scope". This sheet contains the tower state before the project and the production premise only.

## Existing absorber/stripper system

- The system has a primary absorber, high-pressure condenser and separator, and a de-ethanizing stripper. It separates C2/C3 and heavier saturated light ends (source Figure 1 and "Stripper tower").
- Stripper shell diameter: **9 ft**. It contains **20 three-pass valve trays**, most at **24 in.** spacing (source "Stripper tower").
- A bottom reboiler and a side reboiler are installed. The side draw and return sit between the fourth and fifth trays from the bottom (source "Stripper tower").
- Highest internal liquid load is above the side-reboiler return. Design liquid loading for that section is **3,308 gpm**, about **52 gpm/ft2** in the 9 ft shell (source project hydraulic data).
- The current design capacity is **76,000 b/d**. Summer light-ends peaks and reformer swings produce downcomer flooding on the existing trays (source tower scan and operating account).
- LPG typically contains **6-7 vol% ethane** in this state. About **250 b/d propane** is lost to fuel gas because absorber lean-oil flow is reduced to unload the stripper (source operating account).

## Product criterion and modelling boundary

- LPG vapour pressure is limited to **208 psig**, corresponding in the source to about **3.5 vol% ethane** in the LPG.
- The publication does not give a complete feed assay. A DWSIM model may use a C2/C3/C4 surrogate feed, but every fraction and the b/d-to-mass conversion has to be labelled as assumed.
- Preserve the 9 ft shell, side-reboiler location and bottom four trays in the base model.

## Project premise

The desired design capacity is **92,000 b/d** (**1.2105x** the current design capacity) at the LPG vapour-pressure criterion. Find the hydraulic and thermal scope inside the existing shell, and test the effect of feed preheat rather than silently adding reboiler duty.
