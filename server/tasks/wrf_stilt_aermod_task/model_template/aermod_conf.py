aermap_inp = """CO STARTING
   TITLEONE  aermod_project
   DATATYPE  NED
   DATAFILE  {datafile}
   DOMAINXY  {aermod_domainxy}
   ANCHORXY  {aermod_anchorxy}
   RUNORNOT  RUN
CO FINISHED

SO STARTING
   {so_points}
SO FINISHED

RE STARTING
   {re_points}
RE FINISHED

OU STARTING
   RECEPTOR  aermap.rec
   SOURCLOC  aermap.src
OU FINISHED
"""

aermod_inp = """CO STARTING
   TITLEONE  aermod_project
   MODELOPT  dfault  conc
   AVERTIME  1 24 PERIOD
   POLLUTID  POLLUTANT
   RUNORNOT  run
   ERRORFIL  ERRORS.OUT
CO FINISHED

SO STARTING
   ELEVUNIT  meters
** The digit '4' was removed from the y-coordinate
**                          X        Y        Z  
**                        ------   ------   ------ 
   {location}
   {srcparam}
   {houremis}
   SRCGROUP  ALL
SO FINISHED

RE STARTING
   INCLUDED ../aermap/aermap.rec
RE FINISHED

ME STARTING
   SURFFILE  ./aermod.sfc
   PROFFILE  ./aermod.pfl
   SURFDATA  99999  2024
   UAIRDATA  99999  2024
   PROFBASE  73.2
ME FINISHED

OU STARTING
   RECTABLE 1 10
   SUMMFILE  aermod.sum
OU FINISHED
"""


mmif_inp = """INPUT {wrf_file}

start      {start} ; start time in LST for TimeZone, hour-ending format 2024100400
stop       {end}    ; end   time in LST for TimeZone, hour-ending format 2024100500

TimeZone   0   ! default is zero, i.e. GMT-00

# grid       IJ -5,-5 -5,-5   ! default
# grid IJ 0,0 210,186
grid IJ {grid_ij}

layers TOP 25 50 100 200 300 500 1000 1500 2000 3000 5000

stability  GOLDER  ! default

CALSCI_MIXHT WRF   ! default

aer_mixht     MMIF  ! default
aer_min_mixht 1.0  ! default (same as AERMET)
aer_min_obuk  1.0  ! default (same as AERMET)
aer_min_speed 0.0  ! default (following Apr 2018 MMIF Guidance)

FSL_INTERVAL 1

{points}

Output   AERMOD  SFC   aermod.sfc
Output   AERMOD  PFL   aermod.pfl
"""
