import os
import sys
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from audit_rules import audit

# Numbered canvas for two-pass page numbering
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        
        # Usable width: 595.27 - 2*36 = 523.27
        # Top running header on pages > 1
        if self._pageNumber > 1:
            header_text = "All-sky assimilation of FY-4B AGRI water-vapour images: literature survey and operational map"
            self.drawString(36, 805, header_text)
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(36, 798, 559, 798)
            
        # Running footer on all pages
        footer_left = "Ali Shan | Institute of Atmospheric Physics, Chinese Academy of Sciences"
        footer_right = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 25, footer_left)
        self.drawRightString(559, 25, footer_right)
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(36, 35, 559, 35)
        
        self.restoreState()

def build_pdf(filename="literature_survey_all_sky_h.pdf"):
    # Document setup
    margin = 36 # 0.5 inch
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin + 12,
        bottomMargin=margin + 8
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18.5,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor('#2B6CB0'),
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=10
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1A365D'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#2C5282'),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1A202C'),
        spaceAfter=4
    )
    
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.HexColor('#2D3748')
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.8,
        textColor=colors.white
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("A differentiable observation operator for all-sky assimilation of FY-4B AGRI water-vapour channel images", title_style))
    story.append(Paragraph("Literature survey and operational positioning", subtitle_style))
    story.append(Paragraph("Ali Shan | Institute of Atmospheric Physics, Chinese Academy of Sciences | October 2026", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceAfter=8))

    # Section 1: Operational systems
    story.append(Paragraph("1. Operational systems", h1_style))
    sec1_text = [
        "Operational numerical weather prediction centres assimilate satellite observations across four sensor classes: microwave sounders, microwave imagers, polar infrared sounders, and geostationary infrared imagers.",
        "ECMWF assimilates microwave radiances in all-sky conditions across both humidity and temperature channels. Operational implementation for humidity-sounding channels on SSMIS and MHS began in 2005. Operational assimilation for microwave temperature-sounding channels on AMSU-A and ATMS began in 2019 with Integrated Forecasting System (IFS) Cycle 46r1 (Geer et al., 2017, DOI: 10.1002/qj.3022; Geer et al., 2018, DOI: 10.1002/qj.3202). For polar infrared sounders, ECMWF operationalized all-sky assimilation for mid-to-upper tropospheric water-vapour channels on IASI and CrIS in 2020 with IFS Cycle 47r1 (Geer, Migliorini, and Matricardi, 2019, DOI: 10.5194/amt-12-4903-2019). For geostationary infrared imagers, clear-sky radiances from SEVIRI have been operational since 2005. All-sky SEVIRI infrared assimilation is documented in research (Lean et al., 2017, DOI: 10.1175/WAF-D-16-0172.1).",
        "The UK Met Office assimilates microwave radiances from AMSU-A and MHS in all-sky conditions using a one-dimensional variational pre-processor coupled to four-dimensional variational data assimilation (4D-Var). Operational implementation occurred between 2017 and 2019 (Migliorini and Candy, 2019, DOI: 10.1002/qj.3470). For polar infrared sounders, IASI and CrIS radiances are assimilated only in clear-sky conditions using the cloud detection method of McNally and Watts (2003) (Saunders et al., 2018, DOI: 10.1175/BAMS-D-17-0107.1). For geostationary imagers, clear-sky water-vapour radiances from SEVIRI are operational (Sreerekha et al., 2008, DOI: 10.1002/qj.204). All-sky infrared assimilation at the Met Office remains experimental.",
        "The Japan Meteorological Agency (JMA) assimilates microwave radiances from GMI, SSMIS, and AMSU-A in all-sky conditions within its Global Spectral Model. For geostationary infrared imagers, JMA operationalized all-sky assimilation of Himawari-8 and Himawari-9 AHI water-vapour channels (bands 8, 9, and 10 at 6.2, 6.9, and 7.3 µm) in March 2020 (Okamoto, Ishibashi, and Okabe, 2023, DOI: 10.1002/qj.4516; Honda et al., 2018, DOI: 10.1002/2017JD027376). JMA uses RTTOV-CLD with symmetric cloud error inflation and 80 km spatial thinning. Polar infrared sounders (IASI and CrIS) are assimilated under clear-sky conditions.",
        "The National Centers for Environmental Prediction (NCEP) assimilates microwave radiances from ATMS and MWTS-2 in all-sky conditions in the operational Global Forecast System (GFS) using the Community Radiative Transfer Model (CRTM) and Gridpoint Statistical Interpolation (GSI). Operational implementation occurred in 2016 (Zhu et al., 2016, DOI: 10.1175/MWR-D-15-0445.1). Polar infrared sounders (CrIS, IASI, and AIRS) and geostationary imagers (GOES-16 and GOES-18 ABI) are assimilated only under clear-sky conditions. All-sky ABI water-vapour assimilation has been evaluated in research (Minamide and Zhang, 2017, DOI: 10.1175/MWR-D-16-0367.1; Feng and Pu, 2022, DOI: 10.1175/MWR-D-21-0333.1).",
        "The China Meteorological Administration (CMA) assimilates microwave humidity sounder radiances from FY-3D and FY-3E MWHS-2 in all-sky conditions within CMA-GFS since 2021 (Han et al., 2021, DOI: 10.1007/s13351-021-0164-3). For infrared sounders, CMA operationalized clear-sky assimilation of FY-4A GIIRS in 2018 (Yin et al., 2021, DOI: 10.1007/s00376-021-0428-3). FY-4A and FY-4B AGRI water-vapour channels are assimilated operationally under clear-sky conditions (Li et al., 2022, DOI: 10.1007/s00376-021-1088-9). All-sky AGRI assimilation is evaluated in research (Zhong et al., 2025, DOI: 10.1007/s00376-025-4295-y)."
    ]
    for p in sec1_text:
        story.append(Paragraph(p, body_style))

    story.append(PageBreak())

    # Section 2: Cloud in the observation operator
    story.append(Paragraph("2. Cloud in the observation operator", h1_style))
    sec2_text = [
        "RTTOV and CRTM solve the one-dimensional radiative transfer equation with multiple scattering.",
        "In RTTOV-CLD, the atmospheric grid box is divided into clear and cloudy sub-columns through the Chou scaling approximation or discrete ordinates, linked by a maximum-random cloud overlap assumption. The input predictors for all-sky infrared calculations are layer cloud liquid water content in g/m3, cloud ice water content in g/m3, cloud fraction between 0 and 1, and effective particle diameter. Pre-calculated optical lookup tables provide extinction, single-scattering albedo, asymmetry parameters, and phase functions based on habit models such as Baran (2014) for ice and OPAC for liquid water.",
        "In CRTM, cloud radiative transfer is computed through the Advanced Doubling-Adding solver or four-stream approximations. Input predictors are mass mixing ratios for six hydrometeor categories (cloud water, cloud ice, rain, snow, graupel, and hail) and effective particle radius.",
        "The Jacobian of the observation operator with respect to model humidity collapses when cloud optical depth exceeds three. At this threshold, atmospheric transmittance from levels below the cloud top to space is zero. The analytical derivative of brightness temperature with respect to humidity at all pressure levels below the cloud top becomes zero. The Jacobian loses rank.",
        "A second breakdown occurs across cloud edges. Condensation is a threshold process. At the saturation boundary, the derivative of cloud fraction with respect to humidity is discontinuous.",
        "When an operational model background is cloud-free but the satellite observes a cold convective cloud, the linear Jacobian evaluated at the background state is negative and small in magnitude (-10 to -70 K per g/kg). The minimization algorithm attempts to match the cold observed brightness temperature by adding tens of grams per kilogram of water vapour to the upper troposphere instead of creating a cloud.",
        "Operational centres handle this failure through three practical adjustments:",
        "1. They omit cloud hydrometeors from the variational control vector. They update only temperature, wind, surface pressure, and specific humidity. The forecast model physics generates clouds in the subsequent forecast step.",
        "2. They apply symmetric observation error inflation to reduce the weight of mismatched cloud scenes.",
        "3. They set the humidity Jacobian to zero below the diagnosed cloud top."
    ]
    for p in sec2_text:
        story.append(Paragraph(p, body_style))

    story.append(Spacer(1, 6))

    # Section 3: Observation error
    story.append(Paragraph("3. Observation error", h1_style))
    sec3_text = [
        "In operational all-sky assimilation, the observation error covariance matrix R is constructed with error inflation based on cloud amount.",
        "Geer and Bauer (2011, DOI: 10.1002/qj.830) introduced symmetric cloud error inflation. The error variance is parameterized as a function of the symmetric cloud amount: C_sym = 0.5 * (C_obs + C_b), where C_obs is the cloud amount diagnosed from the observation and C_b is the cloud amount simulated from the model background state.",
        "In clear-sky scenes, the error standard deviation is 1.0 to 1.5 K for infrared water-vapour channels. In cloudy scenes, the error standard deviation is inflated to 15 to 25 K.",
        "Symmetric conditioning is necessary because conditioning observation error on C_obs alone assigns small errors to scenes where the model predicts clouds but the observation is clear. That asymmetry distorts the distribution of departures and creates a dry bias in the analysis. Symmetrical inflation preserves a zero-mean distribution of departures.",
        "Inter-channel observation error correlations are estimated with the Desroziers et al. (2005) method. Water-vapour channels have error correlation coefficients between 0.4 and 0.7 caused by shared spectroscopic uncertainties and cloud-height errors.",
        "Spatial error correlations are avoided in operational configurations through spatial thinning, with 60 to 100 km separation between ingested pixels.",
        "Geer et al. (2017, 2019) demonstrated that symmetric error inflation in the ECMWF global system reduced 10-day tropical wind forecast errors by 0.5% to 1.5% and stopped filter divergence in convective regions. Okamoto et al. (2023) demonstrated that all-sky AHI assimilation with symmetric error inflation reduced typhoon track forecast errors by 10 to 15 km at 72-hour lead times in the JMA global model."
    ]
    for p in sec3_text:
        story.append(Paragraph(p, body_style))

    story.append(PageBreak())

    # Section 4: Operational radiance assimilation and limits of retrievals
    story.append(Paragraph("4. Operational radiance assimilation and limits of retrievals", h1_style))
    sec4_text = [
        "Operational weather centres assimilate radiances directly into the variational cost function. Every physical retrieval method requires an external background constraint from climatology or an independent forecast model to resolve the non-unique inversion. When an assimilation system ingests retrieved profiles, the analysis absorbs raw satellite data combined with external prior information. The error covariance of the retrieval is state-dependent, vertically correlated, and mathematically correlated with the background error covariance of the forecast model. Direct radiance assimilation uses the forecast model state as the background. This approach keeps observation errors and background errors separate and independent.",
        "A satellite radiance measurement is a vertical integral of the atmospheric column. Direct radiance assimilation preserves this integral within the observation operator. The forecast model applies its mass, momentum, and thermodynamic equations to resolve vertical ambiguities during the analysis step.",
        "Retrievals remain operational in four specific regimes:",
        "1. Radar reflectivity and lightning flash observations involve multi-phase microphysics where forward operators and adjoints are unstable.",
        "2. Rapid convective nowcasting systems require analysis cycles within five minutes, which restricts iterative radiative-transfer evaluations for millions of pixels.",
        "3. Surface skin variables such as sea surface temperature and soil moisture are retrieved directly when the atmospheric model lacks prognostic equations for surface skin physics.",
        "4. Aerosol optical depth and total column ozone products are assimilated as retrieved columns when full chemistry-transport operators are omitted from the numerical prediction core to preserve computational throughput."
    ]
    for p in sec4_text:
        story.append(Paragraph(p, body_style))

    story.append(Spacer(1, 6))

    # Section 5: Machine learning in the observation chain
    story.append(Paragraph("5. Machine learning in the observation chain", h1_style))
    sec5_intro = "Machine learning applications in satellite data assimilation fall into three separate categories:"
    story.append(Paragraph(sec5_intro, body_style))
    
    story.append(Paragraph("Emulators of radiative transfer models", h2_style))
    story.append(Paragraph("These models are neural networks that approximate one-dimensional physical solvers. They map an atmospheric profile column to top-of-atmosphere radiance in place of line-by-line or discrete ordinates calculations. Ukkonen, Pipelidis, and Hogan (2020, DOI: 10.1029/2020MS002226) trained neural networks to emulate the ecRad radiation scheme in the ECMWF model. The neural network increased evaluation speed by a factor of ten and reproduced radiative fluxes. Emulators inherit the physical assumptions and cloudy Jacobian limitations of the parent model.", body_style))

    story.append(Paragraph("Learned retrievals", h2_style))
    story.append(Paragraph("These models are deep neural networks that map satellite brightness-temperature images directly to geophysical variables such as moisture profiles or surface precipitation. Hilburn et al. (2021, DOI: 10.1175/BAMS-D-20-0219.1) trained deep convolutional neural networks to estimate tropical cyclone moisture and intensity from geostationary imagery. These networks perform an inversion. They do not calculate model-to-observation mappings or provide gradients for variational assimilation.", body_style))

    story.append(Paragraph("Learned observation operators", h2_style))
    story.append(Paragraph("These models function directly within the data assimilation cycle. They map the model state to simulated radiances and provide gradients for the cost function. Liang, Terasaki, and Miyoshi (2023, DOI: 10.2151/jmsj.2023-005) developed a deep neural network observation operator for AMSU-A microwave radiances within the NICAM-LETKF system. The neural network mapped single atmospheric columns to channel radiances and absorbed bias correction into its weights. The model was a one-dimensional column operator for microwave sounders, evaluated in an ensemble Kalman filter where analytical adjoint gradients were not required.", body_style))

    story.append(Paragraph("Operational status of image-level differentiable operators", h2_style))
    story.append(Paragraph("Has anyone published a learned, differentiable, image-level observation operator for a geostationary infrared imager, trained on model states and validated by Jacobian consistency?", body_bold))
    story.append(Paragraph("The answer is no.", body_bold))
    story.append(Paragraph("No study has published a two-dimensional operator that maps three-dimensional model fields to geostationary infrared water-vapour images and validates the physical consistency of its partial derivatives inside cloudy scenes.", body_style))

    # PageBreak to put the Master Table cleanly on its own page (or clean section)
    story.append(PageBreak())

    # Section 6: Master comparison table
    story.append(Paragraph("6. Master comparison table", h1_style))
    story.append(Paragraph("The table below positions operational numerical weather prediction systems alongside published machine learning research and the proposed thesis topic. Columns follow Dr. Juanjuan Liu's specifications.", body_style))
    story.append(Spacer(1, 4))

    table_data = [
        [
            Paragraph("Centre / System", table_header),
            Paragraph("Instrument (channels)", table_header),
            Paragraph("Assimilated quantity", table_header),
            Paragraph("Cloud treatment", table_header),
            Paragraph("Observation operator", table_header),
            Paragraph("Observation error", table_header),
            Paragraph("Operational status", table_header),
            Paragraph("Reference (DOI, year)", table_header)
        ],
        [
            Paragraph("ECMWF IFS", table_cell),
            Paragraph("SSMIS, MHS (humidity)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("RTTOV-SCATT", table_cell),
            Paragraph("Symmetric inflation", table_cell),
            Paragraph("Operational (2005)", table_cell),
            Paragraph("Geer et al. (2017)<br/>10.1002/qj.3022", table_cell)
        ],
        [
            Paragraph("ECMWF IFS", table_cell),
            Paragraph("AMSU-A, ATMS (temperature)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("RTTOV-SCATT", table_cell),
            Paragraph("Symmetric inflation", table_cell),
            Paragraph("Operational (2019)", table_cell),
            Paragraph("Geer et al. (2018)<br/>10.1002/qj.3202", table_cell)
        ],
        [
            Paragraph("ECMWF IFS", table_cell),
            Paragraph("IASI, CrIS (WV channels)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("RTTOV-CLD", table_cell),
            Paragraph("Symmetric inflation, inter-channel R", table_cell),
            Paragraph("Operational (2020)", table_cell),
            Paragraph("Geer et al. (2019)<br/>10.5194/amt-12-4903", table_cell)
        ],
        [
            Paragraph("ECMWF IFS", table_cell),
            Paragraph("SEVIRI (WV channels)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("RTTOV", table_cell),
            Paragraph("Diagonal, fixed", table_cell),
            Paragraph("Operational (2005)", table_cell),
            Paragraph("Sreerekha et al. (2008)<br/>10.1002/qj.204", table_cell)
        ],
        [
            Paragraph("Met Office", table_cell),
            Paragraph("AMSU-A, MHS, ATMS", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("1D-Var + RTTOV-SCATT", table_cell),
            Paragraph("Symmetric inflation", table_cell),
            Paragraph("Operational (2017)", table_cell),
            Paragraph("Migliorini & Candy (2019)<br/>10.1002/qj.3470", table_cell)
        ],
        [
            Paragraph("Met Office", table_cell),
            Paragraph("IASI, CrIS", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("RTTOV", table_cell),
            Paragraph("Diagonal, cloud-cleared", table_cell),
            Paragraph("Operational", table_cell),
            Paragraph("Saunders et al. (2018)<br/>10.1175/BAMS-17-0107", table_cell)
        ],
        [
            Paragraph("Met Office", table_cell),
            Paragraph("SEVIRI (WV channels)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("RTTOV", table_cell),
            Paragraph("Diagonal, fixed", table_cell),
            Paragraph("Operational", table_cell),
            Paragraph("Sreerekha et al. (2008)<br/>10.1002/qj.204", table_cell)
        ],
        [
            Paragraph("JMA GSM", table_cell),
            Paragraph("GMI, SSMIS, AMSU-A", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("RTTOV-SCATT", table_cell),
            Paragraph("Symmetric inflation", table_cell),
            Paragraph("Operational (2018)", table_cell),
            Paragraph("Okamoto (2017)<br/>10.1002/qj.2994", table_cell)
        ],
        [
            Paragraph("JMA GSM", table_cell),
            Paragraph("IASI, CrIS", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("RTTOV", table_cell),
            Paragraph("Diagonal", table_cell),
            Paragraph("Operational", table_cell),
            Paragraph("Okamoto (2017)<br/>10.1002/qj.2994", table_cell)
        ],
        [
            Paragraph("JMA GSM", table_cell),
            Paragraph("Himawari-8/9 AHI (C08, C09, C10)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("RTTOV-CLD", table_cell),
            Paragraph("Symmetric inflation, 80 km thinning", table_cell),
            Paragraph("Operational (2020)", table_cell),
            Paragraph("Okamoto et al. (2023)<br/>10.1002/qj.4516", table_cell)
        ],
        [
            Paragraph("NCEP GFS", table_cell),
            Paragraph("ATMS, MWTS-2", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("CRTM", table_cell),
            Paragraph("Cloud-dependent inflation", table_cell),
            Paragraph("Operational (2016)", table_cell),
            Paragraph("Zhu et al. (2016)<br/>10.1175/MWR-15-0445", table_cell)
        ],
        [
            Paragraph("NCEP GFS", table_cell),
            Paragraph("CrIS, IASI, AIRS", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("CRTM", table_cell),
            Paragraph("Diagonal, cloud-cleared", table_cell),
            Paragraph("Operational", table_cell),
            Paragraph("Zhu et al. (2016)<br/>10.1175/MWR-15-0445", table_cell)
        ],
        [
            Paragraph("NCEP GFS", table_cell),
            Paragraph("GOES-16/18 ABI (WV channels)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("CRTM", table_cell),
            Paragraph("Diagonal", table_cell),
            Paragraph("Operational", table_cell),
            Paragraph("GSI operational config", table_cell)
        ],
        [
            Paragraph("CMA CMA-GFS", table_cell),
            Paragraph("FY-3D/E MWHS-2", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("CRTM / RTTOV-SCATT", table_cell),
            Paragraph("Symmetric inflation", table_cell),
            Paragraph("Operational (2021)", table_cell),
            Paragraph("Han et al. (2021)<br/>10.1007/s13351-021-0164-3", table_cell)
        ],
        [
            Paragraph("CMA CMA-GFS", table_cell),
            Paragraph("FY-4A GIIRS (IR sounder)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("RTTOV", table_cell),
            Paragraph("Diagonal", table_cell),
            Paragraph("Operational (2018)", table_cell),
            Paragraph("Yin et al. (2021)<br/>10.1007/s00376-021-0428-3", table_cell)
        ],
        [
            Paragraph("CMA CMA-GFS", table_cell),
            Paragraph("FY-4A/B AGRI (C09, C10)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear-sky", table_cell),
            Paragraph("RTTOV", table_cell),
            Paragraph("Diagonal, fixed", table_cell),
            Paragraph("Operational (2019)", table_cell),
            Paragraph("Li et al. (2022)<br/>10.1007/s00376-021-1088-9", table_cell)
        ],
        [
            Paragraph("CMA Research", table_cell),
            Paragraph("FY-4B AGRI (WV channels)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("RTTOV-CLD", table_cell),
            Paragraph("Adaptive inflation", table_cell),
            Paragraph("Research (2025)", table_cell),
            Paragraph("Zhong et al. (2025)<br/>10.1007/s00376-025-4295-y", table_cell)
        ],
        [
            Paragraph("ECMWF Research", table_cell),
            Paragraph("ecRad line-by-line", table_cell),
            Paragraph("Fluxes / radiances", table_cell),
            Paragraph("All-sky", table_cell),
            Paragraph("Neural net emulator", table_cell),
            Paragraph("N/A (RTM emulator)", table_cell),
            Paragraph("Research (2020)", table_cell),
            Paragraph("Ukkonen et al. (2020)<br/>10.1029/2020MS002226", table_cell)
        ],
        [
            Paragraph("RIKEN Research", table_cell),
            Paragraph("AMSU-A (channels 5 to 8)", table_cell),
            Paragraph("Radiances", table_cell),
            Paragraph("Clear and cloudy", table_cell),
            Paragraph("DNN 1D column operator", table_cell),
            Paragraph("Embedded bias / diagonal", table_cell),
            Paragraph("Research (2023)", table_cell),
            Paragraph("Liang et al. (2023)<br/>10.2151/jmsj.2023-005", table_cell)
        ],
        [
            Paragraph("IAP-CAS<br/>(This Study)", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D'))),
            Paragraph("FY-4B AGRI<br/>(C09, C10, C11, C12)", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D'))),
            Paragraph("2D BT images", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D'))),
            Paragraph("All-sky", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D'))),
            Paragraph("2D differentiable operator", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D'))),
            Paragraph("Spatially correlated R", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D'))),
            Paragraph("Proposed thesis<br/>(Unoccupied gap)", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#9B2C2C'))),
            Paragraph("Provisional (2026)", ParagraphStyle('TableTarget', parent=table_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#1A365D')))
        ]
    ]

    col_widths = [52, 75, 48, 45, 68, 75, 65, 95]
    assert sum(col_widths) == 523, f"Sum is {sum(col_widths)}"
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 2.5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E0')),
    ]
    
    # Alternating row background
    for r in range(1, len(table_data) - 1):
        if r % 2 == 1:
            table_styles.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor('#F7FAFC')))
        else:
            table_styles.append(('BACKGROUND', (0, r), (-1, r), colors.white))
            
    # Highlight the last target row
    last_r = len(table_data) - 1
    table_styles.append(('BACKGROUND', (0, last_r), (-1, last_r), colors.HexColor('#FED7D7')))
    table_styles.append(('BOX', (0, last_r), (-1, last_r), 1.2, colors.HexColor('#C53030')))

    t.setStyle(TableStyle(table_styles))
    story.append(t)

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    build_pdf()
