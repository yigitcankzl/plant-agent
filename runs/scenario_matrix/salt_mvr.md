# Scenario matrix: salt_mvr (muse-spark-1.3-contributor; capacity and work_order re-run after the tag-alias fix)

| Scenario | Result | Tools | Proposals | Files |
|---|---|---|---|---|
| capacity | No - vapour compressor limits plant today | get_spec, process_capacity, read_data_sheet, read_pid, run_process | Add 49.5 tonne per hour parallel compressor K-202: verified; Clean main heater E-201: verified; Hold purge steam at today's rate: verified |  |
| whatif_sweep | Warmer feed helps heater, compressor still full | get_spec, read_data_sheet, sweep |  | chart: Main feed temperature sensitivity at 120% feed |
| datasheet | Data sheet ready for compressor K-201 | make_document |  | document: Data sheet K-201 |
| summary | Salt plant needs upgrades to reach target | make_document |  | document: Summary of answer 9 |
| work_order | Work order ready: clean main heater | make_document | Clean main heater E-201: verified | document: Work order E-201: Clean main heater E-201 |
| drawing | Revised drawing done, compressor noted | draw_revision, get_spec, read_data_sheet, read_pid |  | drawing: Rev B - 120% capacity upgrade with parallel compressor |
| relief | No - eight sides lack secure relief protection | read_pid, relief_scan |  |  |
| unknown | Cannot calculate noise - locations and sound ratings missing | historian, read_data_sheet, read_pid, report_gap, search_documents |  |  |
| add_parallel | Second compressor unloads first, heaters still limit | get_spec, read_data_sheet, read_pid, run_process | Add parallel vapour compressor K-202: verified |  |
| add_series | No - second desuperheater changes nothing | get_spec, read_data_sheet, read_pid, run_process | Add second desuperheater D-202 after D-201: NOT verified (still over: V-201, V-201) |  |
| bypass | Main unit runs, purge waste nearly doubles | get_spec, read_data_sheet, read_pid, run_process |  |  |
| fouling | Cut output below 1900 watts per square-metre-kelvin | get_spec, read_data_sheet, read_pid, sweep |  | chart: foul_E201_U_at_100pct; chart: foul_E201_U_refined_100pct |
| feed_conc | Dilute feed cuts salt by 41 percent | get_spec, read_data_sheet, read_pid, run_process |  |  |
| upsize | Bigger heater fits but compressor still limits | get_spec, read_data_sheet, read_pid, run_process | Replace E-201 with 10,000 m2 unit: verified |  |
