#!/bin/bash
# platform = Oracle Linux 8
# packages = grubby

grubby --update-kernel=ALL --args="mitigation=off"
