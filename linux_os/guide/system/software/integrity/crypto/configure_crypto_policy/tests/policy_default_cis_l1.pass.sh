#!/bin/bash
# platform = Oracle Linux 8,Oracle Linux 9,Red Hat Enterprise Linux 9
# profiles = xccdf_org.ssgproject.content_profile_cis_server_l1,xccdf_org.ssgproject.content_profile_cis_workstation_l1
# packages = crypto-policies-scripts

update-crypto-policies --set "DEFAULT:NO-SHA1"
