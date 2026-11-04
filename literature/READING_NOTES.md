# Literature reading log and evaluation notes

This log organizes primary papers from the all-sky satellite data assimilation survey according to Dr. Juanjuan Liu's four-part reading framework:
1. What problem does the paper address?
2. What method does it use?
3. What does it find?
4. What does it leave unsolved?

### 1. Geer et al. (2018): operational all-sky assimilation review
- Citation: Geer, A. J., Lonitz, K., Weston, P., Kazumori, M., Okamoto, K., Zhu, Y., Bormann, N., Collard, A., Holm, E., and Bauer, P. (2018). All-sky satellite data assimilation at operational weather forecasting centres. Quarterly Journal of the Royal Meteorological Society, 144(713), 1191–1217. DOI: 10.1002/qj.3202
- Problem: Traditional satellite data assimilation discarded cloudy observations. This practice created severe sampling bias and deprived forecast models of observations in active weather systems.
- Method: The authors review physical principles, observation operators (RTTOV-SCATT and CRTM), symmetric error models, and variational quality control across ECMWF, the Met Office, JMA, and NCEP.
- Findings: Operational assimilation of all-sky microwave humidity and temperature radiances delivers substantial medium-range forecast improvements. It reduces 10-day tropical wind errors by 0.5% to 1.5% and anchors moisture and wind analyses in storm regions.
- Unsolved: Extension to infrared sensors is hindered by strong cloud absorption, severe Jacobian non-linearities, and microphysical uncertainties at thermal wavelengths.

### 2. Okamoto, Ishibashi, and Okabe (2023): JMA all-sky AHI operational assimilation
- Citation: Okamoto, K., Ishibashi, T., and Okabe, I. (2023). All-sky infrared radiance assimilation of a geostationary satellite in the Japan Meteorological Agency's global system. Quarterly Journal of the Royal Meteorological Society, 149(755), 2311–2336. DOI: 10.1002/qj.4516
- Problem: Geostationary infrared imagers offer high spatial and temporal coverage, but operational weather centres had restricted their use to clear-sky conditions due to cloud modeling errors.
- Method: The authors implement operational all-sky assimilation for Himawari-8 and Himawari-9 AHI water-vapour bands (8, 9, 10) in the JMA Global Spectral Model. They use RTTOV-CLD, symmetric cloud-dependent error inflation, and 80 km spatial thinning.
- Findings: All-sky AHI assimilation improved moisture and wind analyses in the mid-to-upper troposphere. It reduced typhoon track forecast errors by 10 to 15 km at 72-hour lead times.
- Unsolved: Sub-column cloud fraction assumptions cause threshold gradient collapse in 1D RTTOV. Dense spatial correlations across convective systems cannot be assimilated directly, which forces 80 km thinning.

### 3. Xu, Cheng, Deng, Liu, Wang et al. (2023): FY-4A AGRI clear-sky radiance assimilation
- Citation: Xu, L., Cheng, W., Deng, Z., Liu, J., Wang, B., Lu, B., Wang, S., and Dong, L. (2023). Assimilation of the FY-4A AGRI Clear-Sky Radiance Data in a Regional Numerical Model and Its Impact on the Forecast of the '21·7' Henan Extremely Persistent Heavy Rainfall. Advances in Atmospheric Sciences, 40(5), 847–862. DOI: 10.1007/s00376-022-1380-3
- Problem: Regional convective forecast models over China require rapid updates of upper-tropospheric moisture fields to forecast persistent extreme precipitation events.
- Method: The authors assimilate FY-4A AGRI clear-sky radiances (channels 9 and 10) within a regional WRF numerical system using RTTOV forward modeling and cloud-mask screening.
- Findings: Assimilation of AGRI water-vapour radiances strengthened upper-tropospheric moisture analysis accuracy. It improved the simulated rainfall intensity and spatial location for the record Henan rainstorm.
- Unsolved: Heavy cloud bands directly covering the severe convective cores were masked out and excluded from the assimilation cycle. Convective cloud structures remained unconstrained by observations.

### 4. Geer, Migliorini, and Matricardi (2019): ECMWF all-sky polar infrared assimilation
- Citation: Geer, A. J., Migliorini, S., and Matricardi, M. (2019). All-sky assimilation of infrared radiances sensitive to mid- and upper-tropospheric moisture and cloud. Atmospheric Measurement Techniques, 12(9), 4903–4929. DOI: 10.5194/amt-12-4903-2019
- Problem: Hyperspectral infrared sounders (IASI and CrIS) provide thousands of channels, but operational systems cleared or discarded all cloud-affected scenes.
- Method: The authors assimilate water-vapour sounding channels under all-sky conditions using RTTOV-CLD with nine ice habit representations (Baran tables) and symmetric error inflation based on cloud amount.
- Findings: The study demonstrated positive impact on forecast performance in mid-to-upper tropospheric moisture and temperature fields. It confirmed the feasibility of all-sky infrared sounding without full microphysical control vectors.
- Unsolved: Radiative transfer remains strictly one-dimensional per field-of-view. Three-dimensional cloud radiation effects and high-resolution spatial correlations in cloud fields are omitted.

### 5. Liang, Terasaki, and Miyoshi (2023): machine learning observation operator
- Citation: Liang, J., Terasaki, K., and Miyoshi, T. (2023). A Machine Learning Approach to the Observation Operator for Satellite Radiance Data Assimilation. Journal of the Meteorological Society of Japan. Ser. II, 101(1), 61–76. DOI: 10.2151/jmsj.2023-005
- Problem: Radiative transfer solvers are computationally demanding and require empirical bias correction schemes that interact unpredictably with physical forward operators.
- Method: Deep neural networks were trained to map atmospheric profiles directly to AMSU-A microwave channel brightness temperatures. The scheme was tested within a Local Ensemble Transform Kalman Filter (LETKF).
- Findings: The neural network matched physical RTTOV simulations in forward accuracy. It absorbed systematic observation-minus-background biases directly into network weights.
- Unsolved: The model was evaluated only as a 1D column model for microwave sounders in an ensemble filter. Analytical adjoint gradients and 2D spatial cloud image representations were not developed.
