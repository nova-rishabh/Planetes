import numpy as np
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord, Distance
from astropy.time import Time
import astropy.units as u

# SPHEREx 6 detector bands & spectral ranges
DETECTORS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
BAND_RANGES = [
    '0.75–1.11 µm',
    '1.11–1.64 µm',
    '1.64–2.42 µm',
    '2.42–3.82 µm',
    '3.82–4.42 µm',
    '4.42–5.00 µm'
]

# Offline fallback catalog with astrometry presets (avoids CDS timeouts)
PRESET_CATALOG = {
    "barnard": {
        "name": "Barnard's Star",
        "ra": 269.45208,
        "dec": 4.69339,
        "pm_ra": -798.58,
        "pm_dec": 10328.12,
        "parallax": 547.45,
        "rv": -110.5
    },
    "sirius": {
        "name": "Sirius",
        "ra": 101.28715,
        "dec": -16.71611,
        "pm_ra": -546.01,
        "pm_dec": -1223.07,
        "parallax": 379.21,
        "rv": -5.5
    },
    "proxima": {
        "name": "Proxima Centauri",
        "ra": 217.42894,
        "dec": -62.67949,
        "pm_ra": -3775.75,
        "pm_dec": 765.54,
        "parallax": 768.13,
        "rv": -22.2
    },
    "vega": {
        "name": "Vega",
        "ra": 279.23473,
        "dec": 38.78369,
        "pm_ra": 201.03,
        "pm_dec": 286.23,
        "parallax": 130.23,
        "rv": -13.9
    },
    "betelgeuse": {
        "name": "Betelgeuse",
        "ra": 88.79294,
        "dec": 7.40706,
        "pm_ra": 27.54,
        "pm_dec": 11.30,
        "parallax": 6.55,
        "rv": 21.91
    }
}


def resolve_target(
    ra_deg=None,
    dec_deg=None,
    target_name=None,
    pm_ra=0.0,
    pm_dec=0.0,
    parallax_mas=None,
    radial_velocity_kms=0.0,
    epoch_year=2026.86
):
    """
    Resolves sky coordinates from local catalog, online CDS, or raw RA/Dec.
    """
    obs_time = Time(epoch_year, format='decimalyear')

    # If target name is provided without numerical coordinates
    if target_name and (ra_deg is None or dec_deg is None):
        key = target_name.lower().replace("'", "").replace("star", "").strip()
        matched_key = next((k for k in PRESET_CATALOG if k in key), None)

        if matched_key:
            entry = PRESET_CATALOG[matched_key]
            return resolve_target(
                ra_deg=entry["ra"],
                dec_deg=entry["dec"],
                target_name=entry["name"],
                pm_ra=entry["pm_ra"],
                pm_dec=entry["pm_dec"],
                parallax_mas=entry["parallax"],
                radial_velocity_kms=entry["rv"],
                epoch_year=epoch_year
            )

        # Fallback to online CDS query if not in local dictionary
        try:
            coord = SkyCoord.from_name(target_name)
            return coord, target_name
        except Exception:
            raise RuntimeError(
                f"Could not resolve '{target_name}' online or in local catalog. "
                "Please enter numerical RA and Dec directly."
            )

    display_name = target_name if target_name else f"RA {ra_deg:.4f}°, Dec {dec_deg:.4f}°"

    if pm_ra != 0.0 or pm_dec != 0.0:
        dist_obj = Distance(parallax=parallax_mas * u.mas) if parallax_mas is not None else 100 * u.pc
        coord_j2000 = SkyCoord(
            ra=ra_deg * u.deg,
            dec=dec_deg * u.deg,
            distance=dist_obj,
            pm_ra_cosdec=pm_ra * u.mas / u.yr,
            pm_dec=pm_dec * u.mas / u.yr,
            radial_velocity=radial_velocity_kms * u.km / u.s,
            obstime=Time('J2000.0')
        )
        coord = coord_j2000.apply_space_motion(new_obstime=obs_time)
    else:
        coord = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame='icrs')

    return coord, display_name


def generate_spherex_cutouts(coord, rel_fluxes=None):
    """
    Generates 50x50 pixel simulated cutouts across SPHEREx detectors D1-D6.
    """
    if rel_fluxes is None:
        rel_fluxes = {
            'D1': 1.00,
            'D2': 0.88,
            'D3': 0.65,
            'D4': 0.38,
            'D5': 0.20,
            'D6': 0.09
        }

    cutouts = {}
    y, x = np.mgrid[-25:25, -25:25]

    for idx, det in enumerate(DETECTORS):
        np.random.seed(int(abs(coord.ra.deg * 100)) + idx)
        psf = rel_fluxes.get(det, 0.5) * np.exp(-(x**2 + y**2) / (2.0 * (1.8)**2))
        noise = np.random.normal(0, 0.04, (50, 50))
        cutouts[det] = psf + noise

    return cutouts


def process_target(
    ra_deg=None,
    dec_deg=None,
    target_name=None,
    pm_ra=0.0,
    pm_dec=0.0,
    parallax_mas=None,
    radial_velocity_kms=0.0,
    save_filename="output_cutout_6bands.png"
):
    """
    End-to-end execution: resolves position, generates 6-band cutouts,
    and displays side-by-side detector comparison plot.
    """
    coord, display_name = resolve_target(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        target_name=target_name,
        pm_ra=pm_ra,
        pm_dec=pm_dec,
        parallax_mas=parallax_mas,
        radial_velocity_kms=radial_velocity_kms
    )

    print("=" * 65)
    print(f"TARGET               : {display_name}")
    print(f"RIGHT ASCENSION (RA) : {coord.ra.deg:.6f}° ({coord.ra.to_string(unit=u.hour, sep='hms')})")
    print(f"DECLINATION (DEC)    : {coord.dec.deg:.6f}° ({coord.dec.to_string(unit=u.deg, sep='dms')})")
    print("=" * 65)

    cutouts = generate_spherex_cutouts(coord)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(1, 6, figsize=(20, 3.8), sharey=True)

    for i, det in enumerate(DETECTORS):
        ax = axes[i]
        im = ax.imshow(cutouts[det], origin='lower', cmap='inferno')
        ax.axhline(25, color='cyan', linestyle=':', linewidth=0.8, alpha=0.7)
        ax.axvline(25, color='cyan', linestyle=':', linewidth=0.8, alpha=0.7)
        ax.set_title(f"Band {det}\n{BAND_RANGES[i]}", fontsize=11, fontweight='bold', pad=8)
        ax.set_xticks([])
        ax.set_yticks([])

    cbar_ax = fig.add_axes([0.91, 0.18, 0.012, 0.64])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label('Calibrated Flux (Arb. Units)', fontsize=10)

    fig.suptitle(f"{display_name} — SPHEREx 6-Detector Cutouts", fontsize=13, fontweight='bold', y=1.06)

    plt.savefig(save_filename, dpi=300, bbox_inches='tight')
    print(f"[SUCCESS] Saved plot to '{save_filename}'")
    plt.show()

    return {
        "target": display_name,
        "ra_deg": coord.ra.deg,
        "dec_deg": coord.dec.deg,
        "cutouts": cutouts
    }


# =========================================================================
# INTERACTIVE CLI EXECUTION
# =========================================================================
if __name__ == "__main__":
    print("\n--- SPHEREx Pipeline Query ---")
    user_choice = input("Search by (1) Star Name or (2) RA/Dec Coordinates? [Enter 1 or 2]: ").strip()

    if user_choice == "1":
        star_name = input("Enter star name (e.g. Barnard, Sirius, Proxima, Vega): ").strip()
        clean_name = star_name.lower().replace(' ', '_').replace("'", '')
        save_file = f"{clean_name}_spherex_6bands.png"
        result = process_target(target_name=star_name, save_filename=save_file)

    elif user_choice == "2":
        ra_input = float(input("Enter RA in degrees (e.g. 269.45208): ").strip())
        dec_input = float(input("Enter Dec in degrees (e.g. 4.69339): ").strip())
        label = input("Enter a label/name for this target (optional): ").strip() or "Custom Target"
        
        has_pm = input("Apply proper motion? (y/n): ").strip().lower()
        if has_pm == 'y':
            pm_ra_val = float(input("  PM RA (mas/yr): ").strip())
            pm_dec_val = float(input("  PM Dec (mas/yr): ").strip())
            plx_val = float(input("  Parallax (mas): ").strip())
            result = process_target(
                ra_deg=ra_input,
                dec_deg=dec_input,
                target_name=label,
                pm_ra=pm_ra_val,
                pm_dec=pm_dec_val,
                parallax_mas=plx_val,
                save_filename="custom_pm_target_6bands.png"
            )
        else:
            result = process_target(
                ra_deg=ra_input,
                dec_deg=dec_input,
                target_name=label,
                save_filename="custom_target_6bands.png"
            )
    else:
        print("Defaulting to Barnard's Star...")
        result = process_target(target_name="Barnard's Star", save_filename="barnard_spherex_6bands.png")