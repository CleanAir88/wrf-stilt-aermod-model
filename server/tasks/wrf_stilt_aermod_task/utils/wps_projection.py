import pyproj


class WPSDomainLCC(object):
    """
    A top-level Lambert Conic Conformal projection domain.
    """

    def __init__(self, dom_id, cfg, parent=None):
        """
        Initialize a top-level LCC domain.

        :param dom_id: the domain id
        :param cfg: the configuration dictionary
        :param parent: the parent domain (if this is a child)
        """
        self.dom_id = dom_id
        self.parent = parent
        self.parent_id = parent.dom_id if parent is not None else self.dom_id
        self.top_level = parent is None
        self._init_from_dict(cfg)

    def _init_from_dict(self, cfg):
        """
        Initialize the domain from a dictionary containing the parameters.

        :param cfg: the parameter dictionary
        """
        self.parent_start = tuple(cfg["parent_start"])
        self.domain_size = tuple(cfg["domain_size"])
        self.parent_cell_size_ratio = cfg["parent_cell_size_ratio"]
        if self.top_level:
            # this is a top level domain
            self.cell_size = tuple(cfg["cell_size"])
            self.ref_latlon = tuple(cfg["center_latlon"])

            if "truelats" in cfg:
                self.truelats = cfg["truelats"]
            else:
                self.truelats = [self.ref_lat] * 2
            if "stand_lon" in cfg:
                self.stand_lon = cfg["stand_lon"]
            else:
                self.stand_lon = self.ref_lon
            self._init_projection()
        else:
            self.cell_size = [float(x) / self.parent_cell_size_ratio for x in self.parent.cell_size]

    def _init_projection(self):
        """
        This function is based on code by Pavel Krc <krc@cs.cas.cz>, minor changes applied.
        It initializes the projection for a top-level domain.
        """
        radius = 6370e3

        # Spherical latlon used by WRF
        self.latlon_sphere = pyproj.Proj(
            units="m", proj="latlon", a=radius, b=radius, towgs84="0,0,0", no_defs=True
        )

        # Lambert Conformal Conic used by WRF
        self.lambert_grid = pyproj.Proj(
            units="m",
            proj="lcc",
            lat_1=self.truelats[0],
            lat_2=self.truelats[1],
            lat_0=self.ref_latlon[0],
            lon_0=self.stand_lon,
            a=radius,
            b=radius,
            towgs84="0,0,0",
            no_defs=True,
        )

        grid_size_j = (self.domain_size[0] - 1) * self.cell_size[0]
        grid_size_i = (self.domain_size[1] - 1) * self.cell_size[1]

        grid_center_j, grid_center_i = pyproj.transform(
            self.latlon_sphere, self.lambert_grid, self.ref_latlon[1], self.ref_latlon[0]
        )

        self.offset_i = grid_center_i - grid_size_i * 0.5
        self.offset_j = grid_center_j - grid_size_j * 0.5

    def latlon_to_ij(self, lat, lon):
        """
        Convert latitude and longitude into grid coordinates.

        If this is a child domain, it asks it's parent to do the projectiona and then
        remaps it into its own coordinate system via parent_start and cell size ratio.

        :param lat: latitude
        :param lon: longitude
        :return: the i, j position in grid coordinates
        """
        if self.top_level:
            proj_j, proj_i = pyproj.transform(self.latlon_sphere, self.lambert_grid, lon, lat)
            return (
                (proj_i - self.offset_i) / self.cell_size[0],
                (proj_j - self.offset_j) / self.cell_size[1],
            )
        else:
            pi, pj = self.parent.latlon_to_ij(lat, lon)
            pcsr, ps = self.parent_cell_size_ratio, self.parent_start
            delta = (pcsr - 1) / 2
            return ((pi - ps[0] + 1.0) * pcsr + delta, (pj - ps[1] + 1.0) * pcsr + delta)

    def ij_to_latlon(self, i, j):
        if self.top_level:
            i_value = i * self.cell_size[1] + self.offset_i
            j_value = j * self.cell_size[0] + self.offset_j
            lon, lat = pyproj.transform(
                self.lambert_grid,
                self.latlon_sphere,
                i_value,
                j_value,
            )
            return round(lat, 3), round(lon, 3)
        else:
            parent_i = (i) / self.parent_cell_size_ratio + self.parent_start[1] - 1
            parent_j = (j) / self.parent_cell_size_ratio + self.parent_start[0] - 1
            # return self.parent.ij_to_latlon(i + self.parent_start[0]-1, j + self.parent_start[1]-1)
            return self.parent.ij_to_latlon(parent_i, parent_j)


if __name__ == "__main__":
    top_cfg = {
        "cell_size": [27000, 27000],  # dx, dy
        "center_latlon": [34.0, 110.0],  # ref_lat, ref_lon
        "truelats": [25.0, 40.0],
        "stand_lon": 110.0,
        "parent_cell_size_ratio": 1,
        "domain_size": [195, 245],  # j, i
        "parent_start": [1, 1],  # j, i
    }

    d02_cfg = {
        "parent_cell_size_ratio": 3,
        "domain_size": [
            34,
            28,
        ],
        "parent_start": [116, 141],
    }

    d03_cfg = {
        "parent_cell_size_ratio": 3,
        "domain_size": [52, 40],
        "parent_start": [9, 7],
    }

    d04_cfg = {
        "parent_cell_size_ratio": 3,
        "domain_size": [76, 58],
        "parent_start": [13, 10],
    }

    # 创建顶层域
    d01 = WPSDomainLCC("d01", top_cfg)

    # 创建子域
    d02 = WPSDomainLCC("d02", d02_cfg, parent=d01)
    d03 = WPSDomainLCC("d03", d03_cfg, parent=d02)
    d04 = WPSDomainLCC("d04", d04_cfg, parent=d03)

    print("d01: ", d01.ij_to_latlon((245 - 1) / 2, (195 - 1) / 2))
    print("d01: ", d01.ij_to_latlon(0, 0))
    print("d02: ", d02.ij_to_latlon(0, 0))
    print("d03: ", d03.ij_to_latlon(0, 0))
    print("d04: ", d04.ij_to_latlon(0, 0))
