
# plain gcc for buildhost-native binary, for mips use the other
CC = gcc
#CC = mips-linux-gnu-gcc

CFLAGS   = -DCBC=1 -std=c99 -Os # -Wall
# some size optimizations
CFLAGS  += -ffunction-sections -fdata-sections -Wl,--gc-sections
CFLAGS  += -fno-unwind-tables -fno-asynchronous-unwind-tables
CFLAGS  += -fmerge-all-constants -fno-ident -ffast-math -fno-math-errno
CFLAGS  += -fsingle-precision-constant

# to avoid having to reproduce the target's build env, link statically
LDFLAGS  = -static

TARGET  = unifi-inform-data
FILES   = main.c broadcast.c aes/aes.c aes/pkcs7_padding.c
HEADERS = broadcast.h aes/aes.h aes/pkcs7_padding.h

all: strip

$(TARGET): $(FILES) $(HEADERS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $(FILES)

strip: $(TARGET)
	@strip -S --strip-unneeded -R .note.gnu.gold-version -R .comment -R .note -R .note.gnu.build-id $(TARGET)

clean:
	@rm -f $(TARGET)
