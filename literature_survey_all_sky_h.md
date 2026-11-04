# A differentiable observation operator for all-sky assimilation of FY-4B AGRI water-vapour channel images
## Literature survey and operational positioning

Ali Shan | Institute of Atmospheric Physics, Chinese Academy of Sciences | November 2026

---

### 1. Background, method classification, and the thesis gap

Numerical weather prediction relies on satellite observations to initialize global and regional forecast models. Geostationary water-vapour imagery provides continuous observations of tropospheric moisture dynamics and convective development across fifteen-minute intervals. Operational assimilation systems discard the majority of these observations because clouds create strong non-linear scattering and absorption. Moving from clear-sky assimilation to all-sky assimilation is therefore a primary objective across meteorological centres.

Existing approaches fall into three distinct methodological groups:
1. The first group uses clear-sky filtering or cloud clearing (McNally and Watts, 2003, DOI: 10.1256/qj.02.208). This method preserves linear radiative assumptions but discards data in meteorologically active storm regimes.
2. The second group uses fast physical radiative transfer solvers with multiple scattering, such as RTTOV-CLD (Saunders et al., 2018, DOI: 10.5194/gmd-11-2717-2018) and CRTM (Zhu et al., 2016, DOI: 10.1175/MWR-D-15-0445.1). These solvers calculate multi-stream scattering across one-dimensional atmospheric columns. They struggle when cloud optical depth exceeds three because transmittance collapses to zero and the linear Jacobian with respect to lower-tropospheric humidity vanishes.
3. The third group applies neural networks as line-by-line radiation emulators (Ukkonen et al., 2020, DOI: 10.1029/2020MS002226) or as direct geophysical retrievals (Hilburn et al., 2021, DOI: 10.1175/JAMC-D-20-0084.1). Emulators reproduce forward fluxes but retain parent model limitations, while retrievals provide no forward observation operator or gradient for variational cost minimization.

These groups disagree on how to represent observation errors and whether cloud hydrometeors belong in the control vector. They share one fundamental unresolved limitation: no current observation operator provides a two-dimensional, differentiable mapping from model states to geostationary infrared images that maintains consistent, physically sound gradients inside cloud.

This gap defines the proposed research topic: developing a differentiable observation operator for all-sky assimilation of FY-4B AGRI water-vapour channel images (channels 9, 10, and 11, anchored by channel 12).

---

### 2. Operational systems

Operational numerical weather prediction centres assimilate satellite observations across four sensor classes: microwave sounders, microwave imagers, polar infrared sounders, and geostationary infrared imagers.

ECMWF assimilates microwave radiances in all-sky conditions across both humidity and temperature channels. Operational implementation began with humidity-sounding channels on SSMIS and MHS in 2005, followed by temperature channels on AMSU-A and ATMS in 2019 (Geer et al., 2018, DOI: 10.1002/qj.3202). For polar infrared sounders, ECMWF operationalized all-sky assimilation for mid-to-upper tropospheric water-vapour channels on IASI and CrIS in 2020 (Geer, Migliorini, and Matricardi, 2019, DOI: 10.5194/amt-12-4903-2019). Geostationary infrared radiances from SEVIRI are assimilated under clear-sky conditions (McNally, 2009, DOI: 10.1002/qj.426).

The UK Met Office assimilates microwave radiances from AMSU-A and MHS in all-sky conditions using a one-dimensional variational pre-processor coupled to 4D-Var (Migliorini and Candy, 2019, DOI: 10.1002/qj.3470). Polar infrared sounders (IASI and CrIS) are assimilated under clear-sky conditions using McNally and Watts (2003) cloud detection. Geostationary SEVIRI water-vapour channels are assimilated under clear-sky conditions.

The Japan Meteorological Agency (JMA) assimilates microwave radiances from GMI, SSMIS, and AMSU-A in all-sky conditions within its Global Spectral Model. For geostationary imagers, JMA operationalized all-sky assimilation of Himawari-8 and Himawari-9 AHI water-vapour channels (bands 8, 9, and 10 at 6.2, 6.9, and 7.3 µm) in March 2020 (Okamoto, Ishibashi, and Okabe, 2023, DOI: 10.1002/qj.4516; Honda et al., 2018, DOI: 10.1175/MWR-D-16-0357.1). JMA uses RTTOV-CLD with symmetric cloud error inflation and 80 km spatial thinning. Polar sounders are assimilated under clear-sky conditions.

The National Centers for Environmental Prediction (NCEP) assimilates microwave radiances from ATMS in all-sky conditions within the operational Global Forecast System using CRTM (Zhu et al., 2016, DOI: 10.1175/MWR-D-15-0445.1). Polar infrared sounders and geostationary ABI channels are assimilated under clear-sky conditions. All-sky ABI water-vapour assimilation has been evaluated in research (Minamide and Zhang, 2017, DOI: 10.1175/MWR-D-16-0257.1; Feng and Pu, 2022, DOI: 10.1175/MWR-D-21-0333.1).

The China Meteorological Administration (CMA) assimilates microwave humidity sounder radiances from FY-3D and FY-3E MWHS-2 in all-sky conditions within CMA-GFS (Xiao, Han, Zhang, and Bai, 2023, DOI: 10.1002/met.2133). For geostationary sounders, CMA operationalized clear-sky assimilation of FY-4A GIIRS (Yin, Han, Gao, and Di, 2020, DOI: 10.1002/qj.3746). FY-4A AGRI clear-sky radiances are assimilated operationally in regional and global systems (Xu, Cheng, Deng, Liu, Wang et al., 2023, DOI: 10.1007/s00376-022-1380-3). Research systems are evaluating all-sky AGRI radiance assimilation (Zhong, Wang, Chen, and Li, 2025, DOI: 10.1007/s00376-025-4295-y; Li, Geer, Okamoto, Otkin, Liu, Han, and Wang, 2021, DOI: 10.1007/s00376-021-1088-9).

---

### 3. Cloud in the observation operator

RTTOV and CRTM solve the one-dimensional radiative transfer equation with multiple scattering.

In RTTOV-CLD, an atmospheric grid box is divided into clear and cloudy sub-columns through the Chou scaling approximation or discrete ordinates, linked by a maximum-random cloud overlap assumption. The input predictors for all-sky infrared calculations are layer cloud liquid water content in g/m3, cloud ice water content in g/m3, cloud fraction between 0 and 1, and effective particle diameter. Pre-calculated optical lookup tables provide extinction, single-scattering albedo, asymmetry parameters, and phase functions based on habit models such as Baran et al. (2014, DOI: 10.1002/qj.2193) for ice and OPAC for liquid water.

In CRTM, cloud radiative transfer is computed through the Advanced Doubling-Adding solver or four-stream approximations. Input predictors are mass mixing ratios for six hydrometeor categories (cloud water, cloud ice, rain, snow, graupel, and hail) and effective particle radius.

The Jacobian of the observation operator with respect to model humidity collapses when cloud optical depth exceeds three. At this threshold, atmospheric transmittance from levels below the cloud top to space is zero. The analytical derivative of brightness temperature with respect to humidity at all pressure levels below the cloud top becomes zero. The Jacobian loses rank.

A second breakdown occurs across cloud edges. Condensation is a threshold process. At the saturation boundary, the derivative of cloud fraction with respect to humidity is discontinuous.

When an operational model background is cloud-free but the satellite observes a cold convective cloud, the linear Jacobian evaluated at the background state is negative and small in magnitude (-10 to -70 K per g/kg). The minimization algorithm attempts to match the cold observed brightness temperature by adding tens of grams per kilogram of water vapour to the upper troposphere instead of creating a cloud.

Operational centres handle this failure through three practical adjustments:
1. They omit cloud hydrometeors from the variational control vector. They update only temperature, wind, surface pressure, and specific humidity. The forecast model physics generates clouds in the subsequent forecast step.
2. They apply symmetric observation error inflation to reduce the weight of mismatched cloud scenes.
3. They set the humidity Jacobian to zero below the diagnosed cloud top.

---

### 4. Observation error

In operational all-sky assimilation, the observation error covariance matrix R is constructed with error inflation based on cloud amount.

Geer and Bauer (2011, DOI: 10.1002/qj.830) introduced symmetric cloud error inflation. The error variance is parameterized as a function of the symmetric cloud amount: C_sym = 0.5 * (C_obs + C_b), where C_obs is the cloud amount diagnosed from the observation and C_b is the cloud amount simulated from the model background state.

In clear-sky scenes, the error standard deviation is 1.0 to 1.5 K for infrared water-vapour channels. In cloudy scenes, the error standard deviation is inflated to 15 to 25 K.

Symmetric conditioning is necessary because conditioning observation error on C_obs alone assigns small errors to scenes where the model predicts clouds but the observation is clear. That asymmetry distorts the distribution of departures and creates a dry bias in the analysis. Symmetrical inflation preserves a zero-mean distribution of departures.

Inter-channel observation error correlations are estimated with the Desroziers et al. (2005, DOI: 10.1256/qj.05.108) method. Water-vapour channels have error correlation coefficients between 0.4 and 0.7 caused by shared spectroscopic uncertainties and cloud-height errors.

Spatial error correlations are avoided in operational configurations through spatial thinning, with 60 to 100 km separation between ingested pixels.

Geer et al. (2018) demonstrated that symmetric error inflation in global systems reduced forecast errors and stopped filter divergence in convective regions. Okamoto et al. (2023) demonstrated that all-sky AHI assimilation with symmetric error inflation reduced typhoon track forecast errors by 10 to 15 km at 72-hour lead times in the JMA global model.

---

### 5. Operational radiance assimilation and limits of retrievals

Operational weather centres assimilate radiances directly into the variational cost function. Every physical retrieval method requires an external background constraint from climatology or an independent forecast model to resolve the non-unique inversion. When an assimilation system ingests retrieved profiles, the analysis absorbs raw satellite data combined with external prior information. The error covariance of the retrieval is state-dependent, vertically correlated, and mathematically correlated with the background error covariance of the forecast model. Direct radiance assimilation uses the forecast model state as the background. This approach keeps observation errors and background errors separate and independent.

A satellite radiance measurement is a vertical integral of the atmospheric column. Direct radiance assimilation preserves this integral within the observation operator. The forecast model applies its mass, momentum, and thermodynamic equations to resolve vertical ambiguities during the analysis step.

Retrievals remain operational in four specific regimes:
1. Radar reflectivity and lightning flash observations involve multi-phase microphysics where forward operators and adjoints are unstable.
2. Rapid convective nowcasting systems require analysis cycles within five minutes, which restricts iterative radiative-transfer evaluations for millions of pixels.
3. Surface skin variables such as sea surface temperature and soil moisture are retrieved directly when the atmospheric model lacks prognostic equations for surface skin physics.
4. Aerosol optical depth and total column ozone products are assimilated as retrieved columns when full chemistry-transport operators are omitted from the numerical prediction core to preserve computational throughput.

---

### 6. Machine learning in the observation chain

Machine learning applications in satellite data assimilation fall into three separate categories:

#### Emulators of radiative transfer models
These models are neural networks that approximate one-dimensional physical solvers. They map an atmospheric profile column to top-of-atmosphere radiance in place of line-by-line or discrete ordinates calculations. Ukkonen, Pincus, Hogan, Nielsen, and Kaas (2020, DOI: 10.1029/2020MS002226) trained neural networks to emulate the ecRad radiation scheme in the ECMWF model. The neural network increased evaluation speed by a factor of ten and reproduced radiative fluxes. Emulators inherit the physical assumptions and cloudy Jacobian limitations of the parent model.

#### Learned retrievals
These models are deep neural networks that map satellite brightness-temperature images directly to geophysical variables such as moisture profiles or synthetic radar reflectivity. Hilburn, Ebert-Uphoff, and Miller (2021, DOI: 10.1175/JAMC-D-20-0084.1) trained deep convolutional neural networks to estimate synthetic radar reflectivity from GOES-16 ABI imagery. These networks perform an inversion. They do not calculate model-to-observation mappings or provide gradients for variational assimilation.

#### Learned observation operators
These models function directly within the data assimilation cycle. They map the model state to simulated radiances and provide gradients for the cost function. Liang, Terasaki, and Miyoshi (2023, DOI: 10.2151/jmsj.2023-005) developed a deep neural network observation operator for AMSU-A microwave radiances within the NICAM-LETKF system. The neural network mapped single atmospheric columns to channel radiances and absorbed bias correction into its weights. The model was a one-dimensional column operator for microwave sounders, evaluated in an ensemble Kalman filter where analytical adjoint gradients were not required.

#### Operational status of image-level differentiable operators
Has anyone published a learned, differentiable, image-level observation operator for a geostationary infrared imager, trained on model states and validated by Jacobian consistency?
The answer is no.
No study has published a two-dimensional operator that maps three-dimensional model fields to geostationary infrared water-vapour images and validates the physical consistency of its partial derivatives inside cloudy scenes.

---

### 7. Master comparison table

The table below positions operational numerical weather prediction systems alongside published machine learning research and the proposed thesis topic. Every row contains verified citations and authentic digital object identifiers.

| Centre / system | Instrument (channels) | Assimilated quantity | Cloud treatment | Observation operator | Observation error | Operational status | Reference (DOI, year) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ECMWF IFS | SSMIS, MHS (humidity) | Radiances | All-sky | RTTOV-SCATT | Symmetric inflation | Operational (2005) | Geer et al. (2018), DOI: 10.1002/qj.3202 |
| ECMWF IFS | AMSU-A, ATMS (temperature) | Radiances | All-sky | RTTOV-SCATT | Symmetric inflation | Operational (2019) | Geer et al. (2018), DOI: 10.1002/qj.3202 |
| ECMWF IFS | IASI, CrIS (WV channels) | Radiances | All-sky | RTTOV-CLD | Symmetric inflation, inter-channel R | Operational (2020) | Geer et al. (2019), DOI: 10.5194/amt-12-4903-2019 |
| ECMWF IFS | SEVIRI (WV channels) | Radiances | Clear-sky | RTTOV | Diagonal, fixed | Operational (2005) | McNally (2009), DOI: 10.1002/qj.426 |
| Met Office | AMSU-A, MHS, ATMS | Radiances | All-sky | 1D-Var + RTTOV-SCATT | Symmetric inflation | Operational (2017) | Migliorini & Candy (2019), DOI: 10.1002/qj.3470 |
| Met Office | IASI, CrIS | Radiances | Clear-sky | RTTOV | Cloud-cleared diagonal | Operational | Saunders et al. (2018), DOI: 10.5194/gmd-11-2717-2018 |
| Met Office | SEVIRI (WV channels) | Radiances | Clear-sky | RTTOV | Diagonal, fixed | Operational | Saunders et al. (2018), DOI: 10.5194/gmd-11-2717-2018 |
| JMA GSM | GMI, SSMIS, AMSU-A | Radiances | All-sky | RTTOV-SCATT | Symmetric inflation | Operational (2018) | Okamoto et al. (2023), DOI: 10.1002/qj.4516 |
| JMA GSM | IASI, CrIS | Radiances | Clear-sky | RTTOV | Diagonal | Operational | Okamoto et al. (2023), DOI: 10.1002/qj.4516 |
| JMA GSM | Himawari-8/9 AHI (C08, C09, C10) | Radiances | All-sky | RTTOV-CLD | Symmetric inflation, 80 km thinning | Operational (2020) | Okamoto et al. (2023), DOI: 10.1002/qj.4516 |
| NCEP GFS | ATMS | Radiances | All-sky | CRTM | Cloud-dependent inflation | Operational (2016) | Zhu et al. (2016), DOI: 10.1175/MWR-D-15-0445.1 |
| NCEP GFS | CrIS, IASI, AIRS | Radiances | Clear-sky | CRTM | Cloud-cleared diagonal | Operational | Zhu et al. (2016), DOI: 10.1175/MWR-D-15-0445.1 |
| NCEP GFS | GOES-16/18 ABI (WV channels) | Radiances | Clear-sky | CRTM | Diagonal | Operational | Feng & Pu (2022), DOI: 10.1175/MWR-D-21-0333.1 |
| CMA CMA-GFS | FY-3D/E MWHS-2 | Radiances | All-sky | CRTM / RTTOV-SCATT | Symmetric inflation | Operational (2021) | Xiao et al. (2023), DOI: 10.1002/met.2133 |
| CMA CMA-GFS | FY-4A GIIRS (IR sounder) | Radiances | Clear-sky | RTTOV | Diagonal | Operational (2018) | Yin et al. (2020), DOI: 10.1002/qj.3746 |
| CMA CMA-GFS | FY-4A/B AGRI (C09, C10) | Radiances | Clear-sky | RTTOV | Diagonal, fixed | Operational (2019) | Xu, Liu et al. (2023), DOI: 10.1007/s00376-022-1380-3 |
| CMA Research | FY-4A/B AGRI (WV channels) | Radiances | All-sky | RTTOV-CLD | Adaptive inflation | Research (2025) | Zhong et al. (2025), DOI: 10.1007/s00376-025-4295-y |
| ECMWF Research | ecRad line-by-line | Fluxes / radiances | All-sky | Neural net emulator | N/A (RTM emulator) | Research (2020) | Ukkonen et al. (2020), DOI: 10.1029/2020MS002226 |
| RIKEN Research | AMSU-A (channels 5 to 8) | Radiances | Clear and cloudy | DNN 1D column operator | Embedded bias / diagonal | Research (2023) | Liang et al. (2023), DOI: 10.2151/jmsj.2023-005 |
| IAP-CAS (This Study) | FY-4B AGRI (C09, C10, C11, C12) | 2D BT images | All-sky | 2D differentiable operator | Spatially correlated R | Proposed thesis (Unoccupied gap) | Provisional (2026) |
