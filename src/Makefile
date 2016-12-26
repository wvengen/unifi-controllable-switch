
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

.PHONY: all strip clean

all: strip

$(TARGET): $(FILES) $(HEADERS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(FILES)

strip: $(TARGET)
	strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id $(TARGET)

clean:
	rm -f $(TARGET) dist.src.tar.gz dist.mips.tar.gz

distclean: clean
	rm -f mips/$(TARGET) mips/egrep mips/vmlinux-2.6.32-5-4kc-malta \
        mips/$(QEMU_ROOTWORK) mips/$(QEMU_ROOTBASE) mips/$(QEMU_KERNEL)
	rmdir mips


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


### Install on real device

INSTALL_FILES = \
	unifi-announce-data \
	unifi-daemon \
	unifi-inform-process \
	unifi-inform-send \
	unifi-inform-status \
	syswrapper.sh \
	shinc/common.sh \
	shinc/JSON.sh

.PHONY: install

mips/egrep:
	@mkdir -p mips
	wget -O $@ -c https://busybox.net/downloads/binaries/latest/busybox-mips
	chmod a+x $@

dist.mips.tar.gz: mips/$(TARGET) $(INSTALL_FILES) mips/egrep
	tar -c -z -f $@ --transform='s/^mips\///' mips/$(TARGET) $(INSTALL_FILES) mips/egrep

install: dist.mips.tar.gz
	@if [ -z "$(HOST)" ]; then echo "Usage: make install HOST=[user@]<switch ip>" 1>&2; exit 1; fi
	cat dist.mips.tar.gz | ssh "$(HOST)" 'mkdir -p unifi && tar -x -z -C unifi -f -'
	# @todo finish installation
