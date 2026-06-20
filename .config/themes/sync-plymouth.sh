#!/bin/bash
# Asynchronously called by generate.sh to sync Plymouth
cp /home/hugo2006alm/dotfiles/plymouth-shade-raid/* /usr/share/plymouth/themes/shade-raid/
mkinitcpio -P
