# WRF-STILT-AERMOD Model

An automated platform for identifying potential source areas and quantifying source apportionment, based on the WRF, STILT, and AERMOD models. It supports containerized deployment via Docker, scheduled tasks via Django + Celery, and provides APIs for retrieving simulation results.

- 📘 [Learn more about STILT](https://uataq.github.io/stilt/#/install)  
- 🌍 [Learn more about Air Tracker](https://globalcleanair.org/air-tracker/map/)

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourame/wrf-stilt-aermod-model.git
cd wrf-stilt-aermod-model
```
### 2. Build the Docker image
```
docker build -t wrf-stilt-aermod-model .
```
### 3. Run the container
```
 First, create a data directory on the server to store meteorological files and computation results：
 mkdir （pwd）/data
Then,
 docker run -d --name wrf-stilt-aermod-model -p 8000:8000 -p 5555:5555 \
  -v $(pwd)/data:/src/data \
  wrf-stilt-aermod-model 

```

## STILT Executable Registration

In order to run STILT with forecast meteorology, you must obtain the official HYSPLIT binary.

Apply for access here:

https://www.ready.noaa.gov/HYSPLIT_register.php(https://www.ready.noaa.gov/HYSPLIT_register.php)

After registering, download the executables, unzip them, and copy to:
```
bin/linux_x64/* exe/
```
Or place them directly into the Docker image under ${STILT_WD}/exe/.
