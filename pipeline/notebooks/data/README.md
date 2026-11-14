# Validation data

## `irsa_photometry_ra115.8000_dec-21.6785_qr2.csv`

- **What:** 350 real SPHEREx forced-photometry measurements of one position (RA 115.8000438°, Dec −21.6784668°), all detectors D1–D6, QR2 only. Untouched export.
- **From:** IRSA's SPHEREx photometry service, exported by Tirth. Each row keeps its `obs_publisher_did` (SPHEREx obs_id).
- **Use:** V4, comparing our photometry (D2.4) with IRSA's; developing the spectrum layer (D4.1) before our own photometry exists.
- **Notes:** 168 of 350 fluxes are negative: the source is faint, so many points are noise. Keep them; reject points only by flags and reasons, never by sign.
- **[VERIFY]:** which object this is, and the unit of `flux` / `flux_err` (probably µJy). Ask Tirth or check the IRSA tool's documentation before using the numbers.
