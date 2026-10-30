# Scenario matrix: chem_c01 (muse-spark-1.3-contributor, 1833 s, $0.198)

| Scenario | Result | Tools | Proposals | Files |
|---|---|---|---|---|
| capacity | Yes - more cooling and level reach 120% | check_coverage, get_spec, process_capacity, read_data_sheet, read_pid, run_process | Raise H1007 cooling water to 27 m3/h: verified; Raise H1008 chilled water to 18 m3/h: verified; Raise T4750 working level to 22.1 m3: verified |  |
| whatif_sweep | Colder feed eases cooling, not hold time | get_spec, sweep |  | chart: Feed T sensitivity at 1.2x throughput |
| datasheet | Cooler H1007 is tightest at 120 percent | get_spec, make_document, read_data_sheet, read_pid |  | document: Data sheet H1007 |
| summary | Product cooler limits higher output | make_document |  | document: Summary of answer 9 |
| work_order | Work order ready for cooling increase | make_document |  | document: Work order H1007: Raise H1007 cooling water to 27 m3/h |
| drawing | Rev B drawing shows cooler fix | draw_revision |  | drawing: Rev B - H1007 cooling increase for 120 percent throughput |
| relief | No - coolers, pump and tank unprotected | read_data_sheet, read_pid, relief_scan, report_gap, search_documents |  |  |
| unknown | Noise level cannot be calculated here | default.answer, read_data_sheet, read_pid, report_gap, search_documents |  |  |
| add_parallel | Second pump halves load, plant still limited | get_spec, run_process | Add second P4711 in parallel: verified |  |
| add_series | Booster does not fix cooling at 120% | get_spec, read_data_sheet, read_pid, run_process | Add 2 bar booster pump in series between P4711 and H1007: NOT verified (still over: H1007) |  |
| bypass | Bypass changes cooling almost not at all | get_spec, read_data_sheet, read_pid, run_process | Bypass 47123/C1 with spool piece: verified |  |
| remove | Cooler out: dispatch too hot at any flow | get_spec, process_capacity, read_data_sheet, read_pid, run_process |  |  |
| upsize | Larger motor not needed, cooling still fails | get_spec, read_data_sheet, read_pid, run_process |  |  |
| utility | No - dispatch too hot, tank hold short | get_spec, read_data_sheet, read_pid, run_process |  |  |
