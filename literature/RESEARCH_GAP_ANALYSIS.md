# Research Gap Analysis: All-Sky Geostationary Infrared Observation Operators

This document synthesizes the findings of the literature survey to establish the scientific motivation and research gap for the proposed master's thesis topic: *A differentiable observation operator for all-sky assimilation of FY-4B AGRI water-vapour channel images*.

---

### 1. The operational data assimilation bottleneck

Numerical weather prediction models simulate atmospheric dynamics with grid spacings between 1 and 10 kilometres. Geostationary meteorological satellites observe the atmosphere continuously at 5 to 15 minute temporal resolution and 2 to 4 kilometre spatial resolution. Water-vapour channels on instruments such as FY-4B AGRI (channels 9, 10, and 11 at 6.25, 7.10, and 7.42 µm) record the horizontal structure of tropospheric moisture, upper-level vorticity, and vertical motion.

Operational data assimilation systems discard most of these measurements because clouds scatter and absorb thermal infrared radiation non-linearly (Geer et al., 2018, DOI: 10.1002/qj.3202; Li et al., 2021, DOI: 10.1007/s00376-021-1088-9). Discarding cloudy scenes creates a sampling bias. The numerical model receives observational updates in quiescent, clear-sky regions. Active weather systems, tropical cyclones, and severe convective cells remain unconstrained by satellite imagery.

---

### 2. Methodological classifications and their limitations

The literature reveals three primary methodological groups developed to address satellite radiances:

#### Group 1: Clear-sky filtering and cloud clearing
- Operational examples: ECMWF (McNally, 2009, DOI: 10.1002/qj.426), Met Office (Saunders et al., 2018, DOI: 10.5194/gmd-11-2717-2018), and CMA (Xu, Liu et al., 2023, DOI: 10.1007/s00376-022-1380-3).
- What it solves: It restricts assimilation to cloud-free fields-of-view. This restriction preserves linear radiative assumptions and permits standard gaussian error models.
- What it leaves unsolved: It removes all observations within storms. Convective cloud bands and precipitation cores are completely masked out. Model forecast errors grow unchecked in severe weather regimes.

#### Group 2: Fast one-dimensional physical radiative transfer models
- Operational examples: RTTOV-CLD (Saunders et al., 2018) and CRTM (Zhu et al., 2016, DOI: 10.1175/MWR-D-15-0445.1).
- What it solves: It calculates scattering from liquid water and ice hydrometeors across multiple stream approximations. This approach makes all-sky forward calculations possible for microwave channels and limited infrared channels (Okamoto et al., 2023, DOI: 10.1002/qj.4516; Geer et al., 2019, DOI: 10.5194/amt-12-4903-2019).
- What it leaves unsolved: The operator operates strictly on independent one-dimensional atmospheric columns. When cloud optical depth exceeds three ($\tau > 3$), atmospheric transmittance from sub-cloud levels to space drops to zero. The analytical Jacobian $\partial \mathcal{H} / \partial q$ evaluated with respect to water vapour below the cloud top collapses to zero. The Jacobian loses mathematical rank. Across cloud boundaries, condensation operates as a step threshold. This threshold causes discontinuous gradient spikes.

#### Group 3: Machine learning emulators and retrievals
- Published examples: Emulators (Ukkonen et al., 2020, DOI: 10.1029/2020MS002226), deep learning retrievals (Hilburn et al., 2021, DOI: 10.1175/JAMC-D-20-0084.1), and column observation operators (Liang et al., 2023, DOI: 10.2151/jmsj.2023-005).
- What it solves: Emulators accelerate physical radiation computations by an order of magnitude. Retrievals extract geophysical fields directly from imagery. Column operators map single profiles to radiances in ensemble Kalman filters.
- What it leaves unsolved: Emulators reproduce the exact physical limitations and Jacobian collapse of the 1D parent models. Retrievals perform an inverse mapping ($y \mapsto x$) instead of a forward observation operator ($x \mapsto y$). They cannot be used in variational cost functions where the gradient $\partial \mathcal{H} / \partial x$ is required. Column operators neglect spatial image context and lack verified differentiable adjoint gradients.

---

### 3. Disagreements and the shared unresolved research gap

Existing approaches disagree on three fundamental operational choices:
1. Control vector composition: ECMWF, JMA, and NCEP omit hydrometeors from the variational control vector. They update only specific humidity, temperature, and wind. The forecast model physics then forms clouds in the subsequent integration step. In contrast, convective-scale experimental systems attempt to include cloud liquid and ice mixing ratios directly, but face filter divergence and non-gaussian error growth.
2. Observation error treatment: Operational centres disagree on the construction of the observation error covariance matrix $\mathbf{R}$. Some use symmetric cloud amount inflation (Geer and Bauer, 2011, DOI: 10.1002/qj.830; Okamoto et al., 2023). Others rely on empirical thinning down to 80 or 100 kilometre resolution to suppress unresolved cloud representation errors and avoid spatial correlations.
3. Gradient mitigation: When a model is clear but the satellite observes a cold convective cloud, the linear Jacobian evaluated at the background state triggers the false-moistening trap. Centres handle this through ad hoc measures: zeroing the Jacobian below diagnosed cloud top or inflating observation error standard deviations up to 25 K.

Despite these operational adjustments, all reviewed systems share one fundamental limitation:

> No published observation operator provides a two-dimensional, differentiable mapping from numerical weather prediction model fields to geostationary infrared water-vapour images that supplies physically consistent, non-zero gradients inside cloudy scenes.

---

### 4. Proposed research topic and scientific motivation

The identified research gap directly motivates the proposed master's thesis topic:

A differentiable observation operator for all-sky assimilation of FY-4B AGRI water-vapour channel images

Investigating this topic addresses three specific scientific goals:
1. Forward mapping ($x \mapsto y$) on a two-dimensional image grid: Constructing an operator that ingests three-dimensional model thermodynamic fields and cloud states over a convective domain and outputs two-dimensional top-of-atmosphere brightness temperatures for FY-4B AGRI water-vapour channels (C09 at 6.25 µm, C10 at 7.10 µm, C11 at 7.42 µm, anchored by window channel C12 at 10.8 µm).
2. Differentiability inside cloud ($\partial \mathcal{H} / \partial x$): Designing the operator architecture so that partial derivatives with respect to temperature and moisture remain smooth, continuous, and physically informative inside cloudy regimes. This design avoids the rank collapse and step discontinuities of one-dimensional radiative transfer solvers.
3. Structured observation error ($\mathbf{R}$): Establishing a spatial error covariance structure that accounts for two-dimensional spatial correlations across cloud structures without relying on diagonal pixel independence or aggressive 80-kilometre thinning.

This research bridges the gap between satellite remote sensing, atmospheric physics, and variational data assimilation for the Fengyun-4B operational series.
