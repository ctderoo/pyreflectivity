"""
Access Lawrence Berkeley National Laboratory's X-ray reflectivity database
for thick mirror
"""

# Standard library modules.
import urllib

# Third party modules.
import requests
import bs4
import numpy as np

# Local modules.

# Globals and constants variables.

class _Mirror(object):

    URLBASE = 'http://henke.lbl.gov'
    MAX_STEP = 500

    def _process(self, script, data):
        response = self._post(script, data)
        self._check_errors(response)
        s = self._retrieve_data(response)
        return self._parse_data(s)

    def _post(self, script, data):
        url = urllib.request.urljoin(self.URLBASE, '/cgi-bin/' + script)
        return requests.post(url, data)

    def _check_errors(self, response):
        if not response.status_code == requests.codes.ok: #@UndefinedVariable
            raise RuntimeError('Could not connect to server')

        if not response.text.startswith('<Head>'):
            raise RuntimeError(response.text)

    def _retrieve_data(self, response):
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        urldata = soup.body.h2.find('a').attrs['href']

        url = urllib.request.urljoin(self.URLBASE, urldata)
        with urllib.request.urlopen(url) as fp:
            return fp.read()

    def _parse_data(self, s):
        return [list(map(float, line.split())) for line in s.splitlines()[2:]]

    def _iter_range(self, x0, x1, step):
        dx = (x1 - x0) / step
        xs = np.arange(x0, x1, dx)
        x0s = xs[::self.MAX_STEP]
        x1s = x0s + dx * min(step, self.MAX_STEP)
        x1s[-1] = x1
        steps = np.array((x1s - x0s) / dx, dtype=int)
        yield from zip(x0s, x1s, steps)

    def calculate_energy_scan(self, e0_eV, e1_eV, step, angle_deg):
        """
        Returns three columns:
        
          * Photon Energy (eV)
          * Reflectivity
          * Transmission into substrate
        """
        raise NotImplementedError

    def calculate_wavelength_scan(self, lambda0_nm, lambda1_nm, step, angle_deg):
        """
        Returns three columns:
        
          * Wavelength (nm)
          * Reflectivity
          * Transmission into substrate
        """
        raise NotImplementedError

    def calculate_angle_scan(self, theta0_deg, theta1_deg, step, energy_eV):
        """
        Returns three columns:
        
          * Angle (deg)
          * Reflectivity
          * Transmission into substrate
        """
        raise NotImplementedError

class _Layer(object):

    def __init__(self, chemical_formula='SiO2', density_g_cm3=-1):
        self.chemical_formula = chemical_formula
        self.density_g_cm3 = density_g_cm3

class ThickMirror(_Mirror):

    def __init__(self):
        self.chemical_formula = 'SiO2'
        self.density_g_cm3 = -1
        self.roughness_nm = 0
        self.polarization = 1

    def _create_post_data(self):
        data = {}
        data['Formula'] = self.chemical_formula
        data['Density'] = self.density_g_cm3
        data['Sigma'] = self.roughness_nm
        data['Pol'] = self.polarization
        data['Plot'] = 'Linear'
        data['Output'] = 'Plot'
        return data

    def calculate_energy_scan(self, e0_eV, e1_eV, step, angle_deg):
        data = self._create_post_data()
        data['Scan'] = 'Energy'
        data['Min'] = e0_eV
        data['Max'] = e1_eV
        data['Npts'] = step
        data['Fixed'] = angle_deg
        return self._process('mirror.pl', data)

    def calculate_wavelength_scan(self, lambda0_nm, lambda1_nm, step, angle_deg):
        data = self._create_post_data()
        data['Scan'] = 'Wave'
        data['Min'] = lambda0_nm
        data['Max'] = lambda1_nm
        data['Npts'] = step
        data['Fixed'] = angle_deg
        return self._process('mirror.pl', data)

    def calculate_angle_scan(self, theta0_deg, theta1_deg, step, energy_eV):
        data = self._create_post_data()
        data['Scan'] = 'Angle'
        data['Min'] = theta0_deg
        data['Max'] = theta1_deg
        data['Npts'] = step
        data['Fixed'] = energy_eV
        return self._process('mirror.pl', data)

class MultiLayerMirror(_Mirror):

    def __init__(self):
        self._top_layer = _Layer('Si')
        self._bottom_layer = _Layer('Mo')
        self.period_nm = 6.9
        self.ratio = 0.4 # bottom layer thickness / period
        self.interdiffusion_thickenss_nm = 0
        self.nperiod = 40
        self._substrate = _Layer('SiO2')
        self.polarization = 1

    def _create_post_data(self):
        data = {}
        data['Layer2'] = self.top_layer.chemical_formula
        data['Density2'] = self.top_layer.density_g_cm3
        data['Layer1'] = self.bottom_layer.chemical_formula
        data['Density1'] = self.bottom_layer.density_g_cm3
        data['Thick'] = self.period_nm
        data['Gamma'] = self.ratio
        data['Sigma'] = self.interdiffusion_thickenss_nm
        data['Ncells'] = self.nperiod
        data['Substrate'] = self.substrate.chemical_formula
        data['Sdensity'] = self.substrate.density_g_cm3
        data['Pol'] = self.polarization
        data['Plot'] = 'Linear'
        data['Output'] = 'Plot'
        return data

    def calculate_energy_scan(self, e0_eV, e1_eV, step, angle_deg):
        if e0_eV < 30:
            raise ValueError('Minimum energy is 30 eV')
        if e1_eV > 30000:
            raise ValueError('Maximum energy is 30000 eV')

        values = []
        for e0, e1, step in self._iter_range(e0_eV, e1_eV, step):
            data = self._create_post_data()
            data['Scan'] = 'Energy'
            data['Min'] = e0
            data['Max'] = e1
            data['Npts'] = step
            data['Fixed'] = angle_deg
            values.extend(self._process('multi.pl', data)[:-1])

        return np.array(values)

    def calculate_wavelength_scan(self, lambda0_nm, lambda1_nm, step, angle_deg):
        if lambda0_nm < 0.041:
            raise ValueError('Minimum wavelength is 0.041 nm')
        if lambda1_nm > 41.0:
            raise ValueError('Maximum wavelength is 41 nm')

        values = []
        for lambda0, lambda1, step in \
                self._iter_range(lambda0_nm, lambda1_nm, step):
            data = self._create_post_data()
            data['Scan'] = 'Wave'
            data['Min'] = lambda0
            data['Max'] = lambda1
            data['Npts'] = step
            data['Fixed'] = angle_deg
            values.extend(self._process('multi.pl', data)[:-1])

        return np.array(values)

    def calculate_angle_scan(self, theta0_deg, theta1_deg, step, energy_eV):
        if theta0_deg < 0:
            raise ValueError('Minimum angle is 0 deg')
        if theta1_deg > 90:
            raise ValueError('Maximum angle is 90 deg')

        values = []
        for theta0, theta1, step in \
                self._iter_range(theta0_deg, theta1_deg, step):
            data = self._create_post_data()
            data['Scan'] = 'Angle'
            data['Min'] = theta0
            data['Max'] = theta1
            data['Npts'] = step
            data['Fixed'] = energy_eV
            values.extend(self._process('multi.pl', data)[:-1])

        return np.array(values)

    @property
    def top_layer(self):
        return self._top_layer

    @property
    def bottom_layer(self):
        return self._bottom_layer

    @property
    def substrate(self):
        return self._substrate

class EnergyAngleScan(object):

    def __init__(self, mirror):
        self._mirror = mirror
        self._progress = 0.0

    def scan(self, e0_eV, e1_eV, e_step, theta0_deg, theta1_deg, theta_step):
        values = np.zeros((e_step, theta_step))
        thetas = np.linspace(theta0_deg, theta1_deg, theta_step)

        self._progress = 0

        for i, theta_deg in enumerate(thetas):
            self._progress = i / len(thetas)
            dvalues = self.mirror.calculate_energy_scan(e0_eV, e1_eV, e_step, theta_deg)
            values[:, i] = dvalues[:, 1]

        self._progress = 1

        return values

    @property
    def progress(self):
        return self._progress

if __name__ == '__main__':
    # LiF
#    m = ThickMirror()
#    m.chemical_formula = 'LiF'
#    m.polarization = 0
#
#    for energy_eV in np.arange(4000, 13000, 1000):
#        data = m.calculate_angle_scan(11, 55, 500, energy_eV)
#
#        filename = '/tmp/lif_%ieV.csv' % energy_eV
#        np.savetxt(filename, data, delimiter=',')

    # TAP
    m = ThickMirror()
    m.chemical_formula = 'TlHCBH4O4'
    m.polarization = 0

    for energy_eV in np.arange(600, 1900, 50):
        data = m.calculate_angle_scan(11, 55, 500, energy_eV)

        filename = '/tmp/tap_%ieV.csv' % energy_eV
        np.savetxt(filename, data, delimiter=',')

    # LDE2
#    m = MultiLayerMirror()
#    m.top_layer.chemical_formula = 'Ni'
#    m.bottom_layer.chemical_formula = 'C'
#    m.period_nm = 4.96
#    m.polarization = 0
#    m.interdiffusion_thickenss_nm = 0
#    m.nperiod = -1
#
#    for energy_eV in np.arange(150, 500, 25):
#        data = m.calculate_angle_scan(11, 55, 500, energy_eV)
#
#        filename = '/tmp/lde2_%ieV.csv' % energy_eV
#        np.savetxt(filename, data, delimiter=',')

