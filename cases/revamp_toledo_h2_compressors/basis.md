# Toledo hydrocracking hydrogen compressors: blind operating basis

Source: a symposium paper. The citation is withheld from the agent because it identifies the outcome; it is recorded with the withheld outcome in `outcome.json` and in the case's `source` field.

## Existing compression system

- The refinery hydrocracking complex uses two parallel Cooper-Bessemer LM-3 reciprocating compressors for hydrogen recycle service.
- Each compressor handles about **27.5 MMSCFD** from **250 psig** suction to **1,450 psig** discharge in **three stages**.
- Original cylinder bores are **19.5 in.**, **16.25 in.** and **11.0 in.** for the first, second and third stages respectively.
- Each machine is driven by a **3,500 hp** electric motor. The installed frames, motors, intercoolers and foundations are to remain.
- Compressor capacity constrains hydrocracker throughput. The two machines normally share the recycle service.

## Modelling boundary

- The publication does not tabulate a complete recycle-gas assay, valve loss model or interstage temperatures. Use a hydrogen-rich surrogate, state molecular-weight and efficiency assumptions, and preserve the published end pressures.
- Represent the three stages with intercooling. Check final power against the installed motor and report stage pressure ratios and discharge temperatures.
- A cylinder displacement calculation is needed alongside DWSIM; DWSIM alone does not select reciprocating-compressor valves or piston hardware.

## Project premise

Increase recycle-hydrogen capacity by about **12%** in the existing compressor frames while retaining the **3,500 hp** motors. Identify the smallest mechanical scope and verify that the compression duty and cooling remain credible.
