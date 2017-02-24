
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
	rm -f $(TARGET) fwsplit fwmkimage $(FW_TARGET) dist-build.sh \
		    dist.src.tar.gz dist.mips.tar.gz dist.build-cross.tar.gz dist.build-mips.tar.gz
	if [ -d build ]; then rm -f build/* && rmdir build; fi

distclean: clean
	rm -f mips/$(TARGET) mips/fwsplit mips/fwmkimage mips/mksquashfs mips/unsquashfs \
	      mips/vmlinux-2.6.32-5-4kc-malta \
        mips/$(QEMU_ROOTWORK) mips/$(QEMU_ROOTBASE) mips/$(QEMU_KERNEL) \
				mips/$(FW_FILENAME) mips/squashfs.tar.gz mips/lzma.tar.bz2
	if [ -d mips ]; then rmdir mips; fi


### unifi-inform-data helper

$(TARGET): $(FILES) $(HEADERS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(FILES)
	strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id $(TARGET)


### Build utilities

fwsplit: fwsplit.c fw.h
	$(CC) -o $@ fwsplit.c -lz
	strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id $@
fwmkimage: fwmkimage.c fw.h
	$(CC) -o $@ fwmkimage.c -lz
	strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id $@


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

mips/qemu-up:
	@make mips/$(QEMU_ROOTWORK) mips/$(QEMU_KERNEL)
	qemu-system-mips -M malta \
		-kernel mips/$(QEMU_KERNEL) \
		-hda mips/$(QEMU_ROOTWORK) \
		-nographic -append "root=/dev/sda1 console=tty0" \
		-net nic -net user,hostfwd=tcp:127.0.0.1:$(QEMU_SSH_PORT)-:22 >/dev/null & \
		echo $$! >mips/qemu-up
	@echo -n "Waiting until sshd is up (may take a couple of minutes) ... "
	@while ! nc -z -w 30 localhost $(QEMU_SSH_PORT); do sleep 5; done
	@$(QEMU_SSH) echo done

mips/qemu-down:
	[ -f mips/qemu-up ] && kill `cat mips/qemu-up`
	@rm -f mips/qemu-up

mips/compile-$(TARGET): dist.src.tar.gz
	@$(QEMU_SSH) '[ -z `which gcc` ] && echo "deb http://archive.debian.org/debian squeeze main" >/etc/apt/sources.list && apt-get update && apt-get -y install $(QEMU_PACKAGES)' || true
	@zcat dist.src.tar.gz | $(QEMU_SSH) 'rm -Rf src && mkdir -p src && tar -C src -x -f -'
	@$(QEMU_SSH) 'cd src && make CC="diet gcc" $(TARGET)'
	@$(QEMU_SSH) tar -C src -c -f - $(TARGET) | tar -C mips -x -f -

mips/$(TARGET):
	@make mips/qemu-up mips/compile-$(TARGET) mips/qemu-down


### mksquashfs + unsquashfs for MIPS (to repack firmware on the TOUGHswitch itself)

MKSQUASH_URL = https://heanet.dl.sourceforge.net/project/squashfs/squashfs/squashfs4.3/squashfs4.3.tar.gz
LIBLZMA_URL = https://heanet.dl.sourceforge.net/project/sevenzip/LZMA%20SDK/4.65/lzma465.tar.bz2

mips/squashfs.tar.gz:
	@mkdir -p mips
	wget -O $@ $(MKSQUASH_URL)

mips/lzma.tar.bz2:
	@mkdir -p mips
	wget -O $@ $(LIBLZMA_URL)

mips/compile-mksquashfs: mips/squashfs.tar.gz mips/lzma.tar.bz2
	@bzcat mips/lzma.tar.bz2 | $(QEMU_SSH) 'rm -Rf lzma && mkdir -p lzma && tar -C lzma -x -f - C/'
	@zcat mips/squashfs.tar.gz | $(QEMU_SSH) 'rm -Rf squashfs && mkdir -p squashfs && tar -C squashfs --strip-components=2 --wildcards "squashfs*/squashfs-tools" -x -f -'
	@$(QEMU_SSH) 'sed -i "s/max_digits = .*/max_digits = 5;/" squashfs/progressbar.c squashfs/unsquashfs.c' # avoid undefined references to `log10' and `floor' (dietlibc bug?)
	@$(QEMU_SSH) 'sed -i "s/\(TRACE(\"create_inode: dev\)/long long unsigned int qq = i->data;\1/;s/i->data \& 0xff/qq \& 0xff/g" squashfs/unsquashfs.c' # avoid weird invalid type argument error (dietlibc + compiler bug?)
	@$(QEMU_SSH) 'cd squashfs && CFLAGS="-DFNM_EXTMATCH=0 -include pthread.h -include pty.h" make GZIP_SUPPORT=0 LZMA_SUPPORT=1 LZMA_DIR=../lzma COMP_DEFAULT=lzma XATTR_SUPPORT=0 CC="diet gcc"'
	@$(QEMU_SSH) 'cd squashfs && strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id mksquashfs unsquashfs'
	@$(QEMU_SSH) tar -C squashfs -c -f - mksquashfs unsquashfs | tar -C mips -x -f -

mips/compile-fwsplit:
	@tar -c -f - fwsplit.c fwmkimage.c fw.h Makefile | $(QEMU_SSH) 'rm -Rf fwsplit && mkdir -p fwsplit && tar -C fwsplit -x -f -'
	@$(QEMU_SSH) 'cd fwsplit && make CC="diet gcc -D_GNU_SOURCE" fwsplit fwmkimage'
	@$(QEMU_SSH) tar -C fwsplit -c -f - fwsplit fwmkimage | tar -C mips -x -f -

mips/mksquashfs:
	@make mips/qemu-up mips/compile-mksquashfs mips/compile-fwsplit mips/qemu-down


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
FW_VERSION=v1.3.3
FW_BUILDID=29156.160523.1659
FW_FWVERSION=SW.ar7240.$(FW_VERSION).$(FW_BUILDID)
# unifi adaptation version (this package)
FW_UNIVERS=1
FW_URL=http://dl.ubnt.com/firmwares/TOUGHSwitch/$(FW_VERSION)/$(FW_FILENAME)

FW_FILENAME=SW.$(FW_VERSION).$(FW_BUILDID).bin
FW_TARGET=SW.$(FW_VERSION).$(FW_BUILDID)+unifi.$(FW_UNIVERS).bin
FW_UNIURL=https://github.com/wvengen/unifi-controllable-switch


firmware: $(FW_TARGET)

dist.mips.tar.gz: mips/$(TARGET) $(INSTALL_FILES)
	tar -c -z -f $@ --transform='s/^mips\///' mips/$(TARGET) $(INSTALL_FILES)

mips/$(FW_FILENAME):
	@mkdir -p mips
	cd mips && wget '$(FW_URL)'

dist-build.sh: dist-build.sh.in
	sed 's|@@FW_FILENAME@@|$(FW_FILENAME)|;s|@@FW_URL@@|$(FW_URL)|;s|@@FW_FWVERSION@@|$(FW_FWVERSION)|;s|@@FW_UNIVERS@@|$(FW_UNIVERS)|;s|@@FW_UNIURL@@|$(FW_UNIURL)|;s|@@FW_TARGET@@|$(FW_TARGET)|;' <dist-build.sh.in >dist-build.sh
	chmod a+x dist-build.sh

$(FW_TARGET): dist-build.sh fwsplit fwmkimage dist.mips.tar.gz mips/$(FW_FILENAME)
	FW_PATH=mips/$(FW_FILENAME) ./dist-build.sh


### Cross build distribution

DIST_BUILD_FILES = \
	Makefile dist-build.sh.in \
	dist.mips.tar.gz \
  fwsplit.c fwmkimage.c fw.h

dist.build-cross.tar.gz: $(DIST_BUILD_FILES)
	@mkdir -p build
	cp -p $(DIST_BUILD_FILES) build/
	sed -i 's/^\(dist.mips.tar.gz:\).*$$/\1/' build/Makefile  # don't try to build mips binary
	sed -i 's/^all:.*$$/all: firmware/' build/Makefile        # default target
	cat DIST_BUILD_CROSS.md | sed 's/@@FW_VERSION@@/$(FW_VERSION)/g;s/@@FW_UNIVERS@@/$(FW_UNIVERS)/g' >build/README.md
	tar -c -z -f $@ build/
	rm -Rf build


### MIPS build distribution

MIPS_BUILD_FILES = \
	dist.mips.tar.gz dist-build.sh \
  mips/mksquashfs mips/unsquashfs \
	mips/fwsplit mips/fwmkimage
 
dist.build-mips.tar.gz: $(MIPS_BUILD_FILES)
	@mkdir -p build
	cp -p $(MIPS_BUILD_FILES) build/
	cat DIST_BUILD_MIPS.md | sed 's/@@FW_VERSION@@/$(FW_VERSION)/g;s/@@FW_UNIVERS@@/$(FW_UNIVERS)/g' >build/README.md
	tar -c -z -f $@ build/
	rm -Rf build

