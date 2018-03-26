# Ansible Modules for Memset's DNS

These modules are currently under development and may well change significantly.

## Requirements

You'll need an API key with the following minimum scopes:

 * dns.reload
 * dns.reverse_map_list
 * dns.reverse_map_update
 * dns.zone_create
 * dns.zone_delete
 * dns.zone_domain_create
 * dns.zone_domain_delete
 * dns.zone_domain_info
 * dns.zone_domain_list
 * dns.zone_domain_update
 * dns.zone_info
 * dns.zone_list
 * dns.zone_record_create
 * dns.zone_record_delete
 * dns.zone_record_info
 * dns.zone_record_list
 * dns.zone_record_update
 * dns.zone_update
 * job.status

## Setup

To test these modules they do not need to exist in the Ansible modules directory - provided is a script to configure the relevant Ansible module directories:

    git clone https://github.com/analbeard/ansible-memset-dns.git
    cd ansible-memset-dns
    source setup.rc

You'll also need to configure the secrets file to populate the DNS manager with:

    cp secrets.yaml.example secrets.yaml