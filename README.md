# Ansible modules for Memset resources

These modules are a WIP location to develop them outside of the Ansible source tree. Once they are complete they are then merged to the Ansible repo.

## Completed modules:

 * [memset_dns_reload](http://docs.ansible.com/ansible/devel/modules/memset_dns_reload_module.html)
 * [memset_zone](http://docs.ansible.com/ansible/devel/modules/memset_zone_module.html)
 * [memset_zone_domain](http://docs.ansible.com/ansible/devel/modules/memset_zone_domain_module.html)
 * [memset_zone_record](http://docs.ansible.com/ansible/devel/modules/memset_zone_record_module.html)

## Roadmap

### Server management

 * memset_server_facts:
   * return facts about all servers which match provided filters.
 * memset_server_snapshot_list:
 * memset_server_snapshot:
   * take or delete snapshots.
 * memset_server_status_list:
   * return status of all servers

### Memstore
 * memset_memstore_container:
   * create/delete container.
   * set acls/cdn
 * memset_memstore_user:
   * create/delete users

### Future work

 * Loadbalancer manipulation
 * Firewalling
