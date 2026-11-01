# DWSIM unit operations in this install

Survey of the DWSIM build at `~/opt/dwsim/usr/local/lib/dwsim` (DWSIM.Interfaces 9.0.5), taken by constructing each `ObjectType` through `Automation3` and reading `GetConnectionPortsList` plus public numeric, boolean and enum properties. Graphic objects, gauges and controllers that throw on `AddObject` are listed as unavailable.

PlantAgent does not reflect over arbitrary properties. `type: dwsim` may only set the allowlist in `plantagent/process.py` (`DWSIM_ALLOW`). SI units below are DWSIM's stored units for those properties. Reactions, a column feed stage and condenser/reboiler specifications are not properties: use `type: reactor` and `type: distillation`.

## What DWSIM does not do

- The rigorous column writes a per-stage profile (T, P, molar and mass traffic, densities, viscosity, thermal conductivity, surface tension) and an `EstimatedDiameter`. That diameter is a single Souders-Brown-style estimate, `u = (-0.17*lt^2 + 0.27*lt - 0.047)*sqrt((rho_L-rho_V)/rho_V)` with `lt` the tray spacing in metres (see `RigorousColumn.vb` in DWSIM 9). It is not a flooding fraction, and there is no weir load, hole velocity or downcomer backup. PlantAgent screens flood with Fair's correlation on the reported traffic.
- `RefluxedAbsorber` and `ReboiledAbsorber` object types throw on creation. Use `DistillationColumn` (the flags exist on that class).
- `ReactionKinetics` on this build is only `Expression` or `PythonScript`. Arrhenius kinetics are `ReactionKinFwdType = Arrhenius`, used when the forward expression is empty: `k = A*exp(-E/RT)` with `E` in J/mol. A CSTR integrates liquid holdup; a vapor-only feed does not react (use a PFR for gas-phase kinetics). `Headspace` must be greater than 0.
- A generic unit cannot create a reaction set or call `ConnectFeed` / `SetCondenserSpec` / `SetReboilerSpec`. Those are the reactor and distillation units.
- `SolidSeparator` is a fixed efficiency split, not a cyclone or filter design. `Filter` exposes cake-filtration inputs but no separate limit check.
- `CustomUO`, `ExcelUO`, `CapeOpenUO`, `FlowsheetUO` and the Python controller are not allowlisted (they run arbitrary code or a nested sheet).
- Several object types fail in `AddObject` (null reference): NodeEn, TPVessel, Nenhum, graphic shapes, RefluxedAbsorber, ReboiledAbsorber, CapeOpenUO, CompressorExpander, HeaterCooler, External, AirCooler2, EnergyMixer, Dummy, SolidOps.

## Allowlisted classes

Ports are listed in DWSIM's order. `in` and `out` on a `dwsim` unit fill the first material ports; extra ports stay open. Energy ports are optional.

| ObjectType | Class | Ports |
|---|---|---|
| `NodeIn` | `Mixer` | Inlet #0, Name: Inlet Stream 1, Type: ConIn; Inlet #1, Name: Inlet Stream 2, Type: ConIn; Inlet #2, Name: Inlet Stream 3, Type: ConIn; Inlet #3, Name: Inlet Stream 4, Type: ConIn; Inlet #4, Name: Inlet Stream 5, Type: ConIn; Inlet #5, Name: Inlet Stream 6, Type: ConIn; Outlet #0, Name: Mixed Stream, Type: ConOut |
| `NodeOut` | `Splitter` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet 1, Type: ConOut; Outlet #1, Name: Outlet 2, Type: ConOut; Outlet #2, Name: Outlet 3, Type: ConOut |
| `Pump` | `Pump` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Outlet, Type: ConOut |
| `Tank` | `Tank` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet, Type: ConOut |
| `Vessel` | `Vessel` | Inlet #0, Name: Inlet Stream #0, Type: ConIn; Inlet #1, Name: Inlet Stream #1, Type: ConIn; Inlet #2, Name: Inlet Stream #2, Type: ConIn; Inlet #3, Name: Inlet Stream #3, Type: ConIn; Inlet #4, Name: Inlet Stream #4, Type: ConIn; Inlet #5, Name: Inlet Stream #5, Type: ConIn; Inlet #6, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Vapor Outlet, Type: ConOut; Outlet #1, Name: Light Liquid Outlet, Type: ConOut; Outlet #2, Name: Heavy Liquid Outlet, Type: ConOut; Outlet #3, Name: Relief Valve Outlet, Type: ConOut |
| `MaterialStream` | `MaterialStream` | Inlet #0, Name: , Type: ConIn; Outlet #0, Name: , Type: ConOut |
| `EnergyStream` | `EnergyStream` | Inlet #0, Name: , Type: ConIn; Outlet #0, Name: , Type: ConOut; Energy Stream, Name: , Type: ConEn |
| `Compressor` | `Compressor` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Outlet, Type: ConOut |
| `Expander` | `Expander` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet, Type: ConOut; Energy Stream, Name: Energy Stream, Type: ConEn |
| `Cooler` | `Cooler` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream (Secondary), Type: ConEn; Outlet #0, Name: Outlet, Type: ConOut; Energy Stream, Name: Energy Stream (Primary), Type: ConEn |
| `Heater` | `Heater` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream (Primary), Type: ConEn; Outlet #0, Name: Outlet, Type: ConOut; Energy Stream, Name: Energy Stream (Secondary), Type: ConEn |
| `Pipe` | `Pipe` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet, Type: ConOut; Energy Stream, Name: Energy Stream, Type: ConEn |
| `Valve` | `Valve` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet, Type: ConOut |
| `OT_Adjust` | `Adjust` |  |
| `OT_Spec` | `Spec` |  |
| `OT_Recycle` | `Recycle` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet, Type: ConOut |
| `RCT_Conversion` | `Reactor_Conversion` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Vapor Outlet, Type: ConOut; Outlet #1, Name: Liquid Outlet, Type: ConOut; Outlet #2, Name: Energy Stream, Type: ConEn |
| `RCT_Equilibrium` | `Reactor_Equilibrium` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Vapor Outlet, Type: ConOut; Outlet #1, Name: Liquid Outlet, Type: ConOut |
| `RCT_Gibbs` | `Reactor_Gibbs` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Vapor Outlet, Type: ConOut; Outlet #1, Name: Liquid Outlet, Type: ConOut |
| `RCT_CSTR` | `Reactor_CSTR` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Liquid Outlet, Type: ConOut; Outlet #1, Name: Vapor Outlet (Optional), Type: ConOut |
| `RCT_PFR` | `Reactor_PFR` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Energy Stream, Type: ConEn; Outlet #0, Name: Outlet, Type: ConOut |
| `HeatExchanger` | `HeatExchanger` | Inlet #0, Name: Inlet Stream 1, Type: ConIn; Inlet #1, Name: Inlet Stream 2, Type: ConIn; Outlet #0, Name: Outlet Stream 1, Type: ConOut; Outlet #1, Name: Outlet Stream 2, Type: ConOut |
| `ShortcutColumn` | `ShortcutColumn` | Inlet #0, Name: Inlet, Type: ConIn; Inlet #1, Name: Reboiler Duty, Type: ConEn; Outlet #0, Name: Distillate, Type: ConOut; Outlet #1, Name: Bottoms, Type: ConOut; Energy Stream, Name: Condenser Duty, Type: ConEn |
| `DistillationColumn` | `DistillationColumn` | Inlet #0, Name: Column Feed #1, Type: ConIn; Inlet #1, Name: Column Feed #2, Type: ConIn; Inlet #2, Name: Column Feed #3, Type: ConIn; Inlet #3, Name: Column Feed #4, Type: ConIn; Inlet #4, Name: Column Feed #5, Type: ConIn; Inlet #5, Name: Column Feed #6, Type: ConIn; Inlet #6, Name: Column Feed #7, Type: ConIn; Inlet #7, Name: Column Feed #8, Type: ConIn; Inlet #8, Name: Column Feed #9, Type: ConIn; Inlet #9, Name: Column Feed #10, Type: ConIn; Inlet #10, Name: Reboiler Duty, Type: ConEn; Outlet #0, Name: Distillate, Type: ConOut; Outlet #1, Name: Bottoms, Type: ConOut; Outlet #2, Name: Side Draw #1, Type: ConOut; Outlet #3, Name: Side Draw #2, Type: ConOut; Outlet #4, Name: Side Draw #3, Type: ConOut; Outlet #5, Name: Side Draw #4, Type: ConOut; Outlet #6, Name: Side Draw #5, Type: ConOut; Outlet #7, Name: Side Draw #6, Type: ConOut; Outlet #8, Name: Side Draw #7, Type: ConOut; Outlet #9, Name: Overhead Vapor, Type: ConOut; Outlet #10, Name: Condenser Duty, Type: ConEn |
| `AbsorptionColumn` | `AbsorptionColumn` | Inlet #0, Name: Column Feed #1, Type: ConIn; Inlet #1, Name: Column Feed #2, Type: ConIn; Inlet #2, Name: Column Feed #3, Type: ConIn; Inlet #3, Name: Column Feed #4, Type: ConIn; Inlet #4, Name: Column Feed #5, Type: ConIn; Inlet #5, Name: Column Feed #6, Type: ConIn; Inlet #6, Name: Column Feed #7, Type: ConIn; Inlet #7, Name: Column Feed #8, Type: ConIn; Inlet #8, Name: Column Feed #9, Type: ConIn; Inlet #9, Name: Column Feed #10, Type: ConIn; Outlet #0, Name: Top Product, Type: ConOut; Outlet #1, Name: Bottoms Product, Type: ConOut; Outlet #2, Name: Side Draw #1, Type: ConOut; Outlet #3, Name: Side Draw #2, Type: ConOut; Outlet #4, Name: Side Draw #3, Type: ConOut; Outlet #5, Name: Side Draw #4, Type: ConOut; Outlet #6, Name: Side Draw #5, Type: ConOut; Outlet #7, Name: Side Draw #6, Type: ConOut; Outlet #8, Name: Side Draw #7, Type: ConOut; Outlet #9, Name: Side Draw #8, Type: ConOut |
| `OT_EnergyRecycle` | `EnergyRecycle` | Inlet #0, Name: Inlet, Type: ConEn; Outlet #0, Name: Outlet, Type: ConEn |
| `ComponentSeparator` | `ComponentSeparator` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet 1, Type: ConOut; Outlet #1, Name: Outlet 2, Type: ConOut; Energy Stream, Name: Energy Stream, Type: ConEn |
| `OrificePlate` | `OrificePlate` | Inlet #0, Name: Inlet Stream, Type: ConIn; Outlet #0, Name: Outlet Stream, Type: ConOut |
| `CustomUO` | `CustomUO` | Inlet #0, Name: Inlet #1, Type: ConIn; Inlet #1, Name: Inlet #2, Type: ConIn; Inlet #2, Name: Inlet #3, Type: ConIn; Inlet #3, Name: Inlet Energy, Type: ConEn; Inlet #4, Name: Inlet #4, Type: ConIn; Inlet #5, Name: Inlet #5, Type: ConIn; Inlet #6, Name: Inlet #6, Type: ConIn; Outlet #0, Name: Outlet #1, Type: ConOut; Outlet #1, Name: Outlet #2, Type: ConOut; Outlet #2, Name: Outlet #3, Type: ConOut; Outlet #3, Name: Outlet Energy, Type: ConEn; Outlet #4, Name: Outlet #4, Type: ConIn; Outlet #5, Name: Outlet #5, Type: ConIn; Outlet #6, Name: Outlet #6, Type: ConIn |
| `ExcelUO` | `ExcelUO` | Inlet #0, Name: Inlet #1, Type: ConIn; Inlet #1, Name: Inlet #2, Type: ConIn; Inlet #2, Name: Inlet #3, Type: ConIn; Inlet #3, Name: Inlet #4, Type: ConIn; Inlet #4, Name: I/O Energy, Type: ConEn; Outlet #0, Name: Outlet #1, Type: ConOut; Outlet #1, Name: Outlet #2, Type: ConOut; Outlet #2, Name: Outlet #3, Type: ConOut; Outlet #3, Name: Outlet #4, Type: ConOut |
| `FlowsheetUO` | `Flowsheet` | Inlet #0, Name: Inlet #1, Type: ConIn; Inlet #1, Name: Inlet #2, Type: ConIn; Inlet #2, Name: Inlet #3, Type: ConIn; Inlet #3, Name: Inlet #4, Type: ConIn; Inlet #4, Name: Inlet #5, Type: ConIn; Inlet #5, Name: Inlet #6, Type: ConIn; Inlet #6, Name: Inlet #7, Type: ConIn; Inlet #7, Name: Inlet #8, Type: ConIn; Inlet #8, Name: Inlet #9, Type: ConIn; Inlet #9, Name: Inlet #10, Type: ConIn; Outlet #0, Name: Outlet #1, Type: ConOut; Outlet #1, Name: Outlet #2, Type: ConOut; Outlet #2, Name: Outlet #3, Type: ConOut; Outlet #3, Name: Outlet #4, Type: ConOut; Outlet #4, Name: Outlet #5, Type: ConOut; Outlet #5, Name: Outlet #6, Type: ConOut; Outlet #6, Name: Outlet #7, Type: ConOut; Outlet #7, Name: Outlet #8, Type: ConOut; Outlet #8, Name: Outlet #9, Type: ConOut; Outlet #9, Name: Outlet #10, Type: ConOut |
| `SolidSeparator` | `SolidsSeparator` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet 1, Type: ConOut; Outlet #1, Name: Outlet 2, Type: ConOut |
| `Filter` | `Filter` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Filtrate, Type: ConOut; Outlet #1, Name: Retentate, Type: ConOut; Energy Stream, Name: Energy Stream, Type: ConEn |
| `AnalogGauge` | `AnalogGauge` | Energy Stream, Name: , Type: ConEn |
| `DigitalGauge` | `DigitalGauge` | Energy Stream, Name: , Type: ConEn |
| `LevelGauge` | `LevelGauge` | Energy Stream, Name: , Type: ConEn |
| `Controller_PID` | `PIDController` |  |
| `Switch` | `Switch` | Energy Stream, Name: , Type: ConEn |
| `Input` | `Input` | Energy Stream, Name: , Type: ConEn |
| `WindTurbine` | `WindTurbine` | Energy Stream, Name: , Type: ConEn |
| `HydroelectricTurbine` | `HydroelectricTurbine` | Energy Stream, Name: , Type: ConEn |
| `SolarPanel` | `SolarPanel` | Energy Stream, Name: , Type: ConEn |
| `PEMFuelCell` | `PEMFC_Amphlett` | Energy Stream, Name: , Type: ConEn |
| `WaterElectrolyzer` | `WaterElectrolyzer` | Energy Stream, Name: , Type: ConEn |
| `RCT_GibbsReaktoro` | `Reactor_ReaktoroGibbs` | Energy Stream, Name: , Type: ConEn |
| `Mixer` | `Mixer` | Inlet #0, Name: Inlet Stream 1, Type: ConIn; Inlet #1, Name: Inlet Stream 2, Type: ConIn; Inlet #2, Name: Inlet Stream 3, Type: ConIn; Inlet #3, Name: Inlet Stream 4, Type: ConIn; Inlet #4, Name: Inlet Stream 5, Type: ConIn; Inlet #5, Name: Inlet Stream 6, Type: ConIn; Outlet #0, Name: Mixed Stream, Type: ConOut |
| `Splitter` | `Splitter` | Inlet #0, Name: Inlet, Type: ConIn; Outlet #0, Name: Outlet 1, Type: ConOut; Outlet #1, Name: Outlet 2, Type: ConOut; Outlet #2, Name: Outlet 3, Type: ConOut |
| `Controller_Python` | `PythonController` |  |

## Could not be constructed

- `NodeEn`
- `TPVessel`
- `Nenhum`
- `GO_Table`
- `GO_Text`
- `GO_Image`
- `GO_FloatingTable`
- `RefluxedAbsorber`
- `ReboiledAbsorber`
- `GO_Animation`
- `CapeOpenUO`
- `GO_MasterTable`
- `GO_SpreadsheetTable`
- `GO_Rectangle`
- `CompressorExpander`
- `HeaterCooler`
- `GO_Chart`
- `GO_InputControl`
- `External`
- `GO_HTMLText`
- `GO_Button`
- `AirCooler2`
- `EnergyMixer`
- `Dummy`
- `SolidOps`

## Calculation modes

### NodeIn

- `PressureCalculation`: Average, Maximum, Minimum

### NodeOut

- `OperationMode`: SplitRatios, StreamMassFlowSpec, StreamMoleFlowSpec

### Pump

- `CalcMode`: Delta_P, OutletPressure, EnergyStream, Curves, Power

### Vessel

- `CalculationMode`: Adiabatic, Legacy, HeatingCoolingIsothermic, HeatingCoolingIsobaric
- `PressureCalculation`: Average, Maximum, Minimum

### MaterialStream

- `FloatingTableAmountBasis`: Molar_Fractions, Mass_Fractions, Volumetric_Fractions, Molar_Flows, Mass_Flows, Volumetric_Flows, DefaultBasis
- `DefinedFlow`: Mass, Mole, Volumetric
- `ForcePhase`: None, Vapor, Liquid, Solid, GlobalDef
- `SpecType`: Temperature_and_Pressure, Pressure_and_Enthalpy, Pressure_and_Entropy, Pressure_and_VaporFraction, Temperature_and_VaporFraction, Pressure_and_SolidFraction, Volume_and_Temperature, Volume_and_Enthalpy, Volume_and_Entropy
- `CompositionBasis`: Molar_Fractions, Mass_Fractions, Volumetric_Fractions, Molar_Flows, Mass_Flows, Volumetric_Flows, DefaultBasis
- `StreamType`: Feed, Product, Recycle_In, Recycle_Out, Inner, Undefined

### Compressor

- `CalcMode`: OutletPressure, Delta_P, EnergyStream, PowerRequired, Head, Curves, PressureRatio
- `ProcessPath`: Adiabatic, Polytropic

### Expander

- `CalcMode`: OutletPressure, Delta_P, PowerGenerated, Head, Curves, PressureRatio
- `ProcessPath`: Adiabatic, Polytropic

### Cooler

- `CalcMode`: HeatRemoved, OutletTemperature, OutletVaporFraction, TemperatureChange, EnergyStream

### Heater

- `CalcMode`: HeatAdded, OutletTemperature, EnergyStream, OutletVaporFraction, TemperatureChange, HeatAddedRemoved

### Pipe

- `Specification`: Length, OutletPressure, OutletTemperature
- `SelectedFlowPackage`: Beggs_Brill, Lockhart_Martinelli, Petalas_Aziz

### Valve

- `DefinedOpeningKvRelationShipType`: Linear, EqualPercentage, QuickOpening, UserDefined, DataTable
- `FlowCoefficient`: Kv, Cv
- `CalcMode`: DeltaP, OutletPressure, Kv_Liquid, Kv_Gas, Kv_Steam, Kv_General

### OT_Spec

- `SpecCalculationMode`: GlobalSetting, AfterSourceObject, BeforeTargetObject, BeforeFlowsheet, AfterFlowsheet, AfterObject, BeforeObject

### OT_Recycle

- `AccelerationMethod`: None, Wegstein, Dominant_Eigenvalue, GlobalBroyden

### RCT_Conversion

- `ReactorOperationMode`: Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic

### RCT_Equilibrium

- `ReactorOperationMode`: Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic

### RCT_Gibbs

- `ReactivePhaseBehavior`: CalculateEquilibrium, Vapor, Liquid, Solid
- `ReactorOperationMode`: Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic

### RCT_CSTR

- `ReactorOperationMode`: Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic

### RCT_PFR

- `ReactorSizingType`: Length, Diameter
- `ReactorOperationMode`: Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic

### HeatExchanger

- `FlowDir`: CounterCurrent, CoCurrent
- `DefinedTemperature`: Hot_Fluid, Cold_Fluid
- `CalculationMode`: CalcTempHotOut, CalcTempColdOut, CalcBothTemp, CalcBothTemp_UA, CalcArea, ShellandTube_Rating, ShellandTube_CalcFoulingFactor, PinchPoint, ThermalEfficiency, OutletVaporFraction1, OutletVaporFraction2

### DistillationColumn

- `SolverScheme`: Ideal_K_Init, Ideal_Enthalpy_Init, Ideal_K_and_Enthalpy_Init, Direct
- `CondenserType`: Total_Condenser, Partial_Condenser, Full_Reflux
- `ColumnType`: DistillationColumn, AbsorptionColumn, ReboiledAbsorber, RefluxedAbsorber

### AbsorptionColumn

- `OperationMode`: Absorber, Extractor
- `SolverScheme`: Ideal_K_Init, Ideal_Enthalpy_Init, Ideal_K_and_Enthalpy_Init, Direct
- `CondenserType`: Total_Condenser, Partial_Condenser, Full_Reflux
- `ColumnType`: DistillationColumn, AbsorptionColumn, ReboiledAbsorber, RefluxedAbsorber

### OT_EnergyRecycle

- `AccelerationMethod`: None, Wegstein, Dominant_Eigenvalue, GlobalBroyden

### OrificePlate

- `OrifType`: CornerTaps, FlangeTaps, RadiusTaps
- `CalculationMethod`: Homogeneous, Slip

### CustomUO

- `ExecutionEngine`: IronPython, PythonNET

### FlowsheetUO

- `MassTransferMode`: CompoundMassFlows, CompoundMoleFlows, CompoundMassFractions, CompoundMoleFractions

### Filter

- `CalcMode`: Design, Simulation

### AnalogGauge

- `SelectedPropertyType`: accel, activity, activityCoefficient, area, boilingPointTemperature, cakeresistance, cinematic_viscosity, compressibility, compressibilityFactor, deltaP, deltaT, density, diameter, distance, enthalpy, entropy, excessEnthalpy, excessEntropy, force, foulingfactor, fugacity, fugacityCoefficient, gor, head, heat_transf_coeff, heatCapacityCp, heatCapacityCv, heatflow, idealGasHeatCapacity, jouleThomsonCoefficient, kvalue, logFugacityCoefficient, logKvalue, mass, mass_conc, massflow, massfraction, mediumresistance, meltingTemperature, molar_conc, molar_enthalpy, molar_entropy, molar_volume, molarflow, molarfraction, molecularWeight, pressure, reac_rate, reac_rate_heterog, spec_vol, speedOfSound, surfaceTension, temperature, thermalConductivity, thermalConductivityOfLiquid, thermalConductivityOfVapor, thickness, time, vaporPressure, velocity, viscosity, viscosityOfLiquid, viscosityOfVapor, volume, volumetricFlow, diffusivity, none, conductance, heat, mole, emission_factor, specificpower

### DigitalGauge

- `SelectedPropertyType`: accel, activity, activityCoefficient, area, boilingPointTemperature, cakeresistance, cinematic_viscosity, compressibility, compressibilityFactor, deltaP, deltaT, density, diameter, distance, enthalpy, entropy, excessEnthalpy, excessEntropy, force, foulingfactor, fugacity, fugacityCoefficient, gor, head, heat_transf_coeff, heatCapacityCp, heatCapacityCv, heatflow, idealGasHeatCapacity, jouleThomsonCoefficient, kvalue, logFugacityCoefficient, logKvalue, mass, mass_conc, massflow, massfraction, mediumresistance, meltingTemperature, molar_conc, molar_enthalpy, molar_entropy, molar_volume, molarflow, molarfraction, molecularWeight, pressure, reac_rate, reac_rate_heterog, spec_vol, speedOfSound, surfaceTension, temperature, thermalConductivity, thermalConductivityOfLiquid, thermalConductivityOfVapor, thickness, time, vaporPressure, velocity, viscosity, viscosityOfLiquid, viscosityOfVapor, volume, volumetricFlow, diffusivity, none, conductance, heat, mole, emission_factor, specificpower

### LevelGauge

- `SelectedPropertyType`: accel, activity, activityCoefficient, area, boilingPointTemperature, cakeresistance, cinematic_viscosity, compressibility, compressibilityFactor, deltaP, deltaT, density, diameter, distance, enthalpy, entropy, excessEnthalpy, excessEntropy, force, foulingfactor, fugacity, fugacityCoefficient, gor, head, heat_transf_coeff, heatCapacityCp, heatCapacityCv, heatflow, idealGasHeatCapacity, jouleThomsonCoefficient, kvalue, logFugacityCoefficient, logKvalue, mass, mass_conc, massflow, massfraction, mediumresistance, meltingTemperature, molar_conc, molar_enthalpy, molar_entropy, molar_volume, molarflow, molarfraction, molecularWeight, pressure, reac_rate, reac_rate_heterog, spec_vol, speedOfSound, surfaceTension, temperature, thermalConductivity, thermalConductivityOfLiquid, thermalConductivityOfVapor, thickness, time, vaporPressure, velocity, viscosity, viscosityOfLiquid, viscosityOfVapor, volume, volumetricFlow, diffusivity, none, conductance, heat, mole, emission_factor, specificpower

### Switch

- `SelectedPropertyType`: accel, activity, activityCoefficient, area, boilingPointTemperature, cakeresistance, cinematic_viscosity, compressibility, compressibilityFactor, deltaP, deltaT, density, diameter, distance, enthalpy, entropy, excessEnthalpy, excessEntropy, force, foulingfactor, fugacity, fugacityCoefficient, gor, head, heat_transf_coeff, heatCapacityCp, heatCapacityCv, heatflow, idealGasHeatCapacity, jouleThomsonCoefficient, kvalue, logFugacityCoefficient, logKvalue, mass, mass_conc, massflow, massfraction, mediumresistance, meltingTemperature, molar_conc, molar_enthalpy, molar_entropy, molar_volume, molarflow, molarfraction, molecularWeight, pressure, reac_rate, reac_rate_heterog, spec_vol, speedOfSound, surfaceTension, temperature, thermalConductivity, thermalConductivityOfLiquid, thermalConductivityOfVapor, thickness, time, vaporPressure, velocity, viscosity, viscosityOfLiquid, viscosityOfVapor, volume, volumetricFlow, diffusivity, none, conductance, heat, mole, emission_factor, specificpower

### Input

- `SelectedPropertyType`: accel, activity, activityCoefficient, area, boilingPointTemperature, cakeresistance, cinematic_viscosity, compressibility, compressibilityFactor, deltaP, deltaT, density, diameter, distance, enthalpy, entropy, excessEnthalpy, excessEntropy, force, foulingfactor, fugacity, fugacityCoefficient, gor, head, heat_transf_coeff, heatCapacityCp, heatCapacityCv, heatflow, idealGasHeatCapacity, jouleThomsonCoefficient, kvalue, logFugacityCoefficient, logKvalue, mass, mass_conc, massflow, massfraction, mediumresistance, meltingTemperature, molar_conc, molar_enthalpy, molar_entropy, molar_volume, molarflow, molarfraction, molecularWeight, pressure, reac_rate, reac_rate_heterog, spec_vol, speedOfSound, surfaceTension, temperature, thermalConductivity, thermalConductivityOfLiquid, thermalConductivityOfVapor, thickness, time, vaporPressure, velocity, viscosity, viscosityOfLiquid, viscosityOfVapor, volume, volumetricFlow, diffusivity, none, conductance, heat, mole, emission_factor, specificpower

### RCT_GibbsReaktoro

- `ReactorOperationMode`: Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic

### Mixer

- `PressureCalculation`: Average, Maximum, Minimum

### Splitter

- `OperationMode`: SplitRatios, StreamMassFlowSpec, StreamMoleFlowSpec


## Settable properties (allowlist)

A `dwsim` unit may set and report only these names. The unit in parentheses is the SI value DWSIM stores. Enums are set by name.

- **Pump**: `DeltaP` (Pa); `POut` (Pa); `Eficiencia` (percent); `Efficiency` (percent); `OutletTemperature` (K); `CalcMode` (Delta_P, OutletPressure, EnergyStream, Curves, Power)
- **Valve**: `DeltaP` (Pa); `PressureDrop` (Pa); `OutletPressure` (Pa); `Kv` (Kv); `CalcMode` (DeltaP, OutletPressure, Kv_Liquid, Kv_Gas, Kv_Steam, Kv_General)
- **Heater**: `DeltaQ` (kW); `HeatDuty` (kW); `OutletTemperature` (K); `PressureDrop` (Pa); `TemperatureChange` (K); `Efficiency` (fraction); `CalcMode` (HeatAdded, OutletTemperature, EnergyStream, OutletVaporFraction, TemperatureChange, HeatAddedRemoved)
- **Cooler**: `DeltaQ` (kW); `HeatDuty` (kW); `OutletTemperature` (K); `PressureDrop` (Pa); `TemperatureChange` (K); `Efficiency` (fraction); `CalcMode` (HeatRemoved, OutletTemperature, OutletVaporFraction, TemperatureChange, EnergyStream)
- **HeatExchanger**: `Area` (m2); `OverallCoefficient` (W/m2K); `Q` (kW); `HotSidePressureDrop` (Pa); `ColdSidePressureDrop` (Pa); `CalcMode` (CalcTempHotOut, CalcTempColdOut, CalcBothTemp, CalcBothTemp_UA, CalcArea, ShellandTube_Rating, ShellandTube_CalcFoulingFactor, PinchPoint, ThermalEfficiency, OutletVaporFraction1, OutletVaporFraction2)
- **Compressor**: `POut` (Pa); `DeltaP` (Pa); `DeltaQ` (kW); `AdiabaticEfficiency` (percent); `PolytropicEfficiency` (percent); `PressureRatio` (1); `CalcMode` (OutletPressure, Delta_P, EnergyStream, PowerRequired, Head, Curves, PressureRatio); `ProcessPath` (Adiabatic, Polytropic)
- **Expander**: `POut` (Pa); `DeltaP` (Pa); `DeltaQ` (kW); `AdiabaticEfficiency` (percent); `PolytropicEfficiency` (percent); `PressureRatio` (1); `CalcMode` (OutletPressure, Delta_P, PowerGenerated, Head, Curves, PressureRatio); `ProcessPath` (Adiabatic, Polytropic)
- **Tank**: `Volume` (m3)
- **Vessel**: `FlashPressure` (Pa); `FlashTemperature` (K); `CalculationMode` (Adiabatic, Legacy, HeatingCoolingIsothermic, HeatingCoolingIsobaric); `PressureCalculation` (Average, Maximum, Minimum)
- **Mixer**: `PressureCalculation` (Average, Maximum, Minimum)
- **Splitter**: `StreamFlowSpec` (kg/s); `Stream2FlowSpec` (kg/s); `OperationMode` (SplitRatios, StreamMassFlowSpec, StreamMoleFlowSpec)
- **OrificePlate**: `OrificeDiameter` (m); `InternalPipeDiameter` (m); `Beta` (1); `OverallPressureDrop` (Pa); `OrificePressureDrop` (Pa); `OrifType` (CornerTaps, FlangeTaps, RadiusTaps); `CalculationMethod` (Homogeneous, Slip)
- **SolidSeparator**: `SeparationEfficiency` (fraction); `LiquidSeparationEfficiency` (fraction)
- **Filter**: `PressureDrop` (Pa); `TotalFilterArea` (m2); `SubmergedAreaFraction` (fraction); `FilterCycleTime` (s); `CakeRelativeHumidity` (fraction); `SpecificCakeResistance` (m/kg); `FilterMediumResistance` (1/m); `CalcMode` (Design, Simulation)
- **ShortcutColumn**: `StageHeight` (m)
- **DistillationColumn**: `NumberOfStages` (1); `RefluxRatio` (1); `ColumnPressureDrop` (Pa); `CondenserDeltaP` (Pa); `CondenserDuty` (kW); `ReboilerDuty` (kW); `TraySpacing` (m); `DistillateFlowRate` (mol/s); `MaxIterations` (1); `CondenserType` (Total_Condenser, Partial_Condenser, Full_Reflux)
- **AbsorptionColumn**: `NumberOfStages` (1); `ColumnPressureDrop` (Pa); `TraySpacing` (m); `MaxIterations` (1); `OperationMode` (Absorber, Extractor)
- **RCT_Conversion**: `OutletTemperature` (K); `ReactorOperationMode` (Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic)
- **RCT_Equilibrium**: `OutletTemperature` (K); `ReactorOperationMode` (Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic)
- **RCT_Gibbs**: `OutletTemperature` (K); `ReactorOperationMode` (Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic)
- **RCT_CSTR**: `Volume` (m3); `Headspace` (fraction); `OutletTemperature` (K); `CatalystAmount` (kg); `ReactorOperationMode` (Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic)
- **RCT_PFR**: `Length` (m); `Diameter` (m); `Volume` (m3); `CatalystLoading` (kg/m3); `CatalystVoidFraction` (fraction); `CatalystParticleDiameter` (m); `UseUserDefinedPressureDrop` (bool); `UserDefinedPressureDrop` (Pa); `OutletTemperature` (K); `ReactorOperationMode` (Isothermic, Adiabatic, OutletTemperature, NonIsothermalNonAdiabatic)
- **OT_Recycle**: `MaximumIterations` (1); `SmoothingFactor` (1); `AccelerationMethod` (None, Wegstein, Dominant_Eigenvalue, GlobalBroyden)
- **Pipe**: `OutletPressure` (Pa); `OutletTemperature` (K); `Specification` (Length, OutletPressure, OutletTemperature)

The port table above is every ObjectType this install could construct. The spec allowlist is the shorter list in this section. NodeIn is a Mixer and NodeOut is a Splitter; use Mixer and Splitter.

## Reactor and column wrappers

Conversion, equilibrium, CSTR and PFR are `type: reactor`. The rigorous column is `type: distillation`. Both read numbers from DWSIM (conversion from compound molar flows, duties from DeltaQ / CondenserDuty / ReboilerDuty, stage traffic from the column profile text). Stage Parameter vapour and liquid flows stay at zero; the profile string is the source.

DWSIM does not report a flood fraction. The Fair screen uses per-stage mass flows and densities from that profile, with tray spacing and diameter from the unit's limits (`diameter_m` required, `tray_spacing_m` default 0.5, `flood_frac_max` default 0.8). Net area is 90 percent of the shell. Citation is in `fair_flood_fraction` in `plantagent/process.py`.

## Replacing rated equipment

An operating change cannot edit `limits.*`. A physical replacement of an existing unit is explicit:

```json
{"replace_unit": "K 2750", "new_rating": {"diameter_m": 0.6},
 "basis": "Fair flooding below 80 percent at 120 percent feed", "vendor_confirm": true}
```

Only numeric rating or geometry fields already present on that unit or its limits can change. The server re-solves the same process with the new rating and keeps vendor confirmation as an open engineering item; a plain limit edit remains refused.

P&ID coverage is topology-based. It follows model streams through valves and routing nodes, recognises explicit recycle tears and grouped P&ID items, and reports capacity-relevant process lines separately from unmodelled relief, drain and utility lines.
