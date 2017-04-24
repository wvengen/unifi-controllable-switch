
CC = gcc

CFLAGS   = -DCBC=1 -std=c99 -Os
CFLAGS  += -Wno-unused-result # @todo -Wall instead
# some size optimizations
CFLAGS  += -ffunction-sections -fdata-sections -Wl,--gc-sections
CFLAGS  += -fno-unwind-tables -fno-asynchronous-unwind-tables
CFLAGS  += -fmerge-all-constants -fno-ident -ffast-math -fno-math-errno
CFLAGS  += -fsingle-precision-constant

# to avoid having to reproduce the target's build env, link statically
LDFLAGS  = -static

TARGET   = unifi-inform-data$(TARGET_SUFFIX)
FILES    = main.c broadcast.c aes/aes.c aes/pkcs7_padding.c
HEADERS  = broadcast.h aes/aes.h aes/pkcs7_padding.h

.PHONY: all clean firmware

all: $(TARGET)


clean:
	rm -f $(TARGET) fwsplit fwmkimage $(FW_TARGET) \
		    dist.src.tar.gz dist.mips.tar.gz dist.build.tar.gz
	if [ -d build ]; then rm -f build/* && rmdir build; fi

distclean: clean
	rm -f mips/$(TARGET) mips/vmlinux-2.6.32-5-4kc-malta \
        mips/$(QEMU_ROOTWORK) mips/$(QEMU_ROOTBASE) mips/$(QEMU_KERNEL) \
				mips/$(FW_FILENAME)
	if [ -d mips ]; then rmdir mips; fi


### unifi-inform-data helper

$(TARGET): $(FILES) $(HEADERS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(FILES)
	strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id $(TARGET)


### Build utilities

fwsplit: fwsplit.c fw.h
	$(CC) -o $@ fwsplit.c -lz
fwmkimage: fwmkimage.c fw.h
	$(CC) -o $@ fwmkimage.c -lz


### Cross-compile for mips

.PHONY: mips/qemu-down mips/compile-$(TARGET)

QEMU_SSH_PORT = 23023
QEMU_SSH_OPTS = -o ConnectionAttempts=10 -o NoHostAuthenticationForLocalhost=yes -p $(QEMU_SSH_PORT)
QEMU_SSH      = sshpass -p root ssh $(QEMU_SSH_OPTS) root@localhost

QEMU_KERNEL   = vmlinux-2.6.32-5-4kc-malta
QEMU_ROOTBASE = debian_squeeze_mips_standard.qcow2
#QEMU_KERNEL   = vmlinux-3.2.0-4-4kc-malta
#QEMU_ROOTBASE = debian_wheezy_mips_standard.qcow2

QEMU_ROOTWORK = debian_mips_work.qcow2
QEMU_PACKAGES = gcc make dietlibc-dev

mips/$(QEMU_ROOTBASE):
	@mkdir -p mips
	cd mips && wget -c https://people.debian.org/~aurel32/qemu/mips/$(QEMU_ROOTBASE)

mips/$(QEMU_ROOTWORK): mips/$(QEMU_ROOTBASE)
	qemu-img create -f qcow2 -o backing_file=$(QEMU_ROOTBASE) $@

mips/$(QEMU_KERNEL):
	@mkdir -p mips
	cd mips && wget -c https://people.debian.org/~aurel32/qemu/mips/$(QEMU_KERNEL)

dist.src.tar.gz: Makefile $(FILES) $(HEADERS)
	tar -c -z -f $@ Makefile $(FILES) $(HEADERS)

mips/qemu-up: dist.src.tar.gz
	@make mips/$(QEMU_ROOTWORK) mips/$(QEMU_KERNEL)
	qemu-system-mips -M malta \
		-kernel mips/$(QEMU_KERNEL) \
		-hda mips/$(QEMU_ROOTWORK) \
		-drive format=raw,file=dist.src.tar.gz \
		-nographic -append "root=/dev/sda1 console=tty0" \
		-net nic -net user,hostfwd=tcp:127.0.0.1:$(QEMU_SSH_PORT)-:22 >/dev/null & \
		echo $$! >mips/qemu-up
	@echo -n "Waiting until sshd is up (may take a couple of minutes) ... "
	@while ! nc -z -w 30 localhost $(QEMU_SSH_PORT); do sleep 5; done
	@$(QEMU_SSH) echo done

mips/qemu-down:
	[ -f mips/qemu-up ] && kill `cat mips/qemu-up`
	@rm -f mips/qemu-up

mips/compile-$(TARGET):
	@$(QEMU_SSH) '[ -z `which gcc` ] && echo "deb http://archive.debian.org/debian squeeze main" >/etc/apt/sources.list && apt-get update && apt-get -y install $(QEMU_PACKAGES)'
	@$(QEMU_SSH) 'tar xzf /dev/sdb && make CC="diet gcc"'
	@$(QEMU_SSH) cat $(TARGET) >mips/$(TARGET)

mips/$(TARGET):
	@make mips/qemu-up mips/compile-$(TARGET) mips/qemu-down
	@chmod a+x $@


### Firmware with UniFi integration

INSTALL_FILES = \
	unifi-announce-data \
	unifi-daemon \
	unifi-inform-process \
	unifi-inform-send \
	unifi-inform-status \
	syswrapper.sh \
	shinc/common.sh \
	shinc/JSON.sh

# latest version from https://www.ubnt.com/download/accessories/toughswitch
FW_VERSION=v1.3.5
FW_BUILDID=30594.170329.1746
FW_FWVERSION=SW.ar7240.$(FW_VERSION).$(FW_BUILDID)
# unifi adaptation version (this package)
FW_UNIVERS=1

FW_FILENAME=SW.$(FW_VERSION).$(FW_BUILDID).bin
FW_TARGET=SW.$(FW_VERSION).$(FW_BUILDID)+unifi.$(FW_UNIVERS).bin
FW_UNIURL=https://github.com/wvengen/unifi-controllable-switch


firmware: $(FW_TARGET)

dist.mips.tar.gz: mips/$(TARGET) $(INSTALL_FILES)
	tar -c -z -f $@ --transform='s/^mips\///' mips/$(TARGET) $(INSTALL_FILES)

mips/$(FW_FILENAME):
	@mkdir -p mips
	cd mips && wget 'http://dl.ubnt.com/firmwares/TOUGHSwitch/$(FW_VERSION)/$(FW_FILENAME)'

$(FW_TARGET): fwsplit fwmkimage dist.mips.tar.gz mips/$(FW_FILENAME)
	# unpack firmware
	@mkdir -p firmware
	cd firmware && ../fwsplit '../mips/$(FW_FILENAME)'
	unsquashfs -d firmware/root 'firmware/$(FW_FWVERSION).rootfs'
	rm 'firmware/$(FW_FWVERSION).rootfs'
	# add tools to firmware
	mkdir -p firmware/root/usr/unifi
	tar -x -z -C firmware/root/usr/unifi -f dist.mips.tar.gz
	# integrate with system
	printf '#!/bin/sh\n/usr/unifi/syswrapper.sh $$@\n' >firmware/root/bin/syswrapper.sh
	chmod a+x firmware/root/bin/syswrapper.sh
	echo '/usr/unifi/unifi-daemon &' >>firmware/root/usr/etc/rc.d/rc.sysinit
	# add notice to web ui
	for t in templates/tab_status.tmpl templates/tab_device.tmpl; do \
		cat firmware/root/usr/www/$$t | awk ' \
				{print $$0} \
				/echo (\$$fwversion|fw_get_version)/ { print "<span>+ <a href=\"$(FW_UNIURL)\" target=\"_blank\">UniFi v$(FW_UNIVERS)</a></span>" }' \
				>firmware/template.tmp && \
			mv firmware/template.tmp firmware/root/usr/www/$$t; \
	done
	# remove inconvenient max password length restriction
	sed -i 's/ *maxlength="8"//g' firmware/root/usr/www/login.cgi firmware/root/usr/www/templates/tab_device.tmpl
	# pack firmware and cleanup
	mksquashfs firmware/root firmware/$(FW_FWVERSION).rootfs -all-root -noappend -comp lzma
	cd firmware && ../fwmkimage -v '$(FW_FWVERSION)+unifi.$(FW_UNIVERS)' -o '../$(FW_TARGET)' -i '$(FW_FWVERSION).txt'
	@rm -Rf firmware


### Distribution

DIST_BUILD_FILES = \
	Makefile \
	dist.mips.tar.gz \
  fwsplit.c fwmkimage.c fw.h

dist.build.tar.gz: $(DIST_BUILD_FILES)
	@mkdir -p build
	cp -p $(DIST_BUILD_FILES) build/
	sed -i 's/^\(dist.mips.tar.gz:\).*$$/\1/' build/Makefile  # don't try to build mips binary
	sed -i 's/^all:.*$$/all: firmware/' build/Makefile        # default target
	cat DIST_BUILD.md | sed 's/@@FW_VERSION@@/$(FW_VERSION)/g;s/@@FW_UNIVERS@@/$(FW_UNIVERS)/g' >build/README.md
	tar -c -z -f $@ build/
	rm -Rf build

