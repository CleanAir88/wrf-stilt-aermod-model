&share
 wrf_core = 'ARW',
 max_dom = {{max_dom}},
 start_date = {{start_date}},
 end_date = {{end_date}},
 interval_seconds = {{interval_seconds}},
 io_form_geogrid = 2,
 active_grid = {{active_grid}},
 subgrid_ratio_x = 1,
 subgrid_ratio_y = 1,
 opt_output_from_geogrid_path = './',
 debug_level = 0,
 nocolons = .FALSE.
/

&geogrid
 parent_id         =    {{parent_id}},
 parent_grid_ratio =    {{parent_grid_ratio}},
 i_parent_start    =    {{i_parent_start}},
 j_parent_start    =    {{j_parent_start}},
 s_we              =    {{s_we}},
 e_we              =  {{e_we}},
 s_sn              =    {{s_sn}},
 e_sn              =  {{e_sn}},
 geog_data_res = 'default', 'default', 'default', 'default',
 dx = {{dx}},
 dy = {{dy}},
 map_proj = 'lambert',
 ref_lat   =  {{ref_lat}},
 ref_lon   =  {{ref_lon}},
 truelat1  =  25.0,
 truelat2  =  40.0,
 stand_lon =  110.0,
 geog_data_path = '../WPS_GEOG/'
/

&ungrib
 out_format = 'WPS',
 prefix = '{{prefix}}'
/

&metgrid
 fg_name = '{{fg_name}}',
 io_form_metgrid = 2,
 opt_output_from_metgrid_path = '{{opt_output_from_metgrid_path}}',
/

&mod_levs
 press_pa = 201300 , 200100 , 100000 ,
             95000 ,  90000 ,
             85000 ,  80000 ,
             75000 ,  70000 ,
             65000 ,  60000 ,
             55000 ,  50000 ,
             45000 ,  40000 ,

             25000 ,  20000 ,
             15000 ,  10000 ,
              5000 ,   1000
/