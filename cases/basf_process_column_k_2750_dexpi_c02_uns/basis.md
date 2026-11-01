Operating data sheet generated automatically from the DEXPI P&ID (no engineer input beyond the drawing).
Only what the drawing states is listed; process conditions not on the drawing are unknown and must be assumed.

Equipment K 2750 (ProcessColumn): EquipmentDescription Column
  design limits: Height 14000 Millimetre, InsideDiameter 500 Millimetre, LowerLimitDesignPressure -1 Bar, UpperLimitDesignPressure 6 Bar, UpperLimitDesignTemperature 150 DegreeCelsius, MaterialOfConstructionCode 1.4571, SubTagName Chamber 1
Equipment KX 2750 (ColumnSection): InsideDiameter 600 Millimetre
  design limits: MaterialOfConstructionCode 1.4571
Line 2750.001.6: fluid code 8503, piping class 10HB25T10B1, DN None
Line *at N3*: fluid code None, piping class None, DN None
Line *at P3*: fluid code None, piping class None, DN None
Line *at P4*: fluid code None, piping class None, DN None
Connection K 2750(ProcessColumn) -> open-out:PipingNetworkSegment-4(OpenEnd) via direct
Connection K 2750(ProcessColumn) -> 2750.001.6/FlowOutPipeOffPageConnector(FlowOutPipeOffPageConnector) via 2750.001.6/PipeReducer(PipeReducer)
Valve *at N3*/*C2* (OperatedValve)
Valve *at P3*/OperatedValve (OperatedValve)
Valve *at P4*/OperatedValve (OperatedValve)
Instrumentation: *at P3*/BlindFlange(BlindFlange) --measured_at--> ProcessSignalGeneratingFunction-1(ProcessSignalGeneratingFunction)
Instrumentation: *at P3*/BlindFlange(BlindFlange) --MeasuringLineFunction--> PI(Z) 275003A(ProcessInstrumentationFunction)
Instrumentation: PI(Z) 275003A(ProcessInstrumentationFunction) --SignalConveyingFunction--> PIS⁺Z⁺A 275003(ProcessInstrumentationFunction)
Instrumentation: *at P4*/BlindFlange(BlindFlange) --measured_at--> ProcessSignalGeneratingFunction-2(ProcessSignalGeneratingFunction)
Instrumentation: *at P4*/BlindFlange(BlindFlange) --MeasuringLineFunction--> PI(Z) 275003B(ProcessInstrumentationFunction)
Instrumentation: PI(Z) 275003B(ProcessInstrumentationFunction) --SignalConveyingFunction--> PIS⁺Z⁺A 275003(ProcessInstrumentationFunction)
