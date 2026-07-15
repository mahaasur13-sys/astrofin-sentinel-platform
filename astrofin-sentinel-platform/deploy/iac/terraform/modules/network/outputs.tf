output "mikrotik_script_path"  { value = local_file.mikrotik_script.filename }
output "wg_home_conf_path"      { value = local_file.wireguard_home_conf.filename }
output "wg_edge_conf_path"      { value = local_file.wireguard_edge_conf.filename }
