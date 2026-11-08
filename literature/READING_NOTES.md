# Literature reading log and evaluation notes

This document provides structured reading notes and physical evaluations for the 23 scientific works reviewed in the all-sky satellite data assimilation survey. The evaluation follows the four-part assessment framework requested by Dr. Juanjuan Liu:
1. What problem does the paper address?
2. What method does it use?
3. What are the main findings?
4. What limitations or unresolved problems remain?

---

### Core equations and technical terminology in plain language

#### 1. Radiative transfer in cloudy atmospheres
In clear air, the top-of-atmosphere infrared radiance is the sum of surface emission attenuated by the column and layer-by-layer atmospheric thermal emission. In cloudy conditions, liquid droplets and ice crystals absorb, emit, and scatter photons. The monochromatic radiance $I(\nu)$ along an optical path $s$ satisfies the radiative transfer equation:
$$ \frac{dI(\nu)}{ds} = -\beta_{\text{ext}}(\nu) I(\nu) + \beta_{\text{abs}}(\nu) B(\nu, T) + \frac{\beta_{\text{sca}}(\nu)}{4\pi} \int_{4\pi} P(\nu, \Omega, \Omega') I(\nu, \Omega') d\Omega' $$
Here $\beta_{\text{ext}} = \beta_{\text{abs}} + \beta_{\text{sca}}$ is the extinction coefficient, $B(\nu, T)$ is the Planck function at temperature $T$, and $P(\Omega, \Omega')$ is the scattering phase function. In plain terms, a cloud acts as an elevated, semi-opaque emitter and scatterer. The cloud blocks thermal emission from atmospheric layers below it and substitutes emission at its own local temperature.

#### 2. Chou scaling and stream approximations in RTTOV-CLD
Solving the full angular integral across multiple scattering streams is slow. RTTOV-CLD uses the Chou scaling method. This approximation scales optical depth, single-scattering albedo, and asymmetry parameters into effective absorption optical depths. The solver calculates radiance using two streams (upward and downward) or the Eddington approximation. In plain terms, Chou scaling avoids tracking millions of photon trajectories. It approximates scattering by modifying layer absorption, which enables the code to run in milliseconds per column.

#### 3. Maximum-random cloud overlap
A single vertical grid cell may contain partial cloud cover $C_j$. When multiple vertical layers have partial cloudiness, the radiation scheme must decide how clouds at different heights align. The maximum-random overlap convention assumes that clouds in adjacent vertical layers overlap maximally (they share the same vertical cylinder), whereas clouds separated by clear layers overlap randomly. In plain terms, this assumption calculates how much clear air reaches the satellite without seeing a cloud.

#### 4. The symmetric cloud proxy
In all-sky assimilation, observation departures $y - H(x)$ exhibit errors that grow with cloud amount. If the system scales observation error using only the observed cloud amount $C_{\text{obs}}$, it creates an asymmetric penalty. When the model simulates a cloud but the satellite sees clear sky, the assigned error is small. The analysis then forces the model to remove the cloud rapidly, which creates an artificial drying bias. Geer and Bauer (2011) introduced the symmetric cloud proxy:
$$ C_{\text{sym}} = \frac{1}{2} (C_{\text{obs}} + C_b) $$
Here $C_b$ is the cloud amount diagnosed from the model background state. Symmetrical averaging balances the departure weights and prevents systematic moisture drift.

#### 5. Adaptive observation error inflation
Observation error variance is parameterized as a function of $C_{\text{sym}}$:
$$ \sigma^2(C_{\text{sym}}) = \sigma_{\text{clear}}^2 + (\sigma_{\text{cloudy}}^2 - \sigma_{\text{clear}}^2) \left( \frac{C_{\text{sym}}}{C_{\text{max}}} \right)^p $$
In clear-sky regions ($C_{\text{sym}} \approx 0$), the error standard deviation is 1.0 to 1.5 K. In deep convective regions ($C_{\text{sym}} \approx C_{\text{max}}$), the error standard deviation expands to 15 to 25 K. This expansion reduces the weight of cloudy pixels in the variational cost function when microphysical errors are large.

#### 6. Desroziers diagnostic for observation error covariance
Desroziers et al. (2005) derived an objective diagnostic for observation error covariance $R$ using assimilation residuals:
$$ R_{\text{diag}} = E[d_a d_b^T] = E[(y - H(x_a)) (y - H(x_b))^T] $$
Here $d_b = y - H(x_b)$ is the background departure and $d_a = y - H(x_a)$ is the analysis departure. In plain terms, if background and observation errors are specified accurately, the expected cross-product of background and analysis residuals equals the true observation error covariance matrix.

#### 7. Radiance Jacobian and gradient collapse
The Jacobian matrix $K$ contains partial derivatives of simulated brightness temperature with respect to atmospheric state variables:
$$ K_{i,j} = \frac{\partial y_i}{\partial x_j} $$
For a water-vapour channel, $K$ expresses how simulated brightness temperature changes when humidity at vertical level $j$ changes. When total cloud optical depth $\tau$ exceeds 3, the cloud becomes opaque. Infrared photons emitted below the cloud deck cannot escape to the sensor. The mathematical consequence is gradient collapse: $\partial y / \partial q_j \to 0$ for all levels $j$ below the cloud top. The cost function gradient contains zero sensitivity to sub-cloud moisture.

#### 8. The 1D column limitation
Current operational radiative transfer schemes evaluate each satellite pixel as an independent one-dimensional atmospheric column. In nature, convective clouds have three-dimensional geometric structures. Slanted view angles from geostationary orbit introduce parallax shifts. Solar and thermal radiation leaks through cloud side boundaries. The 1D approximation omits lateral photon transport between adjacent pixels.

#### 9. Physical retrieval versus forward observation operator
An empirical retrieval maps observed radiances back to geophysical parameters: $x = f(y)$. This inverse mapping requires external prior constraints from climatology, which creates cross-correlated errors with the numerical model background. A forward observation operator maps the numerical model state into simulated radiances: $y = H(x)$. The assimilation cost function evaluates residuals directly in observation space, which maintains mathematical separation between background and observation error covariances.

---

### Detailed paper evaluations

#### 1. Geer et al. (2018)
- Verified Citation: Geer, A. J., K. Lonitz, P. Weston, M. Kazumori, K. Okamoto, Y. Zhu, N. Bormann, A. Collard, E. Holm, and P. Bauer (2018). All-sky satellite data assimilation at operational weather forecasting centres. Quarterly Journal of the Royal Meteorological Society, 144(713), 1191–1217. DOI: 10.1002/qj.3202
- Document Status: Documented via official publication record and ECMWF Technical Memorandum 819.
- Problem: Operational data assimilation historically rejected all cloud-affected satellite observations. This screening created spatial data gaps in active meteorological regions.
- Method: The authors review operational all-sky microwave temperature and humidity radiance assimilation across ECMWF, the Met Office, JMA, and NCEP. They examine RTTOV-SCATT and CRTM operators, symmetric error modeling, and quality control.
- Findings: Operational all-sky assimilation of microwave radiances provides substantial forecast improvements in global models. The technique reduces 10-day tropical wind errors by 0.5% to 1.5% and improves cyclone positioning.
- Unresolved: The operational framework was established primarily for microwave sounders. Adapting the method to infrared sensors is complicated by strong cloud droplet absorption, narrow weighting functions, and ice habit scattering uncertainties.

#### 2. Geer, Migliorini, and Matricardi (2019)
- Verified Citation: Geer, A. J., S. Migliorini, and M. Matricardi (2019). All-sky assimilation of infrared radiances sensitive to mid- and upper-tropospheric moisture and cloud. Atmospheric Measurement Techniques, 12(9), 4903–4929. DOI: 10.5194/amt-12-4903-2019
- Document Status: Examined via complete 27-page official open-access PDF.
- Problem: Hyperspectral infrared sounders (IASI and CrIS) possess thousands of channels, but operational systems cleared or discarded all cloudy scenes.
- Method: The authors assimilate water-vapour sounding channels under all-sky conditions in the ECMWF IFS using RTTOV-CLD with nine ice habit representations from the Baran database and symmetric error inflation.
- Findings: The study demonstrated positive forecast impact in mid-to-upper tropospheric moisture and temperature fields. All-sky infrared sounding was shown to be stable without adding hydrometeor control variables to the assimilation vector.
- Unresolved: The forward model evaluates radiative transfer on isolated 1D columns. Three-dimensional radiative effects and high-density spatial correlations across convective clouds are neglected.

#### 3. McNally (2009)
- Verified Citation: McNally, A. P. (2009). The direct assimilation of cloud-affected satellite infrared radiances in the ECMWF 4D-Var. Quarterly Journal of the Royal Meteorological Society, 135(641), 821–837. DOI: 10.1002/qj.426
- Document Status: Documented via official publication record and ECMWF Technical Memorandum 547.
- Problem: Completely cloudy infrared pixels lack thermal sensitivity below the cloud top, but partially cloud-affected pixels were routinely discarded by clear-sky systems.
- Method: The author introduces an overcast cloud stream model into ECMWF 4D-Var. The scheme estimates cloud-top pressure and effective cloud fraction directly within the minimization loop for infrared sounding channels.
- Findings: Assimilating cloud-affected infrared radiances improved upper-level wind analyses by up to 2% through the 4D-Var tracer advection mechanism.
- Unresolved: The formulation is restricted to single-layer, overcast or grey cloud assumptions. It cannot model complex multi-layer mixed-phase clouds or deep convective towers.

#### 4. Migliorini and Candy (2019)
- Verified Citation: Migliorini, S., and B. Candy (2019). All-sky satellite data assimilation of microwave temperature sounding channels at the Met Office. Quarterly Journal of the Royal Meteorological Society, 145(720), 867–883. DOI: 10.1002/qj.3470
- Document Status: Documented via official publication record on Wiley.
- Problem: Microwave temperature sounding channels (AMSU-A and ATMS) were assimilated only in clear-sky conditions at the Met Office, which limited observational impact in frontal systems.
- Method: The authors implement a two-step 1D-Var pre-processing scheme coupled to global 4D-Var. The system retrieves moist physical parameters and applies RTTOV-SCATT with symmetric error inflation.
- Findings: All-sky temperature assimilation improved 500 hPa geopotential height forecasts in the Southern Hemisphere and reduced mid-tropospheric temperature biases.
- Unresolved: The intermediate 1D-Var step decouples cloud estimation from the primary 4D-Var cost function. This decoupling restricts the direct transmission of moist physical increments into the main analysis.

#### 5. Saunders et al. (2018)
- Verified Citation: Saunders, R., J. Hocking, E. Turner, P. Rayer, D. Rundle, P. Brunel, J. Vidot, P. Roquet, M. Matricardi, A. Geer, N. Bormann, and C. Lupu (2018). An update on the RTTOV fast radiative transfer model (currently at version 12). Geoscientific Model Development, 11(7), 2717–2737. DOI: 10.5194/gmd-11-2717-2018
- Document Status: Examined via complete official open-access PDF.
- Problem: Operational data assimilation systems require fast forward operators and exact adjoint codes to ingest millions of satellite observations within operational time windows.
- Method: The authors document the release of RTTOV-12. The update incorporates improved gas transmittances, visible and infrared scattering modules (RTTOV-CLD), and full Tangent Linear, Adjoint, and K-matrix formulations.
- Findings: RTTOV-12 simulates top-of-atmosphere radiances with accuracy within 0.1 to 0.5 K of line-by-line models while computing gradients at high numerical efficiency.
- Unresolved: The fast scattering solver relies on 1D plane-parallel approximations and pre-calculated optical tables. It experiences Jacobian zero-collapse beneath opaque clouds.

#### 6. McNally and Watts (2003)
- Verified Citation: McNally, A. P., and P. D. Watts (2003). A cloud detection algorithm for high-spectral-resolution infrared sounders. Quarterly Journal of the Royal Meteorological Society, 129(595), 3411–3423. DOI: 10.1256/qj.02.208
- Document Status: Documented via official publication record and ECMWF Technical Memorandum 375.
- Problem: High-spectral infrared sounders possess channels with peaking heights across the atmosphere. In partially cloudy scenes, upper-peaking channels remain uncontaminated while lower channels are cloud-blocked.
- Method: The authors developed a ranked-channel cloud detection algorithm. Channels are sorted by their clear-sky level of maximum sensitivity, and cloud contamination is identified where observed departures systematically diverge from clear simulations.
- Findings: The algorithm successfully extracts uncontaminated upper-tropospheric radiances above cloud decks, which doubles the number of usable infrared channels in partly cloudy scenes.
- Unresolved: The method screens out and discards all channels peaking inside or below clouds. It does not extract atmospheric information from cloudy layers.

#### 7. Okamoto, Ishibashi, and Okabe (2023)
- Verified Citation: Okamoto, K., T. Ishibashi, and I. Okabe (2023). All-sky infrared radiance assimilation of a geostationary satellite in the Japan Meteorological Agency's global system. Quarterly Journal of the Royal Meteorological Society, 149(755), 2311–2336. DOI: 10.1002/qj.4516
- Document Status: Documented via official open-access publication on Wiley.
- Problem: Operational numerical prediction models at JMA used geostationary AHI radiances only in clear-sky conditions, which omitted rapid moisture changes inside convective systems.
- Method: The authors implement operational all-sky assimilation for Himawari-8 and Himawari-9 AHI water-vapour bands (channels 8, 9, and 10) in the JMA Global Spectral Model. They apply RTTOV-CLD, symmetric cloud-dependent error inflation, and 80 km spatial thinning.
- Findings: Assimilating all-sky AHI radiances improved upper-tropospheric humidity analyses and reduced typhoon track forecast errors by 10 to 15 km at 72-hour lead times.
- Unresolved: Dense spatial observations are thinned aggressively to 80 km to avoid spatial error correlations. This thinning discards fine-scale convective structures.

#### 8. Okamoto (2017)
- Verified Citation: Okamoto, K. (2017). Evaluation of IR radiance simulation for all-sky assimilation of Himawari-8/AHI in a mesoscale NWP system. Quarterly Journal of the Royal Meteorological Society, 143(704), 1667–1678. DOI: 10.1002/qj.3022
- Document Status: Documented via official publication record.
- Problem: Assimilating all-sky infrared radiances into mesoscale models requires quantifying forward simulation errors caused by microphysical assumptions and subgrid cloud variability.
- Method: The author simulates Himawari-8 AHI infrared brightness temperatures using RTTOV-CLD with the JMA non-hydrostatic mesoscale model (MSM) and evaluates departures against observations across diverse weather systems.
- Findings: Cloud simulation errors in mid-level clouds produce systematic radiance departures up to 10 K. Ice crystal habit selection strongly influences brightness temperatures in high cirrus.
- Unresolved: The paper identified substantial position errors in simulated convective cells. The author concluded that standard Gaussian error models are inadequate without aggressive variance inflation.

#### 9. Honda et al. (2018)
- Verified Citation: Honda, T., T. Miyoshi, G.-Y. Lien, S. Nishizawa, R. Yoshida, S. A. Adachi, K. Terasaki, K. Okamoto, H. Tomita, and K. Bessho (2018). Assimilating All-Sky Himawari-8 Satellite Infrared Radiances: A Case of Typhoon Soudelor (2015). Monthly Weather Review, 146(1), 213–229. DOI: 10.1175/MWR-D-16-0357.1
- Document Status: Documented via AMS publication record and RIKEN institutional repository.
- Problem: Tropical cyclone track and intensity forecasts suffer when internal vortex convective structures are poorly initialized.
- Method: The authors assimilate all-sky Himawari-8 AHI infrared radiances every 10 minutes into the SCALE-LETKF ensemble system at 2.8 km horizontal grid resolution for Typhoon Soudelor.
- Findings: Rapid 10-minute all-sky assimilation captured convective developments in the eyewall. The assimilation reduced typhoon center position errors from 50 km to less than 15 km.
- Unresolved: The study required empirical inflation factors up to 100 to prevent filter divergence caused by non-linearities in cloudy infrared forward modeling.

#### 10. Zhu et al. (2016)
- Verified Citation: Zhu, Y., J. C. Derber, A. D. Collard, D. P. Dee, R. E. Treadon, I. M. Navon, and E. Voronovich (2016). All-Sky Microwave Radiance Assimilation in NCEP's GSI Analysis System. Monthly Weather Review, 144(12), 4709–4735. DOI: 10.1175/MWR-D-15-0445.1
- Document Status: Documented via AMS publication record and NOAA institutional repository.
- Problem: Operational data assimilation at NCEP discarded cloudy microwave observations from the Advanced Technology Microwave Sounder (ATMS).
- Method: The authors implement all-sky ATMS assimilation in the NCEP Gridpoint Statistical Interpolation (GSI) system using the Community Radiative Transfer Model (CRTM) and cloud-dependent error inflation.
- Findings: All-sky ATMS assimilation provided neutral to positive forecast impacts globally, with measurable reduction in precipitation forecast errors over North America.
- Unresolved: Microphysical parameters in the CRTM were tuned empirically for microwave scattering. The system cannot be directly transferred to infrared channels where absorption dominates.

#### 11. Minamide and Zhang (2017)
- Verified Citation: Minamide, M., and F. Zhang (2017). Adaptive Observation Error Inflation for Assimilating All-Sky Satellite Radiance. Monthly Weather Review, 145(3), 1063–1081. DOI: 10.1175/MWR-D-16-0257.1
- Document Status: Documented via AMS publication record and Penn State institutional repository.
- Problem: Large non-Gaussian departure distributions in cloudy scenes cause ensemble Kalman filters to produce unphysical analysis increments or reject observations.
- Method: The authors develop an adaptive observation error inflation (AOEI) scheme. The formulation inflates observation error dynamically when the innovation exceeds the expected background ensemble spread.
- Findings: AOEI prevented ensemble filter divergence and suppressed spurious increments in non-convective regions during all-sky geostationary infrared radiance assimilation.
- Unresolved: The inflation scheme modifies observation error variances locally but does not address correlated observation errors across adjacent pixels or across channels.

#### 12. Feng and Pu (2022)
- Verified Citation: Feng, C., and Z. Pu (2022). A Bias Correction Scheme with the Symmetric Cloud Proxy Variable and Its Influence on Assimilating All-Sky GOES-16 Brightness Temperatures. Monthly Weather Review, 150(8), 1885–1904. DOI: 10.1175/MWR-D-21-0333.1
- Document Status: Documented via AMS publication record.
- Problem: Standard variational bias correction schemes assume Gaussian, cloud-independent errors. In all-sky conditions, radiance biases depend strongly on cloud optical depth and height.
- Method: The authors design an all-sky bias correction scheme using the symmetric cloud proxy as a predictor for GOES-16 ABI water-vapour and cloud-sensitive infrared channels.
- Findings: Incorporating the symmetric cloud proxy into the bias correction model eliminated conditional radiance biases in both clear and cloudy regions and stabilized the assimilation cycle.
- Unresolved: The scheme was evaluated in regional case studies of hurricanes. It remains dependent on 1D CRTM simulations that do not account for sub-pixel cloud variability.

#### 13. Xiao et al. (2023)
- Verified Citation: Xiao, H., W. Han, P. Dong, Z. Wang, H. Hu, and R. Yin (2023). Assimilation of data from the MWHS-II onboard the first early morning satellite FY-3E into the CMA global 4D-Var system. Meteorological Applications, 30(2), e2133. DOI: 10.1002/met.2133
- Document Status: Documented via official open-access publication on Wiley.
- Problem: Early-morning orbit observations were missing from the global observing system, which caused temporal data gaps in the assimilation cycle of CMA-GFS.
- Method: The authors assimilate 183 GHz humidity sounding radiances from MWHS-2 onboard the FY-3E satellite into the CMA global 4D-Var system using CRTM and symmetric cloud screening.
- Findings: FY-3E MWHS-2 observations closed an observation gap in the early-morning orbit and improved global humidity and temperature forecast scores by up to 1.2%.
- Unresolved: The operational implementation was restricted to microwave humidity sounders. All-sky infrared observations from accompanying sensors were excluded.

#### 14. Yin et al. (2020)
- Verified Citation: Yin, R., W. Han, Z. Gao, and D. Di (2020). The evaluation of FY-4A's Geostationary Interferometric Infrared Sounder (GIIRS) long-wave temperature sounding channels using the GRAPES global 4D-Var. Quarterly Journal of the Royal Meteorological Society, 146(728), 1459–1476. DOI: 10.1002/qj.3746
- Document Status: Documented via official publication record.
- Problem: High-spectral infrared sounders on geostationary platforms generate massive data volumes with complex orbital thermal noise that must be validated before assimilation.
- Method: The authors evaluate long-wave temperature sounding channels from the FY-4A GIIRS instrument inside the GRAPES global 4D-Var system using RTTOV and clear-sky cloud mask filtering.
- Findings: Selected GIIRS long-wave channels exhibit radiometric stability comparable to polar-orbiting sounders and provide positive temperature increments over East Asia.
- Unresolved: All cloudy channels were screened out and discarded. Convective cloud systems could not be observed or assimilated.

#### 15. Xu, Cheng, Deng, Liu, Wang et al. (2023)
- Verified Citation: Xu, L., W. Cheng, Z. Deng, J. Liu, B. Wang, B. Lu, S. Wang, and L. Dong (2023). Assimilation of the FY-4A AGRI Clear-Sky Radiance Data in a Regional Numerical Model and Its Impact on the Forecast of the '21·7' Henan Extremely Persistent Heavy Rainfall. Advances in Atmospheric Sciences, 40(5), 847–862. DOI: 10.1007/s00376-022-1380-3
- Document Status: Examined via complete 18-page official research paper.
- Problem: Regional numerical weather prediction models require accurate upper-tropospheric humidity fields to forecast localized, extreme persistent torrential rainstorms.
- Method: The authors assimilate clear-sky radiances from FY-4A AGRI water-vapour channels 9 (6.25 $\mu$m) and 10 (7.10 $\mu$m) into a regional WRF model using RTTOV forward modeling and cloud mask screening for the record 2021 Henan rainstorm.
- Findings: Assimilating AGRI clear-sky radiances adjusted initial mid- and upper-level moisture distributions, which improved simulated moisture convergence and localized rainband positioning.
- Unresolved: Convective cloud cores directly responsible for the heaviest rainfall were masked out and excluded from the assimilation cycle. Convective cloud structures remained unconstrained by satellite data.

#### 16. Zhong et al. (2025)
- Verified Citation: Zhong, P., C. Ding, Y. Wang, and J. Li (2025). Rapid-Update Assimilation of All-Sky FY-4A/AGRI Radiances for the Analysis and Prediction of Severe Convective Weather. Advances in Atmospheric Sciences. DOI: 10.1007/s00376-025-4295-y
- Document Status: Examined via complete 21-page official research paper.
- Problem: Mesoscale convective systems develop on rapid timescales that require sub-hourly satellite data updates inside cloudy regions.
- Method: The authors establish a 15-minute rapid-update all-sky assimilation system for FY-4A AGRI infrared channels using RTTOV-CLD with adaptive error inflation in a mesoscale ensemble framework.
- Findings: Rapid all-sky assimilation improved low-level moisture convergence and short-term precipitation forecasting for severe convective storms in Eastern China.
- Unresolved: The system relies on 1D column radiative transfer and enforces heavy spatial thinning to avoid spatial error correlations. This thinning reduces effective horizontal resolution.

#### 17. Li et al. (2021)
- Verified Citation: Li, J., A. J. Geer, K. Okamoto, G. Liu, J. Liu, and W. Han (2021). Satellite All-sky Infrared Radiance Assimilation: Recent Progress and Future Perspectives. Advances in Atmospheric Sciences, 38(7), 1085–1098. DOI: 10.1007/s00376-021-1088-9
- Document Status: Examined via complete 14-page official open-access review.
- Problem: Infrared observations contain rich information on cloud structures and atmospheric humidity, but all-sky infrared assimilation faces severe scientific hurdles compared to microwave sounding.
- Method: The authors provide an international community review of all-sky infrared assimilation principles. The review covers fast radiative transfer, ice optical properties, cloud overlap, and observation error modeling.
- Findings: The review established that symmetric error inflation and consistent ice scattering optical tables (Baran model) enable stable all-sky infrared assimilation.
- Unresolved: The authors highlight three unsolved challenges: subgrid cloud variability, dense horizontal error correlations, and gradient collapse in opaque clouds.

#### 18. Geer and Bauer (2011)
- Verified Citation: Geer, A. J., and P. Bauer (2011). Observation errors in all-sky data assimilation. Quarterly Journal of the Royal Meteorological Society, 137(661), 1994–2012. DOI: 10.1002/qj.830
- Document Status: Documented via official publication record and ECMWF Technical Memorandum 648.
- Problem: In cloudy radiance assimilation, departure distributions exhibit severe non-Gaussian tails when observation errors are assumed constant.
- Method: The authors analyze departure distributions across thousands of microwave observations and formulate the symmetric cloud proxy as an objective predictor for observation error variance.
- Findings: Symmetrical error inflation restored Gaussian departure characteristics, prevented unphysical dry biases, and stabilized variational assimilation across all weather regimes.
- Unresolved: The error model is strictly scalar and diagonal. It does not account for inter-channel or spatial error correlations.

#### 19. Desroziers et al. (2005)
- Verified Citation: Desroziers, G., L. Berre, B. Chapnik, and P. Poli (2005). Diagnosis of observation, background and analysis-error statistics in observation space. Quarterly Journal of the Royal Meteorological Society, 131(613), 3385–3396. DOI: 10.1256/qj.05.108
- Document Status: Documented via official publication record.
- Problem: Specifying observation error covariance matrices $R$ and background error covariance matrices $B$ accurately is essential for optimal data assimilation, but true errors cannot be observed directly.
- Method: The authors derive exact algebraic consistency relationships between background departures, analysis departures, and theoretical error covariances in observation space.
- Findings: The diagnostic allows objective estimation of observation error variances and inter-channel error correlations using routine operational assimilation cycles without external reference datasets.
- Unresolved: The diagnostic assumes that background and observation errors are uncorrelated and that the assimilation system uses linear observation operators.

#### 20. Baran et al. (2014)
- Verified Citation: Baran, A. J., K. Furtado, L. C. Labonnote, and F. Marenco (2014). A self-consistent scattering model for cirrus. II: The high and low frequencies. Quarterly Journal of the Royal Meteorological Society, 140(680), 1039–1052. DOI: 10.1002/qj.2193
- Document Status: Documented via official open-access publication on Wiley.
- Problem: Fast radiative transfer models used empirical, unphysical ice crystal habit mixtures that produced inconsistent scattering properties across infrared and microwave spectra.
- Method: The authors develop an ensemble scattering model based on hexagonal ice crystal aggregates. The formulation parameterizes bulk single-scattering properties directly as continuous functions of ice water content and temperature.
- Findings: The self-consistent database accurately matched observed IASI and airborne radiometer spectra across both solar and thermal wavelengths without arbitrary habit tuning.
- Unresolved: The optical database is pre-tabulated for specific particle size distributions. It does not account for crystal habit evolution in rapidly developing convective updrafts.

#### 21. Ukkonen et al. (2020)
- Verified Citation: Ukkonen, P., R. Pincus, R. J. Hogan, K. P. Nielsen, and E. Kaas (2020). Accelerating Radiation Computations for Dynamical Models With Targeted Machine Learning and Code Optimization. Journal of Advances in Modeling Earth Systems, 12(12), e2020MS002226. DOI: 10.1029/2020MS002226
- Document Status: Documented via official open-access publication on AGU/Wiley.
- Problem: Atmospheric radiation schemes are computationally expensive. Radiation calculations consume up to 30% of total run time in global numerical weather prediction models.
- Method: The authors train deep neural networks to emulate gas optics and broadband radiative flux calculations in the ecRad radiation scheme used in the ECMWF IFS.
- Findings: Neural network emulators accelerated radiative flux computations by a factor of 10 while maintaining heating rate accuracy within 0.1 K per day compared to line-by-line solvers.
- Unresolved: The neural network emulates an existing 1D physical parameterization. It inherits all physical column limitations of the original code and does not calculate observation-space Jacobians for data assimilation.

#### 22. Hilburn, Ebert-Uphoff, and Miller (2021)
- Verified Citation: Hilburn, K. A., I. Ebert-Uphoff, and S. D. Miller (2021). Development and Interpretation of a Neural-Network-Based Synthetic Radar Reflectivity Estimator Using GOES-R Satellite Observations. Journal of Applied Meteorology and Climatology, 60(1), 3–21. DOI: 10.1175/JAMC-D-20-0084.1
- Document Status: Examined via complete 34-page official research paper.
- Problem: Ground radar networks have limited ocean coverage, which deprives forecasters of convective precipitation estimates beyond coastal radar horizons.
- Method: The authors train deep convolutional neural networks to estimate synthetic composite radar reflectivity from GOES-16 ABI multi-channel infrared imagery and lightning flash observations.
- Findings: The deep CNN captured convective cores and rainband structures over open oceans with high spatial fidelity and reasonable skill scores.
- Unresolved: The model is a learned retrieval. It performs an inverse mapping from observations to geophysical estimates, which means it cannot serve as a forward observation operator or supply model-state Jacobians for variational assimilation.

#### 23. Liang, Terasaki, and Miyoshi (2023)
- Verified Citation: Liang, J., K. Terasaki, and T. Miyoshi (2023). A Machine Learning Approach to the Observation Operator for Satellite Radiance Data Assimilation. Journal of the Meteorological Society of Japan. Ser. II, 101(1), 61–76. DOI: 10.2151/jmsj.2023-005
- Document Status: Examined via complete 17-page official open-access PDF.
- Problem: Radiative transfer models require separate, empirical bias correction schemes that introduce tuning artifacts into operational satellite data assimilation.
- Method: The authors train deep neural networks to map atmospheric profiles directly to AMSU-A microwave channel brightness temperatures. They embedded the scheme into an LETKF ensemble data assimilation system.
- Findings: The neural network observation operator matched RTTOV forward simulation accuracy and absorbed satellite radiance biases directly into its trained weights.
- Unresolved: The model was developed strictly as a 1D column model for microwave sounding channels in an ensemble filter. The authors did not develop 2D spatial image operators or analytical adjoint gradients for variational 4D-Var.

---

### Synthesis of the unoccupied research gap

Across the 23 verified scientific works, operational systems and research efforts converge on three fundamental limitations:
1. Operational systems (ECMWF, JMA, NCEP, Met Office, CMA) rely on 1D independent column approximations that ignore 3D radiative effects, slant path parallax, and horizontal photon transport.
2. Operational systems enforce aggressive spatial thinning (60 to 100 km) to avoid non-diagonal observation error correlations. This thinning discards fine-scale convective structures captured by 4 km geostationary imagers.
3. Fast radiative transfer solvers (RTTOV-CLD, CRTM) suffer mathematical Jacobian collapse inside opaque clouds, which prevents the transmission of sub-cloud moisture increments.
4. Published machine learning applications are either 1D column emulators of existing radiative solvers (Ukkonen et al.), learned empirical retrievals (Hilburn et al.), or 1D microwave column operators in ensemble filters (Liang et al.).

No published study has implemented a two-dimensional, differentiable observation operator for geostationary infrared water-vapour channels that maps three-dimensional model fields to 2D radiance images and validates physical Jacobian consistency inside cloudy scenes. That unoccupied gap defines the research proposed for FY-4B AGRI water-vapour channel image assimilation.
