 &time_control
 run_days                            = {{run_days}},
 run_hours                           = {{run_hours}},
 run_minutes                         = {{run_minutes}},
 run_seconds                         = {{run_seconds}},
 start_year                          = {{start_year}},
 start_month                         = {{start_month}},
 start_day                           = {{start_day}},
 start_hour                          = {{start_hour}},
 start_minute                        = {{start_minute}},
 start_second                        = {{start_second}},
 end_year                            = {{end_year}},
 end_month                           = {{end_month}},
 end_day                             = {{end_day}},
 end_hour                            = {{end_hour}},
 end_minute                          = {{end_minute}},
 end_second                          = {{end_second}},
 interval_seconds                    = {{interval_seconds}},
 input_from_file                     = {{input_from_file}},
 history_interval                    = {{history_interval}},
 frames_per_outfile                  = {{frames_per_outfile}},
 restart                             = .false.,
 restart_interval                    = 720,
 io_form_history                     = 2,
 io_form_restart                     = 2,
 io_form_input                       = 2,
 io_form_boundary                    = 2,
 debug_level                         = 0,
 /

 &domains
 time_step                           = 120,
 time_step_fract_num                 = 0,
 time_step_fract_den                 = 1,
 max_dom                             = {{max_dom}},
 i_parent_start    =   {{i_parent_start}},
 j_parent_start    =   {{j_parent_start}},
 e_we              = {{e_we}},
 e_sn              = {{e_sn}},
 e_vert                              = {{e_vert}},    !!! vertical point, 1 larger than layers
 p_top_requested                     = 10000,
 num_metgrid_levels                  = 34,
 num_metgrid_soil_levels             = 4,
 dx                                  = {{dx}},
 dy                                  = {{dy}},
 grid_id                             = {{grid_id}},
 parent_id                           = {{parent_id}},
 parent_grid_ratio                   = {{parent_grid_ratio}},
 parent_time_step_ratio              = {{parent_time_step_ratio}},
 feedback                            = 0,
 smooth_option                       = 2,
 /

 &physics
 mp_physics                          = {{mp_physics}},   
 ra_lw_physics                       = {{ra_lw_physics}},    
 ra_sw_physics                       = {{ra_sw_physics}},   
 radt                                = {{radt}},   
 sf_sfclay_physics                   = {{sf_sfclay_physics}}, 
 sf_surface_physics                  = {{sf_surface_physics}},   
 bl_pbl_physics                      = {{bl_pbl_physics}},  
 bldt                                = {{bldt}},   
 cu_physics                          = {{cu_physics}},   
 cudt                                = 0,    
 isfflx                              = 1,
 ifsnow                              = 0,
 icloud                              = 1,
 surface_input_source                = 1,
 NUM_LAND_CAT                        = 21,
 num_soil_layers                     = 4,
 mp_zero_out                         = 0,
 sf_urban_physics                    = 0,
 maxiens                             = 1,
 maxens                              = 3,
 maxens2                             = 3,
 maxens3                             = 16,
 ensdim                              = 144,
 slope_rad                           = 0,
 topo_shading                        = 0,
 sst_update			     = 0,
 /

 &dynamics
 w_damping                           = 0,
 diff_opt                            = 1,
 km_opt                              = 4,
 diff_6th_opt                        = 0,
 diff_6th_factor                     = 0.12,
 base_temp                           = 290.
 damp_opt                            = 0,
 zdamp                               = 5000.,  
 dampcoef                            = 0.2,     
 khdif                               = 0,      
 kvdif                               = 0,      
 non_hydrostatic                     = .true., 
 moist_adv_opt                       = 1, 
 scalar_adv_opt                      = 1,  
 /
 &bdy_control
 spec_bdy_width                      = 5,
 spec_zone                           = 1,
 relax_zone                          = 4,
 specified                           = {{specified}}, 
 nested                              = {{nested}},
 /

 &grib2
 /

 &namelist_quilt
 nio_tasks_per_group = 0,
 nio_groups = 1,
 /

