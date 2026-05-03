"""Native NGA-West2 GMPE equations generated from audit-only VBA."""
from __future__ import annotations

import math

from ngaw2gmpe.coefficients import load_coefficients


def _excel_col_number(label: str) -> int:
    out = 0
    for ch in label:
        out = out * 26 + ord(ch) - 64
    return out


def _cof(model: str, period: float) -> list[float]:
    lookup_period = 0.001 if model == "CB14" and float(period) == 0 else float(period)
    data = load_coefficients(model)
    rows = data[abs(data["period_s"].astype(float) - lookup_period) < 1e-9].copy()
    if rows.empty:
        raise ValueError(f"No coefficients for {model} period {period}")
    rows["source_col"] = rows["source_cell"].str.extract(r"([A-Z]+)")[0].map(_excel_col_number)
    values = []
    for _, row in rows.sort_values("source_col").iterrows():
        value = row["value"]
        if str(value) == "nan":
            value = row["cached_value"]
        values.append(float(value))
    return values


def pgar_calc(m, rjb, u, rs, ns, region, t):
    c1, c2, c3, counter, dc3, dc3chtur, dc3jpit, e0 = 0, 0, 0, 0, 0, 0, 0, 0
    e1, e2, e3, e4, e5, e6, fm, fp = 0, 0, 0, 0, 0, 0, 0, 0
    h, mh, mref, pgar, r, rref, ss = 0, 0, 0, 0, 0, 0, 0
    cof = _cof('BSSA14', t)
    e0 = cof[0]
    e1 = cof[1]
    e2 = cof[2]
    e3 = cof[3]
    e4 = cof[4]
    e5 = cof[5]
    e6 = cof[6]
    mh = cof[7]
    c1 = cof[8]
    c2 = cof[9]
    c3 = cof[10]
    mref = cof[11]
    rref = cof[12]
    h = cof[13]
    dc3 = cof[14]
    dc3chtur = cof[15]
    dc3jpit = cof[16]
    if ns == 0 and rs == 0 and u == 0:
        ss = 1
    else:
        ss = 0
    if m <= mh:
        fm = e0 * u + e1 * ss + e2 * ns + e3 * rs + e4 * (m - mh) + e5 * (m - mh) ** 2
    else:
        fm = e0 * u + e1 * ss + e2 * ns + e3 * rs + e6 * (m - mh)
    r = math.sqrt(rjb ** 2 + h ** 2)
    if region == 0:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3) * (r - rref)
    elif region == 3 or region == 5:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3chtur) * (r - rref)
    elif region == 1 or region == 4:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3jpit) * (r - rref)
    else:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3) * (r - rref)
    pgar = math.exp(fm + fp)
    return pgar

def dz1_calc(vs30, z1, region, t):
    dz1, mz1 = 0, 0
    if region == 1:
        mz1 = math.exp(-5.23 / 2 * math.log((vs30 ** 2 + 412.39 ** 2) / (1360 ** 2 + 412.39 ** 2))) / 1000
    else:
        mz1 = math.exp(-7.15 / 4 * math.log((vs30 ** 4 + 570.94 ** 4) / (1360 ** 4 + 570.94 ** 4))) / 1000
    dz1 = z1 - mz1
    return dz1

def i_14_raw(m, rrup, f, vs30, t):
    a11, a12, a21, a22, a3, b11, b12, b21 = 0, 0, 0, 0, 0, 0, 0, 0
    b22, counter, fatn, fdis, fflt, fm, fsite, g = 0, 0, 0, 0, 0, 0, 0, 0
    ksi, phi, y = 0, 0, 0
    cof = _cof('I14', t)
    a11 = cof[0]
    a21 = cof[1]
    b11 = cof[2]
    b21 = cof[3]
    a12 = cof[4]
    a22 = cof[5]
    b12 = cof[6]
    b22 = cof[7]
    a3 = cof[8]
    ksi = cof[9]
    g = cof[10]
    phi = cof[11]
    if m <= 6.75:
        fm = a21 * m + a3 * (8.5 - m) ** 2
    else:
        fm = a22 * m + a3 * (8.5 - m) ** 2
    if m <= 6.75:
        fdis = -(b11 + b21 * m) * math.log(rrup + 10)
    else:
        fdis = -(b12 + b22 * m) * math.log(rrup + 10)
    if vs30 < 1200:
        fsite = ksi * math.log(vs30)
    else:
        fsite = ksi * math.log(1200)
    fatn = g * rrup
    fflt = phi * f
    if m <= 6.75:
        y = math.exp(a11 + fm + fdis + fsite + fatn + fflt)
    else:
        y = math.exp(a12 + fm + fdis + fsite + fatn + fflt)
    return y

def i_14_stdev_raw(m, t):
    a11, a12, a21, a22, a3, b11, b12, b21 = 0, 0, 0, 0, 0, 0, 0, 0
    b22, counter, g, ksi, phi, sigma = 0, 0, 0, 0, 0, 0
    cof = _cof('I14', t)
    a11 = cof[0]
    a21 = cof[1]
    b11 = cof[2]
    b21 = cof[3]
    a12 = cof[4]
    a22 = cof[5]
    b12 = cof[6]
    b22 = cof[7]
    a3 = cof[8]
    ksi = cof[9]
    g = cof[10]
    phi = cof[11]
    if t <= 0.05:
        if m <= 5:
            sigma = 1.18 + 0.035 * math.log(0.05) - 0.06 * 5
        elif m >= 7.5:
            sigma = 1.18 + 0.035 * math.log(0.05) - 0.06 * 7.5
        else:
            sigma = 1.18 + 0.035 * math.log(0.05) - 0.06 * m
    elif t >= 3:
        if m <= 5:
            sigma = 1.18 + 0.035 * math.log(3) - 0.06 * 5
        elif m >= 7.5:
            sigma = 1.18 + 0.035 * math.log(3) - 0.06 * 7.5
        else:
            sigma = 1.18 + 0.035 * math.log(3) - 0.06 * m
    else:
        if m <= 5:
            sigma = 1.18 + 0.035 * math.log(t) - 0.06 * 5
        elif m >= 7.5:
            sigma = 1.18 + 0.035 * math.log(t) - 0.06 * 7.5
        else:
            sigma = 1.18 + 0.035 * math.log(t) - 0.06 * m
    return sigma

def bssa_14_raw(m, rjb, u, rs, ns, vs30, region, z1, pgar, t):
    c, c1, c2, c3, counter, dc3, dc3chtur, dc3jpit = 0, 0, 0, 0, 0, 0, 0, 0
    dfr, dfv, dz1, e0, e1, e2, e3, e4 = 0, 0, 0, 0, 0, 0, 0, 0
    e5, e6, f1, f2, f3, f4, f5, f6 = 0, 0, 0, 0, 0, 0, 0, 0
    f7, flin, fm, fnl, fp, fs, fz1, h = 0, 0, 0, 0, 0, 0, 0, 0
    mh, minv, mref, mz1, phi1, phi2, r, r1 = 0, 0, 0, 0, 0, 0, 0, 0
    r2, rref, ss, tau1, tau2, v1, v2, vc = 0, 0, 0, 0, 0, 0, 0, 0
    vref, y = 0, 0
    cof = _cof('BSSA14', t)
    e0 = cof[0]
    e1 = cof[1]
    e2 = cof[2]
    e3 = cof[3]
    e4 = cof[4]
    e5 = cof[5]
    e6 = cof[6]
    mh = cof[7]
    c1 = cof[8]
    c2 = cof[9]
    c3 = cof[10]
    mref = cof[11]
    rref = cof[12]
    h = cof[13]
    dc3 = cof[14]
    dc3chtur = cof[15]
    dc3jpit = cof[16]
    c = cof[17]
    vc = cof[18]
    vref = cof[19]
    f1 = cof[20]
    f3 = cof[21]
    f4 = cof[22]
    f5 = cof[23]
    f6 = cof[24]
    f7 = cof[25]
    r1 = cof[26]
    r2 = cof[27]
    dfr = cof[28]
    dfv = cof[29]
    v1 = cof[30]
    v2 = cof[31]
    phi1 = cof[32]
    phi2 = cof[33]
    tau1 = cof[34]
    tau2 = cof[35]
    if ns == 0 and rs == 0 and u == 0:
        ss = 1
    else:
        ss = 0
    if m <= mh:
        fm = e0 * u + e1 * ss + e2 * ns + e3 * rs + e4 * (m - mh) + e5 * (m - mh) ** 2
    else:
        fm = e0 * u + e1 * ss + e2 * ns + e3 * rs + e6 * (m - mh)
    r = math.sqrt(rjb ** 2 + h ** 2)
    if region == 0:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3) * (r - rref)
    elif region == 3 or region == 5:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3chtur) * (r - rref)
    elif region == 1 or region == 4:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3jpit) * (r - rref)
    else:
        fp = (c1 + c2 * (m - mref)) * math.log(r / rref) + (c3 + dc3) * (r - rref)
    if vs30 <= vc:
        flin = c * math.log(vs30 / vref)
    else:
        flin = c * math.log(vc / vref)
    if vs30 < 760:
        minv = vs30
    else:
        minv = 760
    f2 = f4 * ((math.exp(f5 * (minv - 360))) - math.exp(f5 * (760 - 360)))
    fnl = f1 + f2 * math.log((pgar + f3) / f3)
    fnl = f1 + (f4 * ((math.exp(f5 * (minv - 360))) - math.exp(f5 * (760 - 360)))) * math.log((pgar + f3) / f3)
    if region == 0:
        mz1 = math.exp(-7.15 / 4 * math.log((vs30 ** 4 + 570.94 ** 4) / (1360 ** 4 + 570.94 ** 4))) / 1000
    elif region == 1:
        mz1 = math.exp(-5.23 / 2 * math.log((vs30 ** 2 + 412.39 ** 2) / (1360 ** 2 + 412.39 ** 2))) / 1000
    else:
        mz1 = math.exp(-7.15 / 4 * math.log((vs30 ** 4 + 570.94 ** 4) / (1360 ** 4 + 570.94 ** 4))) / 1000
    dz1 = z1 - mz1
    if z1 == 999:
        dz1 = 0
    else:
        dz1 = dz1
    if t < 0.65:
        fz1 = 0
    elif dz1 <= f7 / f6:
        fz1 = f6 * dz1
    elif dz1 > f7 / f6:
        fz1 = f7
    else:
        fz1 = 0
    if z1 == 999:
        fz1 = 0
    else:
        fz1 = fz1
    fs = flin + fnl
    y = math.exp(fm + fp + fs + fz1)
    return y

def bssa14_stdev_raw(m, rjb, vs30, t):
    c, c1, c2, c3, counter, dc3, dc3chtur, dc3jpit = 0, 0, 0, 0, 0, 0, 0, 0
    dfr, dfv, e0, e1, e2, e3, e4, e5 = 0, 0, 0, 0, 0, 0, 0, 0
    e6, f1, f3, f4, f5, f6, f7, h = 0, 0, 0, 0, 0, 0, 0, 0
    mh, mref, phi, phi1, phi2, phim, phimr, r1 = 0, 0, 0, 0, 0, 0, 0, 0
    r2, rref, sigma, tau1, tau2, taum, v1, v2 = 0, 0, 0, 0, 0, 0, 0, 0
    vc, vref = 0, 0
    cof = _cof('BSSA14', t)
    e0 = cof[0]
    e1 = cof[1]
    e2 = cof[2]
    e3 = cof[3]
    e4 = cof[4]
    e5 = cof[5]
    e6 = cof[6]
    mh = cof[7]
    c1 = cof[8]
    c2 = cof[9]
    c3 = cof[10]
    mref = cof[11]
    rref = cof[12]
    h = cof[13]
    dc3 = cof[14]
    dc3chtur = cof[15]
    dc3jpit = cof[16]
    c = cof[17]
    vc = cof[18]
    vref = cof[19]
    f1 = cof[20]
    f3 = cof[21]
    f4 = cof[22]
    f5 = cof[23]
    f6 = cof[24]
    f7 = cof[25]
    r1 = cof[26]
    r2 = cof[27]
    dfr = cof[28]
    dfv = cof[29]
    v1 = cof[30]
    v2 = cof[31]
    phi1 = cof[32]
    phi2 = cof[33]
    tau1 = cof[34]
    tau2 = cof[35]
    if m <= 4.5:
        taum = tau1
    elif m > 4.5 and m < 5.5:
        taum = tau1 + (tau2 - tau1) * (m - 4.5)
    else:
        taum = tau2
    if m <= 4.5:
        phim = phi1
    elif m > 4.5 and m < 5.5:
        phim = phi1 + (phi2 - phi1) * (m - 4.5)
    else:
        phim = phi2
    if rjb <= r1:
        phimr = phim
    elif rjb > r1 and rjb <= r2:
        phimr = phim + dfr * (math.log(rjb / r1) / (math.log(r2 / r1)))
    else:
        phimr = phim + dfr
    if vs30 >= v2:
        phi = phimr
    elif vs30 >= v1 and vs30 <= v2:
        phi = phimr - dfv * (math.log(v2 / vs30) / (math.log(v2 / v1)))
    else:
        phi = phimr - dfv
    sigma = math.sqrt(taum ** 2 + phi ** 2)
    return sigma

def a1100_cb(m, rrup, rjb, rx, frv, fnm, fhw, w, delta, ztor, z25, zhyp, ztord, wd, zhypd, region, t):
    a1100, a2, c, c0, c1, c10, c11, c12 = 0, 0, 0, 0, 0, 0, 0, 0
    c13, c14, c15, c16, c17, c18, c19, c2 = 0, 0, 0, 0, 0, 0, 0, 0
    c20, c3, c4, c5, c6, c7, c8, c9 = 0, 0, 0, 0, 0, 0, 0, 0
    counter, dc20, dc20ca, dc20ch, dc20jp, f1_rx, f2_rx, f2x = 0, 0, 0, 0, 0, 0, 0, 0
    fatn, fdip, fdis, fflt, ffltf, ffltm, fhng, fhngm = 0, 0, 0, 0, 0, 0, 0, 0
    fhngr, fhngrx, fhngs, fhngz, fhyp, fhyph, fhypm, fmag = 0, 0, 0, 0, 0, 0, 0, 0
    fsed, h1, h2, h3, h4, h5, h6, k1 = 0, 0, 0, 0, 0, 0, 0, 0
    k2, k3, maxr, n, pi, r1, r2, sj = 0, 0, 0, 0, 0, 0, 0, 0
    y, z25r = 0, 0
    cof = _cof('CB14', t)
    c0 = cof[0]
    c1 = cof[1]
    c2 = cof[2]
    c3 = cof[3]
    c4 = cof[4]
    c5 = cof[5]
    c6 = cof[6]
    c7 = cof[7]
    c8 = cof[8]
    c9 = cof[9]
    c10 = cof[10]
    c11 = cof[11]
    c12 = cof[12]
    c13 = cof[13]
    c14 = cof[14]
    c15 = cof[15]
    c16 = cof[16]
    c17 = cof[17]
    c18 = cof[18]
    c19 = cof[19]
    c20 = cof[20]
    dc20ca = cof[21]
    dc20jp = cof[22]
    dc20ch = cof[23]
    a2 = cof[24]
    h1 = cof[25]
    h2 = cof[26]
    h3 = cof[27]
    h4 = cof[28]
    h5 = cof[29]
    h6 = cof[30]
    k1 = cof[31]
    k2 = cof[32]
    k3 = cof[33]
    c = cof[34]
    n = cof[35]
    pi = 4 * math.atan(1)
    if region == 1:
        sj = 1
    else:
        sj = 0
    if ztor == 999:
        ztor = ztord
    else:
        ztor = ztor
    if zhyp == 999:
        zhyp = zhypd
    else:
        zhyp = zhyp
    if w == 999:
        zhyp = 9
    else:
        zhyp = zhyp
    if w == 999:
        w = wd
    else:
        w = w
    z25r = (1 - sj) * math.exp(7.089 - 1.144 * math.log(1100)) + sj * math.exp(5.359 - 1.102 * math.log(1100))
    if z25 == 999:
        z25 = z25r
    else:
        z25 = z25
    if m <= 4.5:
        fmag = (c1 * m)
    elif m <= 5.5:
        fmag = (c1 * m) + (c2 * (m - 4.5))
    elif m <= 6.5:
        fmag = (c1 * m) + (c2 * (m - 4.5)) + (c3 * (m - 5.5))
    elif m > 6.5:
        fmag = (c1 * m) + (c2 * (m - 4.5)) + (c3 * (m - 5.5)) + (c4 * (m - 6.5))
    fdis = ((c5 + (c6 * m)) * (math.log(math.sqrt((rrup * rrup) + (c7 * c7)))))
    ffltf = (c8 * frv) + (c9 * fnm)
    if m <= 4.5:
        ffltm = 0
    elif m <= 5.5:
        ffltm = m - 4.5
    elif m > 5.5:
        ffltm = 1
    fflt = ffltf * ffltm
    r1 = w * math.cos(delta * pi / 180)
    r2 = 62 * m - 350
    f1_rx = h1 + h2 * (rx / r1) + h3 * (rx / r1) ** 2
    f2_rx = h4 + h5 * ((rx - r1) / (r2 - r1)) + h6 * ((rx - r1) / (r2 - r1)) ** 2
    if f2_rx > 0:
        maxr = f2_rx
    else:
        maxr = 0
    if fhw == 0:
        fhngrx = 0
    elif rx < r1 and fhw == 1:
        fhngrx = f1_rx
    elif rx >= r1 and fhw == 1:
        fhngrx = maxr
    if rrup == 0:
        fhngr = 1
    elif rrup > 0:
        fhngr = (rrup - rjb) / rrup
    if f2_rx > 0:
        f2x = f2_rx
    else:
        f2x = 0
    if m <= 5.5:
        fhngm = 0
    elif m <= 6.5:
        fhngm = (m - 5.5) * (1 + a2 * (m - 6.5))
    elif m > 6.5:
        fhngm = 1 + a2 * (m - 6.5)
    if ztor < 16.66:
        fhngz = 1 - 0.06 * ztor
    elif ztor >= 16.66:
        fhngz = 0
    fhngs = (90 - delta) / 45
    fhng = c10 * fhngrx * fhngr * fhngm * fhngz * fhngs
    if z25 <= 1:
        fsed = (c14 + c15 * sj) * (z25 - 1)
    elif z25 > 1 and z25 <= 3:
        fsed = 0
    else:
        fsed = c16 * k3 * math.exp(-0.75) * (1 - math.exp(-0.25 * (z25 - 3)))
    if zhyp <= 7:
        fhyph = 0
    elif zhyp > 7 and zhyp <= 20:
        fhyph = zhyp - 7
    else:
        fhyph = 13
    if m <= 5.5:
        fhypm = c17
    elif m > 5.5 and m <= 6.5:
        fhypm = c17 + (c18 - c17) * (m - 5.5)
    else:
        fhypm = c18
    fhyp = fhyph * fhypm
    if m <= 4.5:
        fdip = c19 * delta
    elif m > 4.5 and m <= 5.5:
        fdip = c19 * (5.5 - m) * delta
    else:
        fdip = 0
    if region == 0:
        dc20 = dc20ca
    elif region == 1 or region == 4:
        dc20 = dc20jp
    elif region == 3:
        dc20 = dc20ch
    else:
        dc20 = dc20ca
    if rrup > 80:
        fatn = (c20 + dc20) * (rrup - 80)
    elif rrup <= 80:
        fatn = 0
    if z25r < 1:
        a1100 = c0 + fmag + fdis + fflt + fhng + fhyp + fdip + fatn +      (c11 + k2 * n) * math.log(1100 / k1) + sj * (c13 + k2 * n) * math.log(1100 / k1) +      (c14 + sj * c15) * (z25r - 1)
    elif z25r > 3:
        a1100 = c0 + fmag + fdis + fflt + fhng + fhyp + fdip + fatn +      (c11 + k2 * n) * math.log(1100 / k1) + sj * (c13 + k2 * n) * math.log(1100 / k1) +      c16 * k3 * math.exp(-0.75) * (1 - math.exp(-0.25 * (z25r - 3)))
    else:
        a1100 = c0 + fmag + fdis + fflt + fhng + fhyp + fdip + fatn +      (c11 + k2 * n) * math.log(1100 / k1) + sj * (c13 + k2 * n) * math.log(1100 / k1)
    y = math.exp(a1100)
    return y

def cb_14_raw(m, rrup, rjb, rx, frv, fnm, fhw, ztor, w, delta, vs30, z25, zhyp, ztord, wd, zhypd, region, a, t):
    a2, c, c0, c1, c10, c11, c12, c13 = 0, 0, 0, 0, 0, 0, 0, 0
    c14, c15, c16, c17, c18, c19, c2, c20 = 0, 0, 0, 0, 0, 0, 0, 0
    c3, c4, c5, c6, c7, c8, c9, counter = 0, 0, 0, 0, 0, 0, 0, 0
    dc20, dc20ca, dc20ch, dc20jp, f1_rx, f2_rx, f2x, fatn = 0, 0, 0, 0, 0, 0, 0, 0
    fdip, fdis, fflt, ffltf, ffltm, fhng, fhngm, fhngr = 0, 0, 0, 0, 0, 0, 0, 0
    fhngrx, fhngs, fhngz, fhyp, fhyph, fhypm, fmag, fsed = 0, 0, 0, 0, 0, 0, 0, 0
    fsite, fsitej, h1, h2, h3, h4, h5, h6 = 0, 0, 0, 0, 0, 0, 0, 0
    k1, k2, k3, maxr, median, n, phi1, phi2 = 0, 0, 0, 0, 0, 0, 0, 0
    phic, philnaf, pi, r1, r2, ro, sj, sjp = 0, 0, 0, 0, 0, 0, 0, 0
    tau1, tau2, y, ypgacb = 0, 0, 0, 0
    cof = _cof('CB14', t)
    c0 = cof[0]
    c1 = cof[1]
    c2 = cof[2]
    c3 = cof[3]
    c4 = cof[4]
    c5 = cof[5]
    c6 = cof[6]
    c7 = cof[7]
    c8 = cof[8]
    c9 = cof[9]
    c10 = cof[10]
    c11 = cof[11]
    c12 = cof[12]
    c13 = cof[13]
    c14 = cof[14]
    c15 = cof[15]
    c16 = cof[16]
    c17 = cof[17]
    c18 = cof[18]
    c19 = cof[19]
    c20 = cof[20]
    dc20ca = cof[21]
    dc20jp = cof[22]
    dc20ch = cof[23]
    a2 = cof[24]
    h1 = cof[25]
    h2 = cof[26]
    h3 = cof[27]
    h4 = cof[28]
    h5 = cof[29]
    h6 = cof[30]
    k1 = cof[31]
    k2 = cof[32]
    k3 = cof[33]
    c = cof[34]
    n = cof[35]
    phi1 = cof[36]
    phi2 = cof[37]
    tau1 = cof[38]
    tau2 = cof[39]
    philnaf = cof[40]
    phic = cof[41]
    ro = cof[42]
    pi = 4 * math.atan(1)
    if region == 1:
        sj = 1
    else:
        sj = 0
    if ztor == 999:
        ztor = ztord
    else:
        ztor = ztor
    if zhyp == 999:
        zhyp = zhypd
    else:
        zhyp = zhyp
    if w == 999:
        zhyp = 9
    else:
        zhyp = zhyp
    if w == 999:
        w = wd
    else:
        w = w
    if m <= 4.5:
        fmag = (c1 * m)
    elif m <= 5.5:
        fmag = (c1 * m) + (c2 * (m - 4.5))
    elif m <= 6.5:
        fmag = (c1 * m) + (c2 * (m - 4.5)) + (c3 * (m - 5.5))
    elif m > 6.5:
        fmag = (c1 * m) + (c2 * (m - 4.5)) + (c3 * (m - 5.5)) + (c4 * (m - 6.5))
    fdis = ((c5 + (c6 * m)) * (math.log(math.sqrt((rrup * rrup) + (c7 * c7)))))
    ffltf = (c8 * frv) + (c9 * fnm)
    if m <= 4.5:
        ffltm = 0
    elif m <= 5.5:
        ffltm = m - 4.5
    elif m > 5.5:
        ffltm = 1
    fflt = ffltf * ffltm
    r1 = w * math.cos(delta * pi / 180)
    r2 = 62 * m - 350
    f1_rx = h1 + h2 * (rx / r1) + h3 * (rx / r1) ** 2
    f2_rx = h4 + h5 * ((rx - r1) / (r2 - r1)) + h6 * ((rx - r1) / (r2 - r1)) ** 2
    if f2_rx > 0:
        maxr = f2_rx
    else:
        maxr = 0
    if fhw == 0:
        fhngrx = 0
    elif rx < r1 and fhw == 1:
        fhngrx = f1_rx
    elif rx >= r1 and fhw == 1:
        fhngrx = maxr
    if rrup == 0:
        fhngr = 1
    elif rrup > 0:
        fhngr = (rrup - rjb) / rrup
    if f2_rx > 0:
        f2x = f2_rx
    else:
        f2x = 0
    if m <= 5.5:
        fhngm = 0
    elif m <= 6.5:
        fhngm = (m - 5.5) * (1 + a2 * (m - 6.5))
    elif m > 6.5:
        fhngm = 1 + a2 * (m - 6.5)
    if ztor < 16.66:
        fhngz = 1 - 0.06 * ztor
    elif ztor >= 16.66:
        fhngz = 0
    fhngs = (90 - delta) / 45
    fhng = c10 * fhngrx * fhngr * fhngm * fhngz * fhngs
    if region == 1:
        sjp = 1
    else:
        sjp = 0
    if vs30 <= k1:
        fsite = c11 * math.log(vs30 / k1) + k2 * (math.log(a + c * (vs30 / k1) ** n) - math.log(a + c))
    else:
        fsite = (c11 + k2 * n) * math.log(vs30 / k1)
    if vs30 <= 200:
        fsitej = (c12 + k2 * n) * (math.log(vs30 / k1) - math.log(200 / k1)) * sjp
    else:
        fsitej = (c13 + k2 * n) * math.log(vs30 / k1) * sjp
    fsite = fsite + fsitej
    if z25 == 999:
        if region == 1:
            z25 = math.exp(5.359 - 1.102 * math.log(vs30))
        else:
            z25 = math.exp(7.089 - 1.144 * math.log(vs30))
    if z25 <= 1:
        fsed = (c14 + c15 * sj) * (z25 - 1)
    elif z25 > 1 and z25 <= 3:
        fsed = 0
    else:
        fsed = c16 * k3 * math.exp(-0.75) * (1 - math.exp(-0.25 * (z25 - 3)))
    if zhyp <= 7:
        fhyph = 0
    elif zhyp > 7 and zhyp <= 20:
        fhyph = zhyp - 7
    else:
        fhyph = 13
    if m <= 5.5:
        fhypm = c17
    elif m > 5.5 and m <= 6.5:
        fhypm = c17 + (c18 - c17) * (m - 5.5)
    else:
        fhypm = c18
    fhyp = fhyph * fhypm
    if m <= 4.5:
        fdip = c19 * delta
    elif m > 4.5 and m <= 5.5:
        fdip = c19 * (5.5 - m) * delta
    else:
        fdip = 0
    if region == 0:
        dc20 = dc20ca
    elif region == 1 or region == 4:
        dc20 = dc20jp
    elif region == 3:
        dc20 = dc20ch
    else:
        dc20 = dc20ca
    if rrup > 80:
        fatn = (c20 + dc20) * (rrup - 80)
    elif rrup <= 80:
        fatn = 0
    median = math.exp(c0 + fmag + fdis + fflt + fhng + fsite + fsed + fhyp + fdip + fatn)
    if t == 0:
        ypgacb = median
    if t < 0.25 and t != 0 and median < ypgacb:
        y = ypgacb
    else:
        y = median
    return y

def cy_14_raw(m, rrup, rjb, rx, vs30, frv, fnm, fhw, delta, ztor, region, z1, z1r, ddpp, t):
    c1, c11, c11b, c1a, c1b, c1c, c1d, c2 = 0, 0, 0, 0, 0, 0, 0, 0
    c3, c4, c4a, c5, c6, c7, c7b, c8 = 0, 0, 0, 0, 0, 0, 0, 0
    c8a, c8b, c9, c9a, c9b, cg1, cg2, cg3 = 0, 0, 0, 0, 0, 0, 0, 0
    chm, cm, cn, counter, crb, deltaz1, deltaz_tor, e = 0, 0, 0, 0, 0, 0, 0, 0
    f1, f1jp, f2, f3, f4, f5, f5jp, f6 = 0, 0, 0, 0, 0, 0, 0, 0
    f6jp, fatn, fdip, fdir, fdis, fflt, fhng, fmag = 0, 0, 0, 0, 0, 0, 0, 0
    fsite, ftor, g, gjpit, gwn, k, maxdir, maxdir1 = 0, 0, 0, 0, 0, 0, 0, 0
    maxdir2, maxoftwo, maxoftwo2, maxztord, maxztorm, maxztorz, mindir, minoftwo = 0, 0, 0, 0, 0, 0, 0, 0
    minoftwo2, mz, mz1, mz_tor, mz_torx, mz_torz, pi, rkdepth = 0, 0, 0, 0, 0, 0, 0, 0
    s1, s2, s2jp, s3, t1, t2, tanh, x = 0, 0, 0, 0, 0, 0, 0, 0
    y, ypga, yref, z = 0, 0, 0, 0
    cof = _cof('CY14', t)
    c2 = cof[0]
    c4 = cof[1]
    c4a = cof[2]
    crb = cof[3]
    c8 = cof[4]
    c8a = cof[5]
    c1 = cof[6]
    c1a = cof[7]
    c1b = cof[8]
    c1c = cof[9]
    c1d = cof[10]
    cn = cof[11]
    cm = cof[12]
    c3 = cof[13]
    c5 = cof[14]
    chm = cof[15]
    c6 = cof[16]
    c7 = cof[17]
    c7b = cof[18]
    c8b = cof[19]
    c9 = cof[20]
    c9a = cof[21]
    c9b = cof[22]
    c11 = cof[23]
    c11b = cof[24]
    cg1 = cof[25]
    cg2 = cof[26]
    cg3 = cof[27]
    f1 = cof[28]
    f2 = cof[29]
    f3 = cof[30]
    f4 = cof[31]
    f5 = cof[32]
    f6 = cof[33]
    t1 = cof[34]
    t2 = cof[35]
    s1 = cof[36]
    s2 = cof[37]
    s3 = cof[38]
    s2jp = cof[39]
    gjpit = cof[40]
    gwn = cof[41]
    f1jp = cof[42]
    f5jp = cof[43]
    f6jp = cof[44]
    pi = 4 * math.atan(1)
    if region == 1:
        f1 = f1jp
    if region == 1:
        s2 = s2jp
    if region == 1:
        f5 = f5jp
    if region == 1 or region == 4:
        g = gjpit
    if region == 3:
        g = gwn
    if region == 1:
        f6 = f6jp
    fmag = c2 * (m - 6) + (c2 - c3) / cn * math.log(1 + math.exp(cn * (cm - m)))
    if (m - chm) > 0:
        maxoftwo = (m - chm)
    else:
        maxoftwo = 0
    x = c6 * maxoftwo
    if (m - cg3) > 0:
        e = m - cg3
    else:
        e = 0
    if (region == 1 or region == 4) and (6 < m and m < 6.9):
        fatn = gjpit * (cg1 + cg2 / ((math.exp(e) + math.exp(-e)) / 2)) * rrup
    elif region == 3:
        fatn = gwn * (cg1 + cg2 / ((math.exp(e) + math.exp(-e)) / 2)) * rrup
    else:
        fatn = (cg1 + cg2 / ((math.exp(e) + math.exp(-e)) / 2)) * rrup
    fdis = c4 * math.log(rrup + c5 * (math.exp(x) + math.exp(-x)) / 2) + (c4a - c4) * math.log(math.sqrt(rrup ** 2 + crb ** 2)) + fatn
    if (m - 4.5) > 0:
        maxoftwo2 = m - 4.5
    else:
        maxoftwo2 = 0
    z = 2 * maxoftwo2
    fflt = frv * (c1a + c1c / ((math.exp(z) + math.exp(-z)) / 2)) + fnm * (c1b + c1d / ((math.exp(z) + math.exp(-z)) / 2))
    k = rx / c9b
    tanh = (math.exp(k) - math.exp(-k)) / (math.exp(k) + math.exp(-k))
    if 2.704 - 1.226 * (m - 5.849) > 0:
        maxztorm = 2.704 - 1.226 * (m - 5.849)
    else:
        maxztorm = 0
    if m <= 5.849 and frv == 1:
        mz_torx = 2.704 * 2.704
    else:
        mz_torx = maxztorm * maxztorm
    if 2.673 - 1.136 * (m - 4.97) > 0 and fnm == 1:
        maxztorz = 2.673 - 1.136 * (m - 4.97)
    else:
        maxztorz = 0
    if m <= 4.97 and fnm == 1:
        mz_torz = 2.673 * 2.673
    else:
        mz_torz = maxztorz * maxztorz
    if (m - 4.97) > 0 and fnm == 0 and frv == 0:
        mz = m - 4.97
    else:
        mz = 0
    if 2.673 - 1.136 * (m - 4.97) > 0 and fnm == 0 and frv == 0:
        maxztord = 2.673 - 1.136 * mz
    else:
        maxztord = 0
    if frv == 1:
        mz_tor = mz_torx
    elif fnm == 1:
        mz_tor = mz_torz
    else:
        mz_tor = maxztord * maxztord
    if ztor == 999:
        ztor = mz_tor
    else:
        ztor = ztor
    deltaz_tor = ztor - mz_tor
    ftor = (c7 + c7b / ((math.exp(z) + math.exp(-z)) / 2)) * deltaz_tor
    if fhw == 0:
        fhng = 0
    else:
        fhng = c9 * fhw * math.cos(delta * pi / 180) * (c9a + (1 - c9a) * tanh) * (1 - math.sqrt(rjb ** 2 + ztor ** 2) / (rrup + 1))
    if z1 == 999:
        z1 = z1r
    else:
        z1 = z1
    if region == 1:
        mz1 = z1 * 1000 - math.exp(-5.23 / 2 * math.log((vs30 ** 2 + 412.39 ** 2) / (1360 ** 2 + 412.39 ** 2)))
    else:
        mz1 = z1 * 1000 - math.exp(-7.15 / 4 * math.log((vs30 ** 4 + 570.94 ** 4) / (1360 ** 4 + 570.94 ** 4)))
    if z1 == z1r:
        deltaz1 = 0
    else:
        deltaz1 = mz1
    fdip = (math.cos(delta * pi / 180) ** 2) * (c11 + c11b / ((math.exp(z) + math.exp(-z)) / 2))
    if (rrup - 40) > 0:
        maxdir = rrup - 40
    else:
        maxdir = 0
    if 1 - maxdir / 30 > 0:
        maxdir1 = 1 - maxdir / 30
    else:
        maxdir1 = 0
    if (m - 5.5) > 0:
        maxdir2 = m - 5.5
    else:
        maxdir2 = 0
    if maxdir2 / 0.8 < 1:
        mindir = maxdir2 / 0.8
    else:
        mindir = 1
    fdir = c8 * maxdir1 * mindir * math.exp(-c8a * (m - c8b) ** 2) * ddpp
    yref = math.exp(c1 + fmag + fdis + fflt + fhng + ftor + fdip + fdir)
    if math.log(vs30 / 1130) < 0:
        minoftwo = math.log(vs30 / 1130)
    else:
        minoftwo = 0
    if vs30 < 1130:
        minoftwo2 = vs30
    else:
        minoftwo2 = 1130
    rkdepth = f5 * (1 - math.exp(-deltaz1 / f6))
    fsite = f1 * minoftwo + f2 * (math.exp(f3 * (minoftwo2 - 360)) - math.exp(f3 * (1130 - 360))) * math.log((yref + f4) / f4)
    y = yref * math.exp(fsite + rkdepth)
    if t == 0:
        ypga = y
    if t <= 0.3 and t != 0 and y < ypga:
        y = ypga
    else:
        y = y
    return y

def cy14_stdev_raw(m, rrup, rjb, rx, vs30, frv, fnm, fhw, delta, ztor, region, z1, ddpp, vs30flag, t):
    b, c1, c11, c11b, c1a, c1b, c1c, c1d = 0, 0, 0, 0, 0, 0, 0, 0
    c2, c3, c4, c4a, c5, c6, c7, c7b = 0, 0, 0, 0, 0, 0, 0, 0
    c8, c8a, c8b, c9, c9a, c9b, cg1, cg2 = 0, 0, 0, 0, 0, 0, 0, 0
    cg3, chm, cm, cn, counter, crb, deltaz_tor, e = 0, 0, 0, 0, 0, 0, 0, 0
    f1, f1jp, f2, f3, f4, f5, f5jp, f6 = 0, 0, 0, 0, 0, 0, 0, 0
    f6jp, fatn, fdip, fdir, fdis, fflt, fhng, finf = 0, 0, 0, 0, 0, 0, 0, 0
    fmag, fmeas, ftor, g, gjpit, gwn, k, maxdir = 0, 0, 0, 0, 0, 0, 0, 0
    maxdir1, maxdir2, maxoftwo, maxoftwo2, maxt, maxztord, maxztorm, maxztorz = 0, 0, 0, 0, 0, 0, 0, 0
    mindir, minoftwo, minoftwo2, mint, mz, mz_tor, mz_torx, mz_torz = 0, 0, 0, 0, 0, 0, 0, 0
    nl0, phi, pi, s, s1, s2, s2jp, s3 = 0, 0, 0, 0, 0, 0, 0, 0
    sigma, sigma_nl0, sigma_nl0_s, t1, t2, tanh, tau, x = 0, 0, 0, 0, 0, 0, 0, 0
    yref, z = 0, 0
    cof = _cof('CY14', t)
    c2 = cof[0]
    c4 = cof[1]
    c4a = cof[2]
    crb = cof[3]
    c8 = cof[4]
    c8a = cof[5]
    c1 = cof[6]
    c1a = cof[7]
    c1b = cof[8]
    c1c = cof[9]
    c1d = cof[10]
    cn = cof[11]
    cm = cof[12]
    c3 = cof[13]
    c5 = cof[14]
    chm = cof[15]
    c6 = cof[16]
    c7 = cof[17]
    c7b = cof[18]
    c8b = cof[19]
    c9 = cof[20]
    c9a = cof[21]
    c9b = cof[22]
    c11 = cof[23]
    c11b = cof[24]
    cg1 = cof[25]
    cg2 = cof[26]
    cg3 = cof[27]
    f1 = cof[28]
    f2 = cof[29]
    f3 = cof[30]
    f4 = cof[31]
    f5 = cof[32]
    f6 = cof[33]
    t1 = cof[34]
    t2 = cof[35]
    s1 = cof[36]
    s2 = cof[37]
    s3 = cof[38]
    s2jp = cof[39]
    gjpit = cof[40]
    gwn = cof[41]
    f1jp = cof[42]
    f5jp = cof[43]
    f6jp = cof[44]
    pi = 4 * math.atan(1)
    if region == 1:
        f1 = f1jp
    if region == 1:
        s2 = s2jp
    if region == 1:
        f5 = f5jp
    if region == 1 or region == 4:
        g = gjpit
    if region == 3:
        g = gwn
    if region == 1:
        f6 = f6jp
    fmag = c2 * (m - 6) + (c2 - c3) / cn * math.log(1 + math.exp(cn * (cm - m)))
    if (m - chm) > 0:
        maxoftwo = (m - chm)
    else:
        maxoftwo = 0
    x = c6 * maxoftwo
    if (m - cg3) > 0:
        e = m - cg3
    else:
        e = 0
    if (region == 1 or region == 4) and (6 < m and m < 6.9):
        fatn = gjpit * (cg1 + cg2 / ((math.exp(e) + math.exp(-e)) / 2)) * rrup
    elif region == 3:
        fatn = gwn * (cg1 + cg2 / ((math.exp(e) + math.exp(-e)) / 2)) * rrup
    else:
        fatn = (cg1 + cg2 / ((math.exp(e) + math.exp(-e)) / 2)) * rrup
    fdis = c4 * math.log(rrup + c5 * (math.exp(x) + math.exp(-x)) / 2) + (c4a - c4) * math.log(math.sqrt(rrup ** 2 + crb ** 2)) + fatn
    if (m - 4.5) > 0:
        maxoftwo2 = m - 4.5
    else:
        maxoftwo2 = 0
    z = 2 * maxoftwo2
    fflt = frv * (c1a + c1c / ((math.exp(z) + math.exp(-z)) / 2)) + fnm * (c1b + c1d / ((math.exp(z) + math.exp(-z)) / 2))
    k = rx / c9b
    tanh = (math.exp(k) - math.exp(-k)) / (math.exp(k) + math.exp(-k))
    if 2.704 - 1.226 * (m - 5.849) > 0:
        maxztorm = 2.704 - 1.226 * (m - 5.849)
    else:
        maxztorm = 0
    if m <= 5.849 and frv == 1:
        mz_torx = 2.704 * 2.704
    else:
        mz_torx = maxztorm * maxztorm
    if 2.673 - 1.136 * (m - 4.97) > 0 and fnm == 1:
        maxztorz = 2.673 - 1.136 * (m - 4.97)
    else:
        maxztorz = 0
    if m <= 4.97 and fnm == 1:
        mz_torz = 2.673 * 2.673
    else:
        mz_torz = maxztorz * maxztorz
    if (m - 4.97) > 0 and fnm == 0 and frv == 0:
        mz = m - 4.97
    else:
        mz = 0
    if 2.673 - 1.136 * (m - 4.97) > 0 and fnm == 0 and frv == 0:
        maxztord = 2.673 - 1.136 * mz
    else:
        maxztord = 0
    if frv == 1:
        mz_tor = mz_torx
    elif fnm == 1:
        mz_tor = mz_torz
    else:
        mz_tor = maxztord * maxztord
    if ztor == 999:
        ztor = mz_tor
    else:
        ztor = ztor
    deltaz_tor = ztor - mz_tor
    ftor = (c7 + c7b / ((math.exp(z) + math.exp(-z)) / 2)) * deltaz_tor
    if fhw == 0:
        fhng = 0
    else:
        fhng = c9 * fhw * math.cos(delta * pi / 180) * (c9a + (1 - c9a) * tanh) * (1 - math.sqrt(rjb ** 2 + ztor ** 2) / (rrup + 1))
    fdip = (math.cos(delta * pi / 180) ** 2) * (c11 + c11b / ((math.exp(z) + math.exp(-z)) / 2))
    if (rrup - 40) > 0:
        maxdir = rrup - 40
    else:
        maxdir = 0
    if 1 - maxdir / 30 > 0:
        maxdir1 = 1 - maxdir / 30
    else:
        maxdir1 = 0
    if (m - 5.5) > 0:
        maxdir2 = m - 5.5
    else:
        maxdir2 = 0
    if maxdir2 / 0.8 < 1:
        mindir = maxdir2 / 0.8
    else:
        mindir = 1
    fdir = c8 * maxdir1 * mindir * math.exp(-c8a * (m - c8b) ** 2) * ddpp
    yref = math.exp(c1 + fmag + fdis + fflt + fhng + ftor + fdip + fdir)
    if math.log(vs30 / 1130) < 0:
        minoftwo = math.log(vs30 / 1130)
    else:
        minoftwo = 0
    if vs30 < 1130:
        minoftwo2 = vs30
    else:
        minoftwo2 = 1130
    b = f2 * (math.exp(f3 * (minoftwo2 - 360)) - math.exp(f3 * (1130 - 360)))
    nl0 = b * (yref / (yref + f4))
    if m >= 5:
        maxt = m
    else:
        maxt = 5
    if maxt < 6.5:
        mint = maxt
    else:
        mint = 6.5
    tau = t1 + (t2 - t1) / 1.5 * (mint - 5)
    sigma_nl0_s = s1 + (s2 - s1) / 1.5 * (mint - 5)
    if vs30flag == 1:
        fmeas = 1
    elif vs30flag == 0:
        finf = 1
    sigma_nl0 = sigma_nl0_s * math.sqrt(0.7 * fmeas + finf * s3 + (1 + nl0) ** 2)
    sigma = math.sqrt((tau * (1 + nl0)) ** 2 + sigma_nl0 ** 2)
    phi = sigma_nl0
    tau = (tau * (1 + nl0))
    s = sigma
    return s

def ask_14_raw(m, rrup, rjb, rx, frv, fnm, fhw, fas, ztor, w, dip, vs30, vs30flag, z1, ry0, region, t):
    a1, a10, a11, a12, a13, a14, a15, a16 = 0, 0, 0, 0, 0, 0, 0, 0
    a17, a2, a25, a28, a29, a2hw, a3, a31 = 0, 0, 0, 0, 0, 0, 0, 0
    a36, a37, a38, a39, a4, a40, a41, a42 = 0, 0, 0, 0, 0, 0, 0, 0
    a43, a44, a45, a46, a5, a6, a7, a8 = 0, 0, 0, 0, 0, 0, 0, 0
    b, bq, br, bs, by, c, c4, c4m = 0, 0, 0, 0, 0, 0, 0, 0
    counter, crjb, f1, f10, f11, f12, f13, f4 = 0, 0, 0, 0, 0, 0, 0, 0
    f5, f6, f7, f8, h1, h2, h3, m1 = 0, 0, 0, 0, 0, 0, 0, 0
    m1z, m2, m2z, maxm, maxval, maxz, n, pi = 0, 0, 0, 0, 0, 0, 0, 0
    r, r1, r2, rd, reg, rvs, ry1, s1 = 0, 0, 0, 0, 0, 0, 0, 0
    s1v, s2, s2v, s3, s4, s5, s6, sa1180 = 0, 0, 0, 0, 0, 0, 0, 0
    t1, t2, t3, t4, t5, v1, vlin, vs30star = 0, 0, 0, 0, 0, 0, 0, 0
    vs30star1180, west, x1, x1z, x2, x2z, y, y1 = 0, 0, 0, 0, 0, 0, 0, 0
    y1z, y2, y2z, z1r, ztord = 0, 0, 0, 0, 0
    cof = _cof('ASK14', t)
    vlin = cof[0]
    b = cof[1]
    n = cof[2]
    m1 = cof[3]
    c = cof[4]
    c4 = cof[5]
    a1 = cof[6]
    a2 = cof[7]
    a3 = cof[8]
    a4 = cof[9]
    a5 = cof[10]
    a6 = cof[11]
    a7 = cof[12]
    a8 = cof[13]
    a10 = cof[14]
    a11 = cof[15]
    a12 = cof[16]
    a13 = cof[17]
    a14 = cof[18]
    a15 = cof[19]
    a16 = cof[20]
    a17 = cof[21]
    a43 = cof[22]
    a44 = cof[23]
    a45 = cof[24]
    a46 = cof[25]
    a25 = cof[26]
    a28 = cof[27]
    a29 = cof[28]
    a31 = cof[29]
    a36 = cof[30]
    a37 = cof[31]
    a38 = cof[32]
    a39 = cof[33]
    a40 = cof[34]
    a41 = cof[35]
    a42 = cof[36]
    s1 = cof[37]
    s2 = cof[38]
    s3 = cof[39]
    s4 = cof[40]
    s1v = cof[41]
    s2v = cof[42]
    s5 = cof[43]
    s6 = cof[44]
    a2hw = 0.2
    h1 = 0.25
    h2 = 1.5
    h3 = -0.75
    m2 = 5
    n = 1.5
    a7 = 0
    crjb = 999.9
    pi = 4 * math.atan(1)
    if ztor == 999:
        if frv == 1:
            maxm = m - 5.849
            if 0 > maxm:
                maxm = 0
            maxz = 2.704 - 1.226 * maxm
            if 0 > maxz:
                maxz = 0
        else:
            maxm = m - 4.97
            if 0 > maxm:
                maxm = 0
            maxz = 2.673 - 1.136 * maxm
            if 0 > maxz:
                maxz = 0
        ztor = maxz ** 2
    if 18 / math.sin(dip * pi / 180) < 10 ** (-1.75 + 0.45 * m):
        west = 18 / math.sin(dip * pi / 180)
    else:
        west = 10 ** (-1.75 + 0.45 * m)
    if w == 999:
        w = west
    else:
        w = w
    m1z = 5
    m2z = 7.2
    maxval = 7.8
    if m <= m1z:
        ztord = maxval
    elif m <= m2z:
        ztord = maxval - (maxval / (m2 - m1)) * (m - m1)
    else:
        ztord = 0
    if ztor == 999:
        ztor = ztord
    else:
        ztor = ztor
    if m >= 5:
        c4m = c4
    elif m >= 4:
        c4m = c4 - (c4 - 1) * (5 - m)
    else:
        c4m = 1
    r = math.sqrt(rrup ** 2 + c4m ** 2)
    if m < m2:
        f1 = a1 + a4 * (m2 - m1) + a8 * (8.5 - m2) ** 2 + a6 * (m - m2) + a7 * (m - m2) ** 2 + (a2 + a3 * (m2 - m1)) * math.log(r) + a17 * rrup
    elif m < m1:
        f1 = a1 + a4 * (m - m1) + a8 * (8.5 - m) ** 2 + (a2 + a3 * (m - m1)) * math.log(r) + a17 * rrup
    else:
        f1 = a1 + a5 * (m - m1) + a8 * (8.5 - m) ** 2 + (a2 + a3 * (m - m1)) * math.log(r) + a17 * rrup
    if t >= 3:
        v1 = 800
    elif t > 0.5:
        v1 = math.exp(-0.35 * math.log(t / 0.5) + math.log(1500))
    else:
        v1 = 1500
    if vs30 < v1:
        vs30star = vs30
    else:
        vs30star = v1
    if ztor <= 20:
        f6 = a15 * ztor / 20
    elif ztor > 20:
        f6 = a15
    if m < 4:
        f7 = 0
    elif m <= 5:
        f7 = a11 * (m - 4)
    else:
        f7 = a11
    if m < 4:
        f8 = 0
    elif m <= 5:
        f8 = a12 * (m - 4)
    else:
        f8 = a12
    r1 = w * math.cos(dip * pi / 180)
    r2 = 3 * r1
    ry1 = rx * math.tan(20 * pi / 180)
    if dip > 30:
        t1 = (90 - dip) / 45
    else:
        t1 = 60 / 45
    if m > 6.5:
        t2 = 1 + a2hw * (m - 6.5)
    elif m > 5.5:
        t2 = 1 + a2hw * (m - 6.5) - (1 - a2hw) * (m - 6.5) ** 2
    else:
        t2 = 0
    if rx <= r1:
        t3 = h1 + h2 * (rx / r1) + h3 * (rx / r1) ** 2
    elif rx < r2:
        t3 = 1 - (rx - r1) / (r2 - r1)
    else:
        t3 = 0
    if ztor < 10:
        t4 = 1 - ztor ** 2 / 100
    else:
        t4 = 0
    if ry0 != 999:
        if ry0 < ry1:
            t5 = 1
        elif (ry0 - ry1) < 5:
            t5 = 1 - (ry0 - ry1) / 5
        else:
            t5 = 0
    else:
        if rjb == 0:
            t5 = 1
        elif rjb < 30:
            t5 = 1 - rjb / 30
        else:
            t5 = 0
    if fhw == 1:
        f4 = a13 * t1 * t2 * t3 * t4 * t5
    else:
        f4 = 0
    if region == 2:
        f12 = a31 * math.log(vs30star / vlin)
    else:
        f12 = 0
    if region == 1:
        br = (a41 + (1180 - 850) * (a42 - a41) / (1150 - 850))
    elif region == 2:
        br = a31 * math.log(1180 / vlin)
    else:
        br = 0
    if region == 1:
        by = a29
    elif region == 3:
        by = a28
    elif region == 2:
        by = a25
    else:
        by = 0
    bs = by * rrup + br
    if 1180 >= v1:
        vs30star1180 = v1
    else:
        vs30star1180 = 1180
    bq = (a10 + b * n) * math.log(vs30star1180 / vlin)
    sa1180 = math.exp(f1 + f6 + frv * f7 + fnm * f8 + fhw * f4 + bq + bs)
    if vs30 < vlin:
        f5 = a10 * math.log(vs30star / vlin) - b * math.log(sa1180 + c) + b * math.log(sa1180 + c * (vs30star / vlin) ** n)
    else:
        f5 = (a10 + b * n) * math.log(vs30star / vlin)
    if region == 1:
        z1r = math.exp(-5.23 / 2 * math.log((vs30 ** 2 + 412 ** 2) / (1360 ** 2 + 412 ** 2))) / 1000
    else:
        z1r = math.exp(-7.67 / 4 * math.log((vs30 ** 4 + 610 ** 4) / (1360 ** 4 + 610 ** 4))) / 1000
    if vs30 <= 150:
        y1z = a43
        y2z = a43
        x1z = 50
        x2z = 150
    elif vs30 <= 250:
        y1z = a43
        y2z = a44
        x1z = 150
        x2z = 250
    elif vs30 <= 400:
        y1z = a44
        y2z = a45
        x1z = 250
        x2z = 400
    elif vs30 <= 700:
        y1z = a45
        y2z = a46
        x1z = 400
        x2z = 700
    else:
        y1z = a46
        y2z = a46
        x1z = 700
        x2z = 1000
    if vs30 == 1180:
        f10 = 0
    else:
        f10 = (y1z + (vs30 - x1z) * (y2z - y1z) / (x2z - x1z)) * math.log((z1 + 0.01) / (z1r + 0.01))
    if fas == 0:
        f11 = 0
    if region == 1:
        if vs30 < 150:
            y1 = a36
            y2 = a36
            x1 = 50
            x2 = 150
        elif vs30 < 250:
            y1 = a36
            y2 = a37
            x1 = 150
            x2 = 250
        elif vs30 < 350:
            y1 = a37
            y2 = a38
            x1 = 250
            x2 = 350
        elif vs30 < 450:
            y1 = a38
            y2 = a39
            x1 = 350
            x2 = 450
        elif vs30 < 600:
            y1 = a39
            y2 = a40
            x1 = 450
            x2 = 600
        elif vs30 < 850:
            y1 = a40
            y2 = a41
            x1 = 600
            x2 = 850
        elif vs30 < 1150:
            y1 = a41
            y2 = a42
            x1 = 850
            x2 = 1150
        else:
            y1 = a42
            y2 = a42
            x1 = 1150
            x2 = 3000
        f13 = y1 + (y2 - y1) / (x2 - x1) * (vs30 - x1)
    if region == 2:
        reg = f12 + a25 * rrup
    elif region == 3:
        reg = a28 * rrup
    elif region == 1:
        reg = f13 + a29 * rrup
    else:
        reg = 0
    if region == 1:
        rvs = f13
    elif region == 2:
        rvs = f12
    else:
        rvs = 0
    rd = rvs + by * rrup
    y = math.exp(f1 + frv * f7 + fnm * f8 + fas * f11 + f5 + fhw * f4 + f6 + f10 + rd)
    return y

def ask14_z1(vs30, region, z1):
    y = 0
    if z1 == 999:
        if region == 1:
            z1 = math.exp(-5.23 / 2 * math.log((vs30 ** 2 + 412 ** 2) / (1360 ** 2 + 412 ** 2))) / 1000
        else:
            z1 = math.exp((-7.67 / 4) * math.log((vs30 ** 4 + 610 ** 4) / (1360 ** 4 + 610 ** 4))) / 1000
    else:
        z1 = z1
    y = z1
    return y

def ask14_stdev_raw(m, rrup, rjb, rx, frv, fnm, fhw, fas, ztor, w, dip, vs30, vs30flag, z1, ry0, region, t):
    a1, a10, a11, a12, a13, a14, a15, a16 = 0, 0, 0, 0, 0, 0, 0, 0
    a17, a2, a25, a28, a29, a2hw, a3, a31 = 0, 0, 0, 0, 0, 0, 0, 0
    a36, a37, a38, a39, a4, a40, a41, a42 = 0, 0, 0, 0, 0, 0, 0, 0
    a43, a44, a45, a46, a5, a6, a7, a8 = 0, 0, 0, 0, 0, 0, 0, 0
    b, bq, br, bs, by, c, c4, c4m = 0, 0, 0, 0, 0, 0, 0, 0
    counter, crjb, f1, f4, f6, f7, f8, h1 = 0, 0, 0, 0, 0, 0, 0, 0
    h2, h3, m1, m1z, m2, m2z, maxm, maxval = 0, 0, 0, 0, 0, 0, 0, 0
    maxz, n, phi, phia, phib, pi, r, r1 = 0, 0, 0, 0, 0, 0, 0, 0
    r2, ratio, ry1, s1, s1v, s2, s2v, s3 = 0, 0, 0, 0, 0, 0, 0, 0
    s4, s5, s6, sa1180, samp, sd, sigma, t1 = 0, 0, 0, 0, 0, 0, 0, 0
    t2, t3, t4, t5, tau, taua, taub, v1 = 0, 0, 0, 0, 0, 0, 0, 0
    vlin, vs30star, vs30star1180, west, ztord = 0, 0, 0, 0, 0
    cof = _cof('ASK14', t)
    vlin = cof[0]
    b = cof[1]
    n = cof[2]
    m1 = cof[3]
    c = cof[4]
    c4 = cof[5]
    a1 = cof[6]
    a2 = cof[7]
    a3 = cof[8]
    a4 = cof[9]
    a5 = cof[10]
    a6 = cof[11]
    a7 = cof[12]
    a8 = cof[13]
    a10 = cof[14]
    a11 = cof[15]
    a12 = cof[16]
    a13 = cof[17]
    a14 = cof[18]
    a15 = cof[19]
    a16 = cof[20]
    a17 = cof[21]
    a43 = cof[22]
    a44 = cof[23]
    a45 = cof[24]
    a46 = cof[25]
    a25 = cof[26]
    a28 = cof[27]
    a29 = cof[28]
    a31 = cof[29]
    a36 = cof[30]
    a37 = cof[31]
    a38 = cof[32]
    a39 = cof[33]
    a40 = cof[34]
    a41 = cof[35]
    a42 = cof[36]
    s1 = cof[37]
    s2 = cof[38]
    s3 = cof[39]
    s4 = cof[40]
    s1v = cof[41]
    s2v = cof[42]
    s5 = cof[43]
    s6 = cof[44]
    h1 = 0.25
    h2 = 1.5
    h3 = -0.75
    m2 = 5
    n = 1.5
    a7 = 0
    a2hw = 0.2
    samp = 0.4
    crjb = 999.9
    pi = 4 * math.atan(1)
    if ztor == 999:
        if frv == 1:
            maxm = m - 5.849
            if 0 > maxm:
                maxm = 0
            maxz = 2.704 - 1.226 * maxm
            if 0 > maxz:
                maxz = 0
        else:
            maxm = m - 4.97
            if 0 > maxm:
                maxm = 0
            maxz = 2.673 - 1.136 * maxm
            if 0 > maxz:
                maxz = 0
        ztor = maxz ** 2
    if 18 / math.sin(dip * pi / 180) < 10 ** (-1.75 + 0.45 * m):
        west = 18 / math.sin(dip * pi / 180)
    else:
        west = 10 ** (-1.75 + 0.45 * m)
    if w == 999:
        w = west
    else:
        w = w
    m1z = 5
    m2z = 7.2
    maxval = 7.8
    if m <= m1z:
        ztord = maxval
    elif m <= m2z:
        ztord = maxval - (maxval / (m2 - m1)) * (m - m1)
    else:
        ztord = 0
    if ztor == 999:
        ztor = ztord
    else:
        ztor = ztor
    if m >= 5:
        c4m = c4
    elif m >= 4:
        c4m = c4 - (c4 - 1) * (5 - m)
    else:
        c4m = 1
    r = math.sqrt(rrup ** 2 + c4m ** 2)
    if m < m2:
        f1 = a1 + a4 * (m2 - m1) + a8 * (8.5 - m2) ** 2 + a6 * (m - m2) + a7 * (m - m2) ** 2 + (a2 + a3 * (m2 - m1)) * math.log(r) + a17 * rrup
    elif m < m1:
        f1 = a1 + a4 * (m - m1) + a8 * (8.5 - m) ** 2 + (a2 + a3 * (m - m1)) * math.log(r) + a17 * rrup
    else:
        f1 = a1 + a5 * (m - m1) + a8 * (8.5 - m) ** 2 + (a2 + a3 * (m - m1)) * math.log(r) + a17 * rrup
    if t >= 3:
        v1 = 800
    elif t > 0.5:
        v1 = math.exp(-0.35 * math.log(t / 0.5) + math.log(1500))
    else:
        v1 = 1500
    if vs30 < v1:
        vs30star = vs30
    else:
        vs30star = v1
    if m < 4:
        f7 = 0
    elif m <= 5:
        f7 = a11 * (m - 4)
    else:
        f7 = a11
    if m < 4:
        f8 = 0
    elif m <= 5:
        f8 = a12 * (m - 4)
    else:
        f8 = a12
    r1 = w * math.cos(dip * pi / 180)
    r2 = 3 * r1
    ry1 = rx * math.tan(20 * pi / 180)
    if dip > 30:
        t1 = (90 - dip) / 45
    else:
        t1 = 60 / 45
    if m > 6.5:
        t2 = 1 + a2hw * (m - 6.5)
    elif m > 5.5:
        t2 = 1 + a2hw * (m - 6.5) - (1 - a2hw) * (m - 6.5) ** 2
    else:
        t2 = 0
    if rx <= r1:
        t3 = h1 + h2 * (rx / r1) + h3 * (rx / r1) ** 2
    elif rx < r2:
        t3 = 1 - (rx - r1) / (r2 - r1)
    else:
        t3 = 0
    if ztor < 10:
        t4 = 1 - ztor ** 2 / 100
    else:
        t4 = 0
    if ry0 != 999:
        if ry0 < ry1:
            t5 = 1
        elif (ry0 - ry1) < 5:
            t5 = 1 - (ry0 - ry1) / 5
        else:
            t5 = 0
    else:
        if rjb == 0:
            t5 = 1
        elif rjb < 30:
            t5 = 1 - rjb / 30
        else:
            t5 = 0
    if fhw == 1:
        f4 = a13 * t1 * t2 * t3 * t4 * t5
    else:
        f4 = 0
    if region == 1:
        br = (a41 + (1180 - 850) * (a42 - a41) / (1150 - 850))
    elif region == 2:
        br = a31 * math.log(1180 / vlin)
    else:
        br = 0
    if region == 1:
        by = a29
    elif region == 3:
        by = a28
    elif region == 2:
        by = a25
    else:
        by = 0
    bs = by * rrup + br
    if 1180 >= v1:
        vs30star1180 = v1
    else:
        vs30star1180 = 1180
    bq = (a10 + b * n) * math.log(vs30star1180 / vlin)
    if ztor <= 20:
        f6 = a15 * ztor / 20
    elif ztor > 20:
        f6 = a15
    sa1180 = math.exp(f1 + f6 + frv * f7 + fnm * f8 + fhw * f4 + bq + bs)
    if region != 1:
        if vs30flag == 0:
            s1 = s1
            s2 = s2
        elif vs30flag == 1:
            s1 = s1v
            s2 = s2v
        if m < 4:
            phia = s1
        elif m <= 6:
            phia = s1 + (s2 - s1) / 2 * (m - 4)
        else:
            phia = s2
    else:
        if rrup < 30:
            phia = s5
        elif rrup <= 80:
            phia = s5 + (s6 - s5) / 50 * (rrup - 30)
        elif rrup > 80:
            phia = s6
    if m < 5:
        taua = s3
    elif m <= 7:
        taua = s3 + (s4 - s3) / 2 * (m - 5)
    else:
        taua = s4
    taub = taua
    phib = math.sqrt(phia ** 2 - samp ** 2)
    if vs30 >= vlin:
        ratio = 0
    else:
        ratio = b * sa1180 * (-1 / (sa1180 + c) + 1 / (sa1180 + c * (vs30 / vlin) ** n))
    tau = taub * (1 + ratio)
    phi = math.sqrt(phib ** 2 * (1 + ratio) ** 2 + samp ** 2)
    sigma = math.sqrt(tau ** 2 + phi ** 2)
    sd = sigma
    return sd

