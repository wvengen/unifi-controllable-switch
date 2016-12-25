/*
 * UniFi controllable switch - inform packet and broadcast helper
 *
 * @todo use data length in header when decrypting
 * @todo error handling for malloc, realloc, open, read, write
 * @todo support compression
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include "aes/aes.h"
#include "aes/pkcs7_padding.h"

#include "broadcast.h"

#define PROGNAME "unifi-inform-data"
#define MAX_BCAST_SIZE 1024


int cmd_help();
int cmd_encrypt(const uint8_t key[16], const uint8_t mac[6]);
int cmd_decrypt(const uint8_t key[16]);
int cmd_broadcast();

int parse_hex(const char *s, uint8_t *out, uint8_t len);
void fatal(const char *msg);
void get_random(void *buf, ssize_t len);
ssize_t write_dw(int fd, uint32_t i);


int main(int argc, const char *argv[]) {
  const char *cmd;
  uint8_t key[16];
  uint8_t mac[6];

  if (argc < 2) return cmd_help(argv[0]);

  cmd = argv[1];

  if (strcmp(cmd, "enc") == 0) {
    if (argc != 4) return cmd_help(argv[0]);
    parse_hex(argv[3], mac, sizeof(mac));
    parse_hex(argv[2], key, sizeof(key));
    return cmd_encrypt(key, mac);
  }

  if (strcmp(cmd, "dec") == 0) {
    if (argc != 3) return cmd_help(argv[0]);
    parse_hex(argv[2], key, sizeof(key));
    return cmd_decrypt(key);
  }

  if (strcmp(cmd, "bcast") == 0) {
    return cmd_broadcast();
  }

  return cmd_help(argv[0]);
}

int cmd_help() {
  const char msg[] =
    "UniFi inform packet encoder/decoder\n"
    "Usage: " PROGNAME " dec <key>          - decode packet data\n"
    "       " PROGNAME " enc <key> <mac>    - encode packet data\n"
    "       " PROGNAME " bcast              - send broadcast packet\n";
  write(2, msg, sizeof(msg));
  return 1;
}

void fatal(const char *msg) {
  const char prefix[] = "error: ";
  write(2, prefix, sizeof(prefix));
  write(2, msg, strlen(msg));
  write(2, "\n", 1);
  exit(2);
}

int cmd_encrypt(const uint8_t key[16], const uint8_t mac[6]) {
  uint8_t iv[16];

  const int chunksize = 64;
  uint8_t chunkin[chunksize + 16]; // extra space for padding
  ssize_t justread;

  uint8_t *dataout;
  ssize_t outsize = 4096;
  ssize_t lenout = 0;

  get_random(iv, 16);

  dataout = (uint8_t*)malloc(outsize);
  while ((justread = read(0, chunkin, chunksize)) > 0) {
    // pad last time (assuming partial read means end reached)
    if (justread < chunksize)
      justread += pkcs7_padding_pad_buffer(chunkin, justread, sizeof(chunkin), 16);
    // realloc if needed
    if (outsize < lenout + justread) {
      outsize *= 2;
      dataout = realloc(dataout, outsize);
    }
    // encrypt
    char isfirst = lenout == 0;
    AES128_CBC_encrypt_buffer(dataout + lenout, chunkin, justread, isfirst ? key : 0, isfirst ? iv : 0);
    lenout += justread;
  }

  write(1, "TNBU", 4);         // magic
  write(1, "\0\0\0\1", 4);     // version
  write(1, mac, 6);            // mac address
  write(1, "\0\1", 2);         // flags
  write(1, iv, 16);            // initialization vector
  write(1, "\0\0\0\1", 4);     // data version
  write_dw(1, lenout);         // data length
  write(1, dataout, lenout);   // encrypted data

  free(dataout);

  return 0;
}

int cmd_decrypt(const uint8_t key[16]) {
  const int chunksize = 64;
  uint8_t iv[16];
  uint8_t buffer[chunksize];
  ssize_t justread;
  uint16_t flags;

  read(0, buffer, 4);          // magic
  if (strncmp(buffer, "TNBU", 4) != 0) fatal("wrong magic");
  read(0, buffer, 4);          // version
  if (strncmp(buffer, "\0\0\0\1", 4) != 0) fatal("wrong version");
  read(0, buffer, 6);          // mac address (ignore)
  read(0, buffer, 2);          // flags
  flags = buffer[0] << 8 | buffer[1];
  read(0, iv, 16);             // initialization vector
  read(0, buffer, 4);          // data version (ignore)
  read(0, buffer, 4);          // data length (ignore) @todo use

  while ((justread = read(0, buffer, chunksize)) > 0) {
    if (flags & 1) {
      AES128_CBC_decrypt_inplace(buffer, justread, key, iv);
      if (justread < chunksize)
        justread = pkcs7_padding_data_length(buffer, justread, 16);
    }
    write(1, buffer, justread);
  }
}

int cmd_broadcast() {
  uint8_t data[MAX_BCAST_SIZE];
  ssize_t len;

  len = read(0, data, sizeof(data));
  if (len <= 0) fatal("no data");

  return broadcast(10001, data, len);
}

// output double word
ssize_t write_dw(int fd, uint32_t i) {
  uint8_t n[4] = {
    (i >> 24) & 0xff,
    (i >> 16) & 0xff,
    (i >>  8) & 0xff,
    (i      ) & 0xff
  };
  return write(1, n, 4);
}

// convert nibble to number
uint8_t nib2num(const char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 0x0a;
  if (c >= 'A' && c <= 'F') return c - 'A' + 0x0a;
  return 0;
}

// hex string to bytes
int parse_hex(const char *s, uint8_t *out, uint8_t len) {
  for (uint8_t i = 0; i < len; i ++) {
    if (s[2*i] == 0 || s[2*i+1] == 0) fatal("hex too short");
    out[i] = nib2num(s[2*i]) << 4 | nib2num(s[2*i+1]);
  }
  return 0;
}

// fill buffer with random bytes
void get_random(void *buf, ssize_t len) {
  int fd = open("/dev/urandom", O_RDONLY);
  if (fd < 0) fatal("could not open random");
  ssize_t c = 0;
  while (c < len) {
    ssize_t justread = read(fd, buf + c , len - c);
    if (justread < 0) goto done;
    c += justread;
  }
done:
  if (c < len) fatal("reading random failed");
  close(fd);
}

